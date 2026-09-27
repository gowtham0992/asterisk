import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
import pytest
from app.preparation.proposal_store import ProposalStore
from app.preparation.store import MissingDraft,StaleDraft,DraftLimit
from tests.test_preparation_package import prepared
from tests.test_api import client,HEADERS
from app import main


def inputs():
    session=prepared()
    return {'files':session.files,'claim':'Evaluation generating units must be absent from training.',
            'documentation':['notes.txt'],'store_inputs':True}


@pytest.fixture
def tickets(tmp_path):
    def connect():
        db=sqlite3.connect(tmp_path/'proposals.sqlite',timeout=5);db.row_factory=sqlite3.Row;return db
    now=[1000.0]
    return ProposalStore(connect,lambda:now[0]),now


def preview(store,owner='alice'):
    data=inputs();return store.create(owner,data['files'],data['claim'],data['documentation'])


def test_preview_is_owned_hash_bound_single_use_and_expiring(tickets):
    store,now=tickets;t=preview(store)
    with pytest.raises(MissingDraft):store.claim('bob',t['ticket_id'],t['payload_hash'],True)
    with pytest.raises(ValueError):store.claim('alice',t['ticket_id'],t['payload_hash'],False)
    with pytest.raises(StaleDraft):store.claim('alice',t['ticket_id'],'0'*64,True)
    ticket=store.claim('alice',t['ticket_id'],t['payload_hash'],True)
    assert ticket.preview()['payload_hash']==t['payload_hash']
    with pytest.raises(StaleDraft):store.claim('alice',t['ticket_id'],t['payload_hash'],True)
    expiring=preview(store);now[0]+=3601
    with pytest.raises(MissingDraft):store.claim('alice',expiring['ticket_id'],expiring['payload_hash'],True)
    assert preview(store)['ticket_id']


def test_quota_and_discard_are_owner_scoped(tickets):
    store,_=tickets;items=[preview(store) for _ in range(3)]
    with pytest.raises(DraftLimit):preview(store)
    preview(store,'bob');store.discard('bob',items[0]['ticket_id'])
    with pytest.raises(DraftLimit):preview(store)
    store.discard('alice',items[0]['ticket_id']);preview(store)


def test_simultaneous_submissions_claim_exactly_once(tickets):
    store,_=tickets;t=preview(store)
    def attempt(_):
        try:store.claim('alice',t['ticket_id'],t['payload_hash'],True);return 'claimed'
        except StaleDraft:return 'rejected'
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(attempt,range(2)))
    assert sorted(results)==['claimed','rejected']


def test_api_preview_disabled_provider_then_one_mocked_completion(client,monkeypatch):
    preview=client.post('/api/preparations/proposal-preview',json=inputs(),headers=HEADERS)
    assert preview.status_code==201,preview.text
    p=preview.json();assert not p['provider_available']
    url='/api/preparations/proposals/'+p['ticket_id']+'/submit'
    body={'payload_hash':p['payload_hash'],'confirm_upload':True}
    assert client.post(url,json=body,headers=HEADERS).status_code==503
    calls=[]
    def complete(messages,maximum,timeout):
        calls.append(messages);assert maximum==4000 and timeout==60
        return {'content':json.dumps(prepared().spec)}
    monkeypatch.setattr(main.app.state,'preparation_complete',complete,raising=False)
    result=client.post(url,json=body,headers=HEADERS)
    assert result.status_code==200,result.text
    assert result.json()['status']=='review_required' and result.json()['confirmation'] is None
    assert result.json()['files']==inputs()['files']
    assert result.json()['model_proposal']['payload_hash']==p['payload_hash']
    assert client.post(url,json=body,headers=HEADERS).status_code==409
    assert len(calls)==1 and calls[0]==p['messages']


def test_failed_provider_does_not_reopen_a_ticket_or_expose_details(client,monkeypatch):
    p=client.post('/api/preparations/proposal-preview',json=inputs(),headers=HEADERS).json()
    calls=[]
    def fail(*args):calls.append(1);raise RuntimeError('private transport secret')
    monkeypatch.setattr(main.app.state,'preparation_complete',fail,raising=False)
    url='/api/preparations/proposals/'+p['ticket_id']+'/submit';body={'payload_hash':p['payload_hash'],'confirm_upload':True}
    error=client.post(url,json=body,headers=HEADERS)
    assert error.status_code==502 and 'private transport secret' not in error.text
    assert client.post(url,json=body,headers=HEADERS).status_code==409 and len(calls)==1
    recovered=client.get(url.removesuffix('/submit'))
    assert recovered.json()['result']=={'status':'failed'}
    assert 'private transport secret' not in recovered.text


def test_native_proposal_can_be_reviewed_and_saved_without_confirmation(client,monkeypatch):
    monkeypatch.setattr(main.app.state,'preparation_complete',lambda *args:{'content':json.dumps(prepared().spec)},raising=False)
    p=client.post('/api/preparations/proposal-preview',json=inputs(),headers=HEADERS).json()
    r=client.post('/api/preparations/proposals/'+p['ticket_id']+'/submit',json={'payload_hash':p['payload_hash'],'confirm_upload':True},headers=HEADERS).json()
    session=prepared()
    from app.preparation.draft import save
    policies=save(session,session.review['review_hash'])['policies']
    body={'files':r['files'],'spec_text':json.dumps(r['spec']),'policies':policies,'model_proposal':r['model_proposal']}
    reviewed=client.post('/api/preparations/review-proposal',json=body,headers=HEADERS)
    assert reviewed.status_code==200,reviewed.text
    record=reviewed.json()['record']
    assert reviewed.json()['confirmation'] is None
    assert record['model_proposal']['payload_hash']==p['payload_hash']
    created=client.post('/api/preparations',json={'title':'Native inputs','record':record,'store_inputs':True},headers=HEADERS)
    assert created.status_code==201,created.text
    reopened=client.get('/api/preparations/'+created.json()['id']).json()
    assert reopened['record']==record and reopened['confirmation'] is None
    changed=json.loads(json.dumps(body));changed['model_proposal']['response_text']='forged'
    assert client.post('/api/preparations/review-proposal',json=changed,headers=HEADERS).status_code==422
    assert len(client.get('/api/preparations').json()['drafts'])==1


def test_completed_response_survives_store_restart_and_remains_private(tickets):
    store,now=tickets;t=preview(store);id=t['ticket_id']
    assert store.recover('alice',id)['state']=='ready'
    store.claim('alice',id,t['payload_hash'],True)
    assert store.recover('alice',id)=={'ticket_id':id,'expires_at':t['expires_at'],'state':'attempted','result':None}
    result={'status':'review_required','confirmation':None,'spec':{'source':'synthetic'}}
    store.finish('alice',id,result)
    reopened=ProposalStore(store.connect,lambda:now[0])
    assert reopened.recover('alice',id)['result']==result
    with pytest.raises(MissingDraft):reopened.recover('bob',id)
    reopened.finish('bob',id,{'status':'failed'})
    reopened.finish('alice',id,{'status':'failed'})
    assert reopened.recover('alice',id)['result']==result
    now[0]+=3601
    with pytest.raises(MissingDraft):reopened.recover('alice',id)


def test_late_provider_result_cannot_resurrect_discarded_or_expired_sources(tickets):
    store,now=tickets
    for discard in [True,False]:
        t=preview(store);id=t['ticket_id'];store.claim('alice',id,t['payload_hash'],True)
        if discard:store.discard('alice',id)
        else:now[0]+=3601
        store.finish('alice',id,{'status':'review_required','files':{'private.txt':'synthetic'}})
        with pytest.raises(MissingDraft):store.recover('alice',id)
        with store.connect() as db:
            assert db.execute('SELECT count(*) FROM preparation_proposal_results WHERE id=?',(id,)).fetchone()[0]==0


def test_recovery_returns_exact_response_without_another_provider_call(client,monkeypatch):
    calls=[]
    def complete(*args):calls.append(1);return {'content':json.dumps(prepared().spec)}
    monkeypatch.setattr(main.app.state,'preparation_complete',complete,raising=False)
    p=client.post('/api/preparations/proposal-preview',json=inputs(),headers=HEADERS).json()
    url='/api/preparations/proposals/'+p['ticket_id']
    response=client.post(url+'/submit',json={'payload_hash':p['payload_hash'],'confirm_upload':True},headers=HEADERS)
    assert response.status_code==200
    for _ in range(2):
        recovered=client.get(url)
        assert recovered.status_code==200 and recovered.json()['result']==response.json()
    assert len(calls)==1
    client.delete(url,headers=HEADERS)
    assert client.get(url).status_code==404


def test_bad_upload_filename_has_actionable_guidance_and_can_be_corrected(client):
    body=inputs();body['files']['notes (copy).txt']=body['files'].pop('notes.txt');body['documentation']=['notes (copy).txt']
    response=client.post('/api/preparations/proposal-preview',json=body,headers=HEADERS)
    assert response.status_code==422
    assert 'Rename' in response.json()['detail']
    assert 'notes (copy)' not in response.text
    assert client.post('/api/preparations/proposal-preview',json=inputs(),headers=HEADERS).status_code==201


def test_preview_unknown_error_stays_private(client,monkeypatch):
    def fail(*args,**kwargs):raise ValueError('private source row and server path')
    monkeypatch.setattr(ProposalStore,'create',fail)
    response=client.post('/api/preparations/proposal-preview',json=inputs(),headers=HEADERS)
    assert response.status_code==422 and 'private source' not in response.text


def test_rejected_repeat_policy_is_visible_before_review_and_recoverable(client,monkeypatch):
    body=inputs();body['files']['data.csv']+='a,p1,train\n'
    preview=client.post('/api/preparations/proposal-preview',json=body,headers=HEADERS).json()
    monkeypatch.setattr(main.app.state,'preparation_complete',lambda *args:{'content':json.dumps(prepared().spec)},raising=False)
    url='/api/preparations/proposals/'+preview['ticket_id']
    response=client.post(url+'/submit',json={'payload_hash':preview['payload_hash'],'confirm_upload':True},headers=HEADERS)
    assert response.status_code==200
    result=response.json()
    assert result['status']=='review_required'
    assert 'Combining them passes the structural checks' in result['proposal_issue']
    assert 'does not establish that they are retransmissions' in result['proposal_issue']
    assert result['confirmation'] is None
    assert not result['spec']['sources'][0].get('deduplicate',False)
    assert client.get(url).json()['result']['proposal_issue']==result['proposal_issue']
    reviewed=client.post('/api/preparations/review-proposal',json={
        'files':result['files'],'spec_text':json.dumps(result['spec']),
        'model_proposal':result['model_proposal'],
        'policies':{'data.csv':{'sample':{'column':'sample'},'repeats':'collapse','evidence':result['spec']['citations']}}
    },headers=HEADERS)
    assert reviewed.status_code==200,reviewed.text
    assert reviewed.json()['population']=={'train':1,'test':1,'excluded':0}
    assert reviewed.json()['confirmation'] is None


@pytest.mark.parametrize('content', ['private malformed model output', json.dumps({
    'status':'extract','sources':[{'file':'data.csv','format':'csv','sample':{'column':'sample'},
    'entity':{'column':'subject'},'partition':{'value':'excluded'}}],
    'citations':[{'file':'notes.txt','start_line':1,'end_line':1}]})])
def test_rejected_completion_is_distinct_from_transport_failure(client,monkeypatch,content):
    p=client.post('/api/preparations/proposal-preview',json=inputs(),headers=HEADERS).json()
    calls=[]
    def complete(*args):
        calls.append(1)
        return {'content':content}
    monkeypatch.setattr(main.app.state,'preparation_complete',complete,raising=False)
    url='/api/preparations/proposals/'+p['ticket_id']
    body={'payload_hash':p['payload_hash'],'confirm_upload':True}
    result=client.post(url+'/submit',json=body,headers=HEADERS)
    assert result.status_code==200
    assert result.json()['status']=='rejected'
    assert result.json()['confirmation'] is None
    assert 'private malformed' not in result.text
    assert client.get(url).json()['result']==result.json()
    assert client.get(url).json()['manual_inputs']=={
        'files':inputs()['files'],'claim':inputs()['claim'],'projection':[]}
    assert client.post(url+'/submit',json=body,headers=HEADERS).status_code==409
    assert len(calls)==1


def test_failed_recovery_retains_only_owner_projected_inputs_until_expiry(tickets):
    store,now=tickets
    t=preview(store)
    store.claim('alice',t['ticket_id'],t['payload_hash'],True)
    store.finish('alice',t['ticket_id'],{'status':'rejected','confirmation':None})
    recovered=store.recover('alice',t['ticket_id'])
    assert recovered['manual_inputs']=={'files':inputs()['files'],'claim':inputs()['claim'],'projection':[]}
    assert recovered['result']['status']=='rejected'
    with pytest.raises(MissingDraft):store.recover('bob',t['ticket_id'])
    with pytest.raises(StaleDraft):store.claim('alice',t['ticket_id'],t['payload_hash'],True)
    now[0]+=3601
    with pytest.raises(MissingDraft):store.recover('alice',t['ticket_id'])


def test_intent_survives_ticket_draft_reopen_and_handoff_without_confirmation(tickets):
    from app.preparation.draft import save, restore
    store,_=tickets;data=inputs()
    intent={'target':'unseen_entities','unit':'frogs'}
    t=store.create('alice',data['files'],data['claim'],data['documentation'],evaluation_intent=intent)
    assert t['evaluation_intent']==intent
    ticket=store.claim('alice',t['ticket_id'],t['payload_hash'],True)
    session=ticket.submit(t['payload_hash'],True,lambda *_:{'content':json.dumps(prepared().spec)})['session']
    session.preview({'data.csv':{'sample':{'column':'sample'},'repeats':'distinct','evidence':prepared().spec['citations']}})
    draft=save(session,session.review['review_hash'])
    restored=restore(draft)
    assert restored.confirmation is None
    assert restored.model_proposal['approved_payload']['evaluation_intent']==intent
    from app.preparation.handoff import files_for
    handoff=files_for(restored.confirm(restored.review['review_hash'],True))
    record=json.loads(handoff['preparation-review.json'])
    assert record['model_proposal']['approved_payload']['evaluation_intent']==intent
    assert 'binding_confirmation' not in record
    assert 'evaluation_intent' not in json.loads(t['messages'][1]['content']), 'This context is retained locally, not added to the model prompt.'


def test_intent_changes_payload_hash_and_rejects_unsupported_purpose(tickets):
    from app.preparation.proposal import ProposalRequest
    data=inputs();args=(data['files'],data['claim'],data['documentation'])
    first=ProposalRequest(*args,evaluation_intent={'target':'unseen_entities','unit':'frogs'})
    second=ProposalRequest(*args,evaluation_intent={'target':'unseen_entities','unit':'recordings'})
    assert first.preview()['payload_hash']!=second.preview()['payload_hash']
    with pytest.raises(ValueError):ProposalRequest(*args,evaluation_intent={'target':'new_sites','unit':'locations'})


def test_api_saved_purpose_survives_reopen_and_export(client,monkeypatch):
    data={**inputs(),'evaluation_intent':{'target':'unseen_entities','unit':'frogs'}}
    p=client.post('/api/preparations/proposal-preview',json=data,headers=HEADERS)
    assert p.status_code==201
    p=p.json()
    monkeypatch.setattr(main.app.state,'preparation_complete',lambda *_:{'content':json.dumps(prepared().spec)},raising=False)
    response=client.post('/api/preparations/proposals/'+p['ticket_id']+'/submit',json={'payload_hash':p['payload_hash'],'confirm_upload':True},headers=HEADERS).json()
    reviewed=client.post('/api/preparations/review-proposal',json={'files':response['files'],'spec_text':json.dumps(response['spec']),'model_proposal':response['model_proposal'],'policies':{'data.csv':{'sample':{'column':'sample'},'repeats':'distinct','evidence':response['spec']['citations']}}},headers=HEADERS)
    assert reviewed.status_code==200
    saved=client.post('/api/preparations',json={'title':'Purpose persistence QA','record':reviewed.json()['record'],'store_inputs':True},headers=HEADERS)
    assert saved.status_code==201
    restored=client.get('/api/preparations/'+saved.json()['id']).json()
    assert restored['confirmation'] is None
    assert restored['record']['model_proposal']['approved_payload']['evaluation_intent']==data['evaluation_intent']
    handoff=client.post('/api/preparations/'+saved.json()['id']+'/handoff',json={'revision':restored['revision'],'review_hash':restored['review_hash'],'confirm':True},headers=HEADERS)
    assert handoff.status_code==200
    record=json.loads(next(f['content'] for f in handoff.json()['files'] if f['name']=='preparation-review.json'))
    assert record['model_proposal']['approved_payload']['evaluation_intent']==data['evaluation_intent']

def test_full_draft_workspace_blocks_preview_and_dispatch_without_consuming_ticket(client,monkeypatch):
    from app.preparation.draft import save
    session=prepared();record=save(session,session.review['review_hash'])
    preview=client.post('/api/preparations/proposal-preview',json=inputs(),headers=HEADERS).json()
    calls=[]
    monkeypatch.setattr(main.app.state,'preparation_complete',lambda *args:calls.append(args),raising=False)
    for i in range(10):
        response=client.post('/api/preparations',json={'title':f'Draft {i}','record':record,'store_inputs':True},headers=HEADERS)
        assert response.status_code==201
    assert client.get('/api/preparations/capabilities').json()['draft_capacity']=={'used':10,'limit':10,'available':False}
    blocked=client.post('/api/preparations/proposal-preview',json=inputs(),headers=HEADERS)
    assert blocked.status_code==409 and 'No model request was made' in blocked.text
    url='/api/preparations/proposals/'+preview['ticket_id']
    blocked=client.post(url+'/submit',json={'payload_hash':preview['payload_hash'],'confirm_upload':True},headers=HEADERS)
    assert blocked.status_code==409 and not calls
    assert client.get(url).json()['state']=='ready'
