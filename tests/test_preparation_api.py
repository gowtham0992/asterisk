import copy
import json
from fastapi.testclient import TestClient
from app import main
from app.preparation.draft import save
from app.preparation.review import executor
from tests.test_api import client,HEADERS
from tests.test_preparation_package import prepared

BASE='/api/preparations'


def payload():
    session=prepared()
    return {'title':'Specimen preparation','record':save(session,session.review['review_hash']),'store_inputs':True}


def create(client,body=None):
    response=client.post(BASE,json=body or payload(),headers=HEADERS)
    assert response.status_code==201,response.text
    return response.json()


def test_save_reopen_replace_and_delete(client):
    body=payload();meta=create(client,body);url=BASE+'/'+meta['id']
    reopened=client.get(url)
    assert reopened.status_code==200
    assert reopened.headers['cache-control']=='no-store'
    assert reopened.json()['record']==body['record']
    assert reopened.json()['confirmation'] is None
    assert reopened.json()['population']=={'train':1,'test':1,'excluded':0}
    listing=client.get(BASE).json()['drafts']
    assert listing==[meta] and 'record' not in listing[0]
    response=client.put(url,json={**body,'title':'Edited','revision':1},headers=HEADERS)
    assert response.status_code==200 and response.json()['revision']==2
    assert client.put(url,json={**body,'revision':1},headers=HEADERS).status_code==409
    assert client.request('DELETE',url,json={'revision':1},headers=HEADERS).status_code==409
    assert client.get(url).json()['title']=='Edited'
    assert client.request('DELETE',url,json={'revision':2},headers=HEADERS).status_code==204
    assert client.get(url).status_code==404 and client.get(BASE).json()['drafts']==[]
    assert client.request('DELETE',url,json={'revision':2},headers=HEADERS).status_code==404


def test_missing_session_and_foreign_owner_cannot_access(client):
    meta=create(client);url=BASE+'/'+meta['id']
    with TestClient(main.app) as other:
        assert other.get(BASE).status_code==401
        assert other.post(BASE,json=payload(),headers=HEADERS).status_code==401
        other.get('/api/session')
        assert other.get(BASE).json()['drafts']==[]
        assert other.get(url).status_code==404
        assert other.put(url,json={**payload(),'revision':1},headers=HEADERS).status_code==404
        assert other.request('DELETE',url,json={'revision':1},headers=HEADERS).status_code==404
    assert client.get(url).status_code==200


def test_csrf_and_explicit_storage_consent(client):
    assert client.post(BASE,json=payload()).status_code==403
    assert client.post(BASE,json=payload(),headers={**HEADERS,'Origin':'https://evil.example'}).status_code==403
    for changes in [{'store_inputs':False},{'owner':'someone-else'},{'confirmation':True}]:
        assert client.post(BASE,json={**payload(),**changes},headers=HEADERS).status_code==422
    body=payload();del body['store_inputs']
    assert client.post(BASE,json=body,headers=HEADERS).status_code==422
    assert client.get(BASE).json()['drafts']==[]


def test_malformed_and_confirmed_drafts_leave_existing_work_intact(client):
    meta=create(client);url=BASE+'/'+meta['id']
    session=prepared()
    bad=[{},session.confirm(session.review['review_hash'],True)]
    record=payload()['record'];record['inputs']['data.csv']='not the hashed input';bad.append(record)
    # Hash consistency alone is insufficient: recomputation rejects bad shapes.
    record=copy.deepcopy(payload()['record']);record['policies']=None
    record['draft_hash']=executor.sha(executor.canonical({k:v for k,v in record.items() if k!='draft_hash'}));bad.append(record)
    for record in bad:
        response=client.put(url,json={**payload(),'record':record,'revision':1},headers=HEADERS)
        assert response.status_code==422,response.text
        assert 'not the hashed input' not in response.text
    assert client.get(url).json()['revision']==1


def test_quota_can_be_freed_by_deletion(client):
    items=[create(client) for _ in range(10)]
    assert client.post(BASE,json=payload(),headers=HEADERS).status_code==409
    assert client.request('DELETE',BASE+'/'+items[0]['id'],json={'revision':1},headers=HEADERS).status_code==204
    create(client)
    assert len(client.get(BASE).json()['drafts'])==10


def test_revision_is_strict_and_content_type_is_json(client):
    meta=create(client);url=BASE+'/'+meta['id']
    for revision in [True,'1',0,1.5]:
        assert client.put(url,json={**payload(),'revision':revision},headers=HEADERS).status_code==422
    # The installed FastAPI rejects untyped request bodies before the handler.
    assert client.post(BASE,content=json.dumps(payload()),headers=HEADERS).status_code==422


def test_preparation_limit_does_not_change_other_upload_limits(client,monkeypatch):
    import app.preparation.api as api
    monkeypatch.setattr(api,'REQUEST_LIMIT',1000)
    assert client.post(BASE,content='x'*1001,headers=HEADERS).status_code==413
    # Restore the actual bound and cross the legacy 4.2 MB threshold using a
    # valid draft. This tests the middleware path, not only its constant.
    monkeypatch.setattr(api,'REQUEST_LIMIT',32_100_000)
    body=payload();record=body['record'];record['inputs']['extra.txt']='x'*4_200_001
    record['draft_hash']=executor.sha(executor.canonical({k:v for k,v in record.items() if k!='draft_hash'}))
    create(client,body)
    assert client.post('/api/audits',content='x'*4_200_001,headers=HEADERS).status_code==413


def test_policy_preview_does_not_persist_until_explicit_save(client):
    body=payload();meta=create(client,body);url=BASE+'/'+meta['id']
    loaded=client.get(url).json()
    assert loaded['sources'][0]['columns']==['sample','split','subject']
    policies=copy.deepcopy(body['record']['policies'])
    policies['data.csv']['sample']={'row':True}
    preview=client.post(url+'/preview',json={'revision':1,'policies':policies},headers=HEADERS)
    assert preview.status_code==200,preview.text
    result=preview.json()
    assert result['confirmation'] is None
    assert result['record']['policies']['data.csv']['sample']=={'row':True}
    assert result['previous_population']==loaded['population']
    assert client.get(url).json()['record']==body['record']
    saved=client.put(url,json={**body,'record':result['record'],'revision':1},headers=HEADERS)
    assert saved.status_code==200 and saved.json()['revision']==2
    assert client.get(url).json()['record']==result['record']


def test_preview_rejects_invalid_policy_stale_revision_and_foreign_session(client):
    body=payload();meta=create(client,body);url=BASE+'/'+meta['id']
    policy=copy.deepcopy(body['record']['policies']);policy['data.csv']['sample']={'column':'missing_column'}
    assert client.post(url+'/preview',json={'revision':1,'policies':policy},headers=HEADERS).status_code==422
    assert client.get(url).json()['record']==body['record']
    assert client.post(url+'/preview',json={'revision':2,'policies':body['record']['policies']},headers=HEADERS).status_code==409
    with TestClient(main.app) as other:
        other.get('/api/session')
        assert other.post(url+'/preview',json={'revision':1,'policies':{}},headers=HEADERS).status_code==404


def test_handoff_requires_current_confirmation_and_keeps_new_check_unconfirmed(client,monkeypatch):
    meta=create(client);url=BASE+'/'+meta['id'];loaded=client.get(url).json()
    body={'revision':1,'review_hash':loaded['review_hash'],'confirm':True}
    assert client.post(url+'/handoff',json={**body,'confirm':False},headers=HEADERS).status_code==422
    assert client.post(url+'/handoff',json={**body,'review_hash':'0'*64},headers=HEADERS).status_code==409
    assert client.post(url+'/handoff',json={**body,'revision':2},headers=HEADERS).status_code==409
    with TestClient(main.app) as other:
        other.get('/api/session')
        assert other.post(url+'/handoff',json=body,headers=HEADERS).status_code==404
    handoff=client.post(url+'/handoff',json=body,headers=HEADERS)
    assert handoff.status_code==200,handoff.text
    files={f['name']:f['content'] for f in handoff.json()['files']}
    assert set(files)=={'splits.csv','entities.csv','asterisk.json','preparation-review.json','README.md'}
    from app.preparation.verify_record import verify
    verified=verify(json.loads(files['preparation-review.json']))
    assert verified['recomputed_population']=={'train':1,'test':1,'excluded':0}
    assert client.get(url).json()['confirmation'] is None
    new=client.post('/api/investigations',headers=HEADERS,json={
        'title':'Prepared split','claim':'Evaluation patients must be absent from training.',
        'evaluation_intent':{'target':'unseen_entities','unit':'patients'},
        'saved_binding':json.loads(files.pop('asterisk.json'))['arguments'],
        'files':[{'name':name,'content':content} for name,content in files.items()]})
    assert new.status_code==201,new.text
    check='/api/investigations/'+new.json()['id']
    plan=client.post(check+'/manual-plan',headers=HEADERS)
    assert plan.status_code==200,plan.text
    assert not plan.json().get('preflight_confirmation')
    assert not plan.json().get('result')
    # Preparing inputs never manufactures an authorization to execute them.
    from app import investigations
    monkeypatch.setenv('NEBIUS_API_KEY','synthetic-key')
    monkeypatch.setenv('NEBIUS_PROJECT_ID','synthetic-project')
    monkeypatch.setattr(investigations,'configured_image',lambda root:'synthetic-image')
    def forbidden(*args,**kwargs):raise AssertionError('Execution must not start')
    monkeypatch.setattr(investigations,'Thread',forbidden)
    blocked=client.post(check+'/run',json={'confirm_upload':True},headers=HEADERS)
    assert blocked.status_code==409 and 'confirm the exact column binding' in blocked.json()['detail']


def test_creation_request_id_returns_same_draft_and_rejects_changed_payload(client):
    from app.preparation.draft import save
    from tests.test_preparation_package import prepared
    session=prepared()
    body={'title':'Retry-safe API draft','record':save(session,session.review['review_hash']),
          'store_inputs':True,'request_id':'a'*32}
    first=client.post('/api/preparations',json=body,headers=HEADERS)
    second=client.post('/api/preparations',json=body,headers=HEADERS)
    assert first.status_code==second.status_code==201
    assert first.json()==second.json()
    assert len(client.get('/api/preparations').json()['drafts'])==1
    assert client.post('/api/preparations',json={**body,'title':'Different'},headers=HEADERS).status_code==409
    assert client.post('/api/preparations',json={**body,'request_id':'invalid'},headers=HEADERS).status_code==422


def test_preview_changes_compare_against_saved_draft_not_original_proposal(client):
    body=payload();meta=create(client,body);url=BASE+'/'+meta['id']
    policies=copy.deepcopy(body['record']['policies'])
    policies['data.csv']['sample']={'row':True}
    first=client.post(url+'/preview',json={'revision':1,'policies':policies},headers=HEADERS).json()
    assert first['source_changes']['changed_records']==2
    assert first['source_changes']['changed_fields']=={'sample':2,'entity':0,'partition':0}
    assert client.put(url,json={**body,'record':first['record'],'revision':1},headers=HEADERS).status_code==200
    same=client.post(url+'/preview',json={'revision':2,'policies':policies},headers=HEADERS).json()
    assert same['source_changes']['changed_records']==0
    policies['data.csv']['partition']={'column':'split','map':{'train':'test','test':'train'}}
    changed=client.post(url+'/preview',json={'revision':2,'policies':policies},headers=HEADERS).json()
    assert changed['source_changes']['changed_fields']=={'sample':0,'entity':0,'partition':2}
    assert changed['source_changes']['source_records']==2
    assert changed['population']==changed['previous_population']  # totals conceal the swap
    assert changed['source_changes']['examples'][0]['before']['partition']!=changed['source_changes']['examples'][0]['after']['partition']
    assert client.get(url).json()['revision']==2


def test_native_review_reports_changes_from_starting_proposal_without_persisting(client):
    body=payload();record=body['record'];policies=copy.deepcopy(record['policies'])
    policies['data.csv']['entity']={'column':'sample'}
    response=client.post(BASE+'/review-proposal',json={'files':record['inputs'],'spec_text':json.dumps(record['original_spec']),'policies':policies},headers=HEADERS)
    assert response.status_code==200,response.text
    changes=response.json()['source_changes']
    assert changes['changed_fields']=={'sample':0,'entity':2,'partition':0}
    assert changes['examples'][0]['before']['entity']=='p1'
    assert changes['examples'][0]['after']['entity']=='a'
    assert client.get(BASE).json()['drafts']==[]


def test_known_preview_failure_explains_action_without_changing_draft(client):
    body=payload();meta=create(client,body);url=BASE+'/'+meta['id']
    policies=copy.deepcopy(body['record']['policies'])
    policies['data.csv'].update(sample={'row':True},repeats='collapse')
    response=client.post(url+'/preview',json={'revision':1,'policies':policies},headers=HEADERS)
    assert response.status_code==422
    assert 'Choose the documented observation-ID column or lookup' in response.json()['detail']
    assert 'No draft was saved or confirmed.' in response.json()['detail']
    assert client.get(url).json()['record']==body['record']


def test_unknown_preview_failure_does_not_reflect_private_exception(client,monkeypatch):
    from app.preparation.session import ReviewSession
    body=payload();meta=create(client,body)
    original=ReviewSession.preview
    calls=0
    def fail_edited(self,policies):
        nonlocal calls
        calls+=1
        if calls==2:raise ValueError('private-source-value /private/secret/path')
        return original(self,policies)
    monkeypatch.setattr(ReviewSession,'preview',fail_edited)
    response=client.post(BASE+'/'+meta['id']+'/preview',json={'revision':1,'policies':body['record']['policies']},headers=HEADERS)
    assert response.status_code==422
    assert 'private-source-value' not in response.text and '/private/' not in response.text
    assert 'could not prepare every source record' in response.json()['detail']


def test_native_review_guidance_distinguishes_empty_partition_and_short_identity(client):
    session=prepared()
    base={'files':session.files,'spec_text':json.dumps(session.spec),'policies':save(session,session.review['review_hash'])['policies']}
    cases=[({'partition':{'value':'train'}},'leave training or evaluation empty'),
           ({'sample':{'column':'sample','prefix':128}},'longer than at least one source value')]
    for change,expected in cases:
        request=copy.deepcopy(base);request['policies']['data.csv'].update(change)
        response=client.post(BASE+'/review-proposal',json=request,headers=HEADERS)
        assert response.status_code==422
        assert expected in response.json()['detail']
    assert client.get(BASE).json()['drafts']==[]
