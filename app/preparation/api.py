"""Session-owned draft persistence. No inference, confirmation or execution."""
from contextlib import contextmanager
from typing import Literal
from threading import BoundedSemaphore
from fastapi import Depends,HTTPException,Request,Response
from pydantic import BaseModel,ConfigDict,Field,StrictInt
from ..evaluation_intent import EvaluationIntent
from .draft import save
from .review import source_changes
from .catalog import sources
from .choice_errors import choice_error,upload_error
from .proposal_store import ProposalStore
from .errors import BeforeDispatchBlocked,BLOCKED_MESSAGE,ProposalRejected
from .store import DraftStore,MissingDraft,StaleDraft,DraftLimit

REQUEST_LIMIT=32_100_000  # 32 MB draft plus bounded envelope / JSON whitespace.


class SaveDraft(BaseModel):
    model_config=ConfigDict(extra='forbid')
    title:str=Field(min_length=1,max_length=120)
    record:dict
    store_inputs:Literal[True]


class CreateDraft(SaveDraft):
    request_id:str|None=Field(default=None,pattern=r'^[a-f0-9]{32}$')


class ReplaceDraft(SaveDraft):
    revision:StrictInt=Field(ge=1)


class DeleteDraft(BaseModel):
    model_config=ConfigDict(extra='forbid')
    revision:StrictInt=Field(ge=1)


class PreviewDraft(DeleteDraft):
    policies:dict


class HandoffDraft(DeleteDraft):
    review_hash:str=Field(pattern=r'^[a-f0-9]{64}$')
    confirm:Literal[True]


class ProposalInputs(BaseModel):
    model_config=ConfigDict(extra='forbid')
    files:dict[str,str]
    claim:str=Field(min_length=10,max_length=3000)
    documentation:list[str]
    evaluation_intent:EvaluationIntent|None=None
    projection:list[dict]|None=None
    store_inputs:Literal[True]


class SubmitProposal(BaseModel):
    model_config=ConfigDict(extra='forbid')
    payload_hash:str=Field(pattern=r'^[a-f0-9]{64}$')
    confirm_upload:Literal[True]


class ReviewProposal(BaseModel):
    model_config=ConfigDict(extra='forbid')
    files:dict[str,str]
    spec_text:str=Field(max_length=100000)
    policies:dict
    model_proposal:dict|None=None


@contextmanager
def input_errors(message='The preparation draft is invalid. Reopen the original inputs and preview your choices again.', *, explain_choices=False, explain_upload=False):
    try:yield
    except MissingDraft as exc:raise HTTPException(404,str(exc)) from exc
    except (StaleDraft,DraftLimit) as exc:raise HTTPException(409,str(exc)) from exc
    except (ValueError,TypeError,KeyError,IndexError,AttributeError,RecursionError) as exc:
        # Never reflect an uploaded row, path, or parser detail into an error.
        guidance=choice_error(exc) if explain_choices else None
        if explain_upload:
            guidance=upload_error(exc)
            if guidance:raise HTTPException(422,guidance+' No model request was made.') from exc
        raise HTTPException(422,(guidance+' No draft was saved or confirmed.') if guidance else message) from exc


def register(app,connect,owner):
    store=DraftStore(connect)
    proposals=ProposalStore(connect)
    processing_slot=BoundedSemaphore(1)

    async def preparation_slot():
        # Fail quickly instead of queuing multiple full-table recomputations.
        # Request scope holds the slot through response serialization/sending.
        if not processing_slot.acquire(blocking=False):
            raise HTTPException(429,'A dataset preparation is already being processed. Your request was not started. Keep your choices and try again shortly.',headers={'Retry-After':'2','X-Asterisk-Rejection':'preparation-capacity'})
        try:
            yield
        finally:
            processing_slot.release()

    heavy=[Depends(preparation_slot)]
    # Matches the app's existing startup mechanism; also handles a configured
    # database changed between application import and server startup.
    app.router.add_event_handler('startup',lambda: DraftStore(connect))
    app.router.add_event_handler('startup',lambda: ProposalStore(connect))
    from .runtime import configure
    app.router.add_event_handler('startup',lambda: configure(app))

    def write_owner(request):
        uid=owner(request)
        if request.headers.get('content-type','').split(';',1)[0].strip().lower()!='application/json':
            raise HTTPException(415,'Send the preparation as JSON.')
        return uid

    @app.get('/api/preparations/capabilities')
    def preparation_capabilities(request:Request):
        uid=owner(request)
        # Configuration only: never contact the provider or reserve budget here.
        return {'proposal_configured':getattr(app.state,'preparation_complete',None) is not None,'draft_capacity':store.capacity(uid)}

    @app.post('/api/preparations/review-proposal',dependencies=heavy)
    def review_proposal(request:Request,body:ReviewProposal):
        write_owner(request)
        with input_errors('These choices could not prepare every source record. Check the identity, repeat, mapping and evidence fields.',explain_choices=True):
            from .intake import open_inputs
            from .model_record import verify_model_record
            session=open_inputs(body.spec_text,body.files)
            if body.model_proposal is not None:
                verify_model_record(body.model_proposal,session.spec,session.files)
                session.model_proposal=body.model_proposal
            review=session.preview(body.policies)
            return {'record':save(session,review['review_hash']),
                    'population':review['reviewed_population'],
                    'previous_population':review['proposed_population'],
                    'source_changes':review.get('source_changes',{'available':False,'reason':'No source comparison was recorded.'}),
                    'lineage':review['extraction']['lineage'],
                    'spec':review['extraction']['spec'],'confirmation':None}

    @app.post('/api/preparations/proposal-preview',status_code=201,dependencies=heavy)
    def preview_proposal(request:Request,body:ProposalInputs):
        uid=write_owner(request)
        with input_errors('Could not prepare this upload preview. Check the source files, claim and documentation selection.',explain_upload=True):
            store.require_capacity(uid)
            return {**proposals.create(uid,body.files,body.claim,body.documentation,body.projection,body.evaluation_intent.model_dump() if body.evaluation_intent else None),
                    'provider_available':getattr(app.state,'preparation_complete',None) is not None,
                    'storage_notice':'Sources are retained on this app server for this preview, expire after one hour, and are removed when expired previews are cleaned up or you discard the preview.'}

    @app.delete('/api/preparations/proposals/{id}',status_code=204)
    def discard_proposal(id:str,request:Request):
        proposals.discard(owner(request),id)
        return Response(status_code=204)

    @app.get('/api/preparations/proposals/{id}')
    def recover_proposal(id:str,request:Request):
        with input_errors():return proposals.recover(owner(request),id)

    @app.post('/api/preparations/proposals/{id}/submit',dependencies=heavy)
    def submit_proposal(id:str,request:Request,body:SubmitProposal):
        uid=write_owner(request)
        complete=getattr(app.state,'preparation_complete',None)
        if complete is None:raise HTTPException(503,'A budgeted preparation provider is not configured. No upload was made.')
        with input_errors():
            store.require_capacity(uid)
            ticket=proposals.claim(uid,id,body.payload_hash,body.confirm_upload)
        try:
            result=ticket.submit(body.payload_hash,body.confirm_upload,complete)
            if result['session'] is None:
                response={'status':'insufficient','missing':result['missing']}
            else:
                session=result['session']
                response={'status':'review_required','spec':session.spec,'files':session.files,
                          'sources':sources(session.spec,session.files),'model_proposal':session.model_proposal,
                          'proposal_issue':session.proposal_issue,
                          'confirmation':None}
        except ProposalRejected as exc:
            response={'status':'rejected','message':str(exc),'confirmation':None}
            proposals.finish(uid,id,response)
            return response
        except BeforeDispatchBlocked:
            proposals.finish(uid,id,{'status':'blocked','provider_contacted':False})
            raise HTTPException(409,BLOCKED_MESSAGE) from None
        except Exception as exc:
            # Store only a fixed public error, never provider exception details.
            proposals.finish(uid,id,{'status':'failed'})
            raise HTTPException(502,'The proposal attempt failed. No automatic retry was made; a remote charge may still have occurred. Create and review a new preview before retrying.') from exc
        proposals.finish(uid,id,response)
        return response

    @app.get('/api/preparations')
    def list_drafts(request:Request):
        return {'drafts':store.list(owner(request))}

    @app.post('/api/preparations',status_code=201,dependencies=heavy)
    def create_draft(request:Request,body:CreateDraft):
        uid=write_owner(request)
        with input_errors():return store.create(uid,body.title,body.record,body.request_id)

    @app.get('/api/preparations/{id}',dependencies=heavy)
    def load_draft(id:str,request:Request):
        uid=owner(request)
        with input_errors():
            result=store.load(uid,id);session=result.pop('session')
            return {**result,'record':save(session,session.review['review_hash']),
                    'population':session.review['reviewed_population'],
                    'sources':sources(session.spec,session.files),
                    'review_hash':session.review['review_hash'],
                    'confirmation':None}

    @app.post('/api/preparations/{id}/handoff',dependencies=heavy)
    def handoff_draft(id:str,request:Request,body:HandoffDraft):
        uid=write_owner(request)
        with input_errors():
            result=store.load(uid,id)
            if result['revision']!=body.revision:
                raise StaleDraft('This preparation changed. Reopen it before continuing')
            session=result['session']
            if session.review['review_hash']!=body.review_hash:
                raise StaleDraft('The preparation preview changed. Reopen it before continuing')
            from .handoff import files_for
            record=session.confirm(body.review_hash,body.confirm)
            files=files_for(record)
            return {'files':[{'name':name,'content':content} for name,content in files.items()],
                    'title':result['title'],'revision':result['revision'],
                    'scope':'Prepared inputs only. Write a new claim and confirm the split binding before execution.'}

    @app.post('/api/preparations/{id}/preview',dependencies=heavy)
    def preview_draft(id:str,request:Request,body:PreviewDraft):
        uid=write_owner(request)
        with input_errors('These choices could not prepare every source record. Check the identity, repeat, mapping and evidence fields; your saved draft is unchanged.',explain_choices=True):
            result=store.load(uid,id)
            if result['revision']!=body.revision:
                raise StaleDraft('This preparation changed. Reopen it before previewing edits')
            session=result['session'];previous=session.review['reviewed_population']
            previous_extraction=session.review['extraction']
            review=session.preview(body.policies)
            return {'record':save(session,review['review_hash']),
                    'population':review['reviewed_population'],
                    'previous_population':previous,
                    'source_changes':source_changes(previous_extraction,review['extraction']),
                    'lineage':review['extraction']['lineage'],
                    'spec':review['extraction']['spec'],
                    'confirmation':None}

    @app.put('/api/preparations/{id}',dependencies=heavy)
    def replace_draft(id:str,request:Request,body:ReplaceDraft):
        uid=write_owner(request)
        with input_errors():return store.update(uid,id,body.revision,body.title,body.record)

    @app.delete('/api/preparations/{id}',status_code=204)
    def delete_draft(id:str,request:Request,body:DeleteDraft):
        uid=write_owner(request)
        with input_errors():store.delete(uid,id,body.revision)
        return Response(status_code=204)
