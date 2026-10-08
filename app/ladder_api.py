"""Ladder endpoints: local measurement, the exact proposal payload, a Nemotron proposal through Nebius Token
Factory, and a replay in a Nebius Sandbox. Only /propose calls a model and only /replay runs remote code."""
import hashlib
import json
import os
import time
import sqlite3
from pathlib import Path
from contextlib import nullcontext
from .ladder_limits import Limits

from fastapi import HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from . import ladder_proposal
from .ladder import LadderError, measure, review_context
from .ladder_sandbox import replay
from .preparation.review import executor
from .sandbox import SandboxError

BASE = 'https://api.tokenfactory.nebius.com/v1/'
# Super with the v4 prompt ships by default (evaluation/ladder-proposal-v5). Ultra passed fresh set B but did not replicate
# on set C, so it stays an option.
MODELS = {'nvidia/nemotron-3-super-120b-a12b': 'Nemotron 3 Super', 'nvidia/Nemotron-3-Ultra-550b-a55b': 'Nemotron 3 Ultra'}
DEFAULT_MODEL = 'nvidia/nemotron-3-super-120b-a12b'


class LadderFile(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str = Field(min_length=1, max_length=300)
    content: str = Field(max_length=16_000_000)


class LadderRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    spec: dict
    files: list[LadderFile] = Field(min_length=1, max_length=80)
    confirmed: list[str] = Field(default_factory=list, max_length=8)
    proposal_id: str | None = Field(default=None, pattern=r'^[a-f0-9]{24}$')


class ReviewRequest(LadderRequest):
    documentation: list[str] | None = Field(default=None, max_length=20)


class ProposalRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    claim: str = Field(min_length=3, max_length=1000)
    files: list[LadderFile] = Field(min_length=1, max_length=80)
    documentation: list[str] = Field(min_length=1, max_length=20)
    share_examples: list[tuple[str, str]] = Field(default_factory=list, max_length=20)
    model: str = DEFAULT_MODEL


def _files(items):
    files = {}
    for item in items:
        if item.name in files:
            raise HTTPException(422, 'Each file name may appear once.')
        files[item.name] = item.content
    if sum(len(v.encode()) for v in files.values()) > executor.MAX_BYTES:
        raise HTTPException(413, 'Ladder inputs exceed 16 MB total.')
    return files


def _messages(body, files):
    if body.model not in MODELS:
        raise HTTPException(422, 'Choose Nemotron 3 Super or Nemotron 3 Ultra.')
    try:
        return ladder_proposal.request(body.claim, files, body.share_examples, body.documentation)
    except LadderError as exc:
        raise HTTPException(422, str(exc)) from None


def token_factory(model, key):
    """A completion function for ladder_proposal.propose: one bounded Token Factory call per invocation."""
    from openai import OpenAI
    usage = {'calls': 0, 'total_tokens': 0}

    def complete(messages, maximum, timeout):
        with OpenAI(base_url=os.getenv('NEBIUS_BASE_URL', BASE), api_key=key, timeout=timeout, max_retries=0) as client:
            response = client.chat.completions.create(model=model, messages=messages, temperature=0, max_tokens=maximum,
                                                      response_format={'type': 'json_object'})
        usage['calls'] += 1
        usage['total_tokens'] += response.usage.total_tokens if response.usage else 0
        return response.choices[0].message.content or ''
    return complete, usage


def register(app, owner, completion=token_factory, sandbox=replay, connect=None):
    limits = Limits(connect) if connect else None
    store = None
    if connect is not None:
        from .ladder_receipts import register as register_receipts
        store = register_receipts(app, connect, owner, LadderRequest, _files)
    @app.get('/api/ladder/benchmark-inputs')
    def benchmark_inputs(request: Request):
        owner(request)
        folder=Path(os.getenv('ASTERISK_BENCHMARK_DIR', str(Path(__file__).resolve().parents[1]/'.data/benchmarks')))/'wsibench'
        try:
            provenance=json.loads((folder/'provenance.json').read_text())
            files={n:(folder/n).read_text() for n in ['train.json','test.json','README.md']}
            for name in ['train.json','test.json']:
                if hashlib.sha256(files[name].encode()).hexdigest()!=provenance[name]['projection_sha256']:
                    raise ValueError('Projected inputs differ from the installed manifest')
        except (OSError, ValueError, KeyError):
            raise HTTPException(503, 'The real benchmark projection is not installed or its hashes differ. Use your own files or the synthetic example.') from None
        return {'claim':'No report-task evaluation patient appears in the report-task training data.',
                'files':[{'name':n,'content':v} for n,v in files.items()], 'provenance':provenance,
                'notice':'Real public benchmark, projected to image identifiers only. No model call or measurement has happened. The source authors’ intended claim is not established here.'}

    @app.get('/api/ladder/allowance')
    def allowance(request: Request):
        who = owner(request)
        return limits.status(who, getattr(request.state, 'judge', False)) if limits else {'mode':'local','remaining_calls':None,'active':True}

    @app.post('/api/ladder')
    def ladder(body: LadderRequest, request: Request):
        owner(request)
        try:
            return measure(body.spec, _files(body.files), body.confirmed)
        except LadderError as exc:
            raise HTTPException(422, str(exc)) from None

    @app.post('/api/ladder/review')
    def review(body: ReviewRequest, request: Request):
        owner(request)
        try:
            files = _files(body.files)
            context = review_context(body.spec, files)
            from .ladder_citations import review as citation_review
            context['citation_review'] = citation_review(body.spec, files, body.documentation)
            return context
        except (LadderError, executor.ExtractionError, ValueError) as exc:
            raise HTTPException(422, str(exc)) from None

    @app.post('/api/ladder/preview')
    def preview(body: ProposalRequest, request: Request):
        """Exactly what /propose would send, so a person can read it first. No network call."""
        owner(request)
        messages = _messages(body, _files(body.files))
        text = json.dumps(messages, ensure_ascii=False)
        return {'model': body.model, 'model_name': MODELS[body.model], 'provider': 'Nebius Token Factory',
                'messages': messages, 'characters': len(text), 'payload_sha256': hashlib.sha256(text.encode()).hexdigest()}

    @app.post('/api/ladder/propose')
    def propose(body: ProposalRequest, request: Request):
        who = owner(request)
        files = _files(body.files)
        messages = _messages(body, files)
        key = os.getenv('NEBIUS_API_KEY')
        if not key:
            raise HTTPException(503, 'Add NEBIUS_API_KEY to the local .env file and restart Asterisk.')
        reservation = limits.operation(who, 2, judge=getattr(request.state, 'judge', False)) if limits else nullcontext()
        complete, usage = completion(body.model, key)
        start = time.monotonic()
        try:
            with reservation:
                proposal, attempts = ladder_proposal.propose(body.claim, files, complete, body.share_examples,
                                                             documentation=body.documentation)
        except LadderError as exc:
            raise HTTPException(422, f'Nemotron did not return a usable ladder after one repair: {exc}') from None
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(502, 'Nebius Token Factory did not complete the request. Check credits and model access, then retry.') from None
        response = {'proposal': proposal, 'attempts': [{'error': a['error']} for a in attempts], 'model': body.model,
                'model_name': MODELS[body.model], 'provider': 'Nebius Token Factory', 'calls': usage['calls'],
                'total_tokens': usage['total_tokens'], 'seconds': round(time.monotonic() - start, 2),
                'payload_sha256': hashlib.sha256(json.dumps(messages, ensure_ascii=False).encode()).hexdigest()}

        response['proposal_id'] = None
        if store:
            try:
                response['proposal_id'] = store.record_proposal(who, response, files, ladder_proposal.PROMPT_VERSION)
            except (sqlite3.Error, OSError):
                response['proposal_record_error'] = 'The proposal completed, but its origin could not be saved. Receipts will not claim a recorded model origin.'
        return response

    @app.post('/api/ladder/replay')
    def replay_ladder(body: LadderRequest, request: Request):
        who = owner(request)
        if body.proposal_id:
            if store is None:
                raise HTTPException(503, 'Proposal storage is unavailable.')
            store.binding_origin(who, body.proposal_id, body.spec, _files(body.files))
        project = os.getenv('NEBIUS_PROJECT_ID') or os.getenv('NEBIUS_AI_PROJECT')
        try:
            with limits.operation(who, 1, judge=getattr(request.state, 'judge', False)) if limits else nullcontext():
                result, provenance = sandbox(body.spec, _files(body.files), body.confirmed, os.getenv('NEBIUS_API_KEY'), project)
        except LadderError as exc:
            raise HTTPException(422, str(exc)) from None
        except SandboxError as exc:
            raise HTTPException(502, str(exc)) from None
        response = {'result': result, 'provenance': provenance}
        if store is not None:
            try:
                saved = store.save(who, body.spec, _files(body.files), result, provenance, proposal_id=body.proposal_id)
                response['receipt_id'] = saved['id']
            except (sqlite3.Error, OSError, HTTPException):
                response['receipt_error'] = 'Replay matched, but workspace storage failed. Download the JSON receipt now; another replay is not needed.'
        return response
