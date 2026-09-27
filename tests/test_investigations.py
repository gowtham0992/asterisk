import json,io,zipfile
import pytest
from fastapi.testclient import TestClient
from app import main,investigations as inv
from tests.test_api import client,HEADERS

from tests.test_primitives import FILES,ARGS,CITE,Trusted
PAYLOAD={'title':'Test receipt','claim':'Specimens must be absent from training.','files':[{'name':n,'content':v} for n,v in FILES.items()],'model':'super'}
PLAN={'kind':'entity_overlap','binding':ARGS,'scope':'Specimens stay out of evaluation.','steps':['Join the identity mapping.'],'citations':[CITE],'limitations':['Only supplied identity records.']}
@pytest.fixture
def setup(client,monkeypatch):
    with main.connect() as db:db.execute('CREATE TABLE IF NOT EXISTS investigations (id TEXT PRIMARY KEY, owner TEXT NOT NULL, payload TEXT NOT NULL)')
    monkeypatch.setenv('NEBIUS_API_KEY','test-secret-never-export')
    monkeypatch.setenv('NEBIUS_PROJECT_ID','test-project')
    monkeypatch.setenv('ASTERISK_PROBE_IMAGE','test-image')
    from app.primitive_runtime import DRIVER
    from app.probes import sha
    monkeypatch.setenv('ASTERISK_PROBE_DRIVER_SHA256',sha(DRIVER))
    pending=[]
    class DeferredThread:
        def __init__(self,target,args,daemon):self.target=target;self.args=args
        def start(self):pending.append(lambda:self.target(*self.args))
    monkeypatch.setattr(inv,'Thread',DeferredThread)
    monkeypatch.setattr(inv,'propose_plan',lambda *a:(inv.validate_plan(inv.Plan.model_validate(PLAN),FILES).model_dump(),{'model':'test-model','tokens':12}))
    return client,pending

def create(c,body=None):
    r=c.post('/api/investigations',json=body or PAYLOAD,headers=HEADERS);assert r.status_code==201,r.text;return r.json()['id']
def test_remote_consent_and_double_start(setup):
    c,jobs=setup;id=create(c);url=f'/api/investigations/{id}'
    assert c.post(url+'/propose',json={},headers=HEADERS).status_code==422
    assert c.post(url+'/propose',json={'confirm_upload':True},headers=HEADERS).status_code==202
    assert c.post(url+'/propose',json={'confirm_upload':True},headers=HEADERS).status_code==409
    assert c.get(url).json()['state']=='planning'
    assert c.delete(url,headers=HEADERS).status_code==409
    jobs.pop()()
    assert c.get(url).json()['state']=='review'
    assert c.post(url+'/run',json={},headers=HEADERS).status_code==422

def test_session_isolation_including_export_and_revisions(setup):
    c,_=setup;id=create(c)
    with TestClient(main.app) as other:
        other.get('/api/session')
        assert all(row['id']!=id for row in other.get('/api/investigations').json())
        for suffix in ('','/inputs','/export','/comparison'):
            assert other.get('/api/investigations/'+id+suffix).status_code==404
        body={**PAYLOAD,'parent_id':id}
        assert other.post('/api/investigations',json=body,headers=HEADERS).status_code==404

@pytest.mark.parametrize('name',['../.env','.env','sub/.env','key.pem','/etc/passwd','src/../secret.py'])
def test_rejects_secrets_and_unsafe_upload_paths(setup,name):
    c,_=setup;body={**PAYLOAD,'files':[{'name':name,'content':'secret'}]}
    assert c.post('/api/investigations',json=body,headers=HEADERS).status_code==422

def test_run_export_and_revision_preserve_original(setup,monkeypatch):
    c,jobs=setup;id=create(c);url=f'/api/investigations/{id}'
    c.post(url+'/propose',json={'confirm_upload':True},headers=HEADERS);jobs.pop()()
    monkeypatch.setattr(inv,'ProbeSandbox',lambda *args:Trusted())
    assert c.post(url+'/run',json={'confirm_upload':True},headers=HEADERS).status_code==409
    binding=c.post(url+'/binding-preview',json={'arguments':ARGS},headers=HEADERS).json()
    assert [r['sample'] for r in binding['source_examples']['rows']]==['a','b','c']
    assert 'do not establish' in binding['source_examples']['scope']
    accepted={'arguments':ARGS,'binding_hash':binding['binding_hash'],'confirm':True}
    assert c.post(url+'/accept-binding',json=accepted,headers=HEADERS).status_code==200
    assert c.post(url+'/accept-binding',json=accepted,headers=HEADERS).status_code==200
    assert c.post(url+'/run',json={'confirm_upload':True},headers=HEADERS).status_code==202
    assert c.post(url+'/run',json={'confirm_upload':True},headers=HEADERS).status_code==409
    jobs.pop()()
    original=c.get(url).json();assert original['state']=='complete'
    summary=next(row for row in c.get('/api/investigations').json() if row['id']==id)
    assert summary['verdict']=='violation'
    assert 'result' not in summary and 'input' not in summary
    archive=c.get(url+'/export');assert archive.status_code==200
    with zipfile.ZipFile(io.BytesIO(archive.content)) as z:
        assert json.loads(z.read('result.json'))['preflight_confirmation']['confirmed']
        assert all(b'test-secret-never-export' not in z.read(n) for n in z.namelist())
    revision=c.post(url+'/with-plan',json={'plan':PLAN,'note':'Clarify the scope.'},headers=HEADERS)
    assert revision.status_code==201
    child=revision.json()['id'];comparison=c.get('/api/investigations/'+child+'/comparison').json()
    assert comparison['before']['verdict']=='violation' and comparison['after']['verdict'] is None
    assert c.get(url).json()==original

def test_provider_failure_preserves_inputs_and_redacts_secret(setup,monkeypatch):
    c,jobs=setup;id=create(c);url=f'/api/investigations/{id}'
    def fail(*args):raise RuntimeError('provider error test-secret-never-export private data')
    monkeypatch.setattr(inv,'propose_plan',fail)
    c.post(url+'/propose',json={'confirm_upload':True},headers=HEADERS);jobs.pop()()
    result=c.get(url);assert result.json()['state']=='failed'
    assert 'test-secret-never-export' not in result.text and 'private data' not in result.text
    assert c.get(url+'/inputs').json()['files']==PAYLOAD['files']

def test_revised_plan_rejects_invented_citation(setup):
    c,jobs=setup;id=create(c);url=f'/api/investigations/{id}'
    c.post(url+'/propose',json={'confirm_upload':True},headers=HEADERS);jobs.pop()()
    bad={**PLAN,'citations':[{'file':'src/train.py','quote':'made up'}]}
    assert c.post(url+'/with-plan',json={'plan':bad,'note':'New scope'},headers=HEADERS).status_code==422

def test_binding_confirmation_requires_exact_record_and_exports_it(setup):
    from tests.test_soundness_v3 import pending_result
    from app.bindings import pending_binding
    c,_=setup;id=create(c);url=f'/api/investigations/{id}'
    files,result=pending_result();result.update(probes={},runs=[],replays=[])
    result['pending_binding']=pending_binding(result)
    with main.connect() as db:
        row=db.execute('SELECT payload FROM investigations WHERE id=?',(id,)).fetchone()
        a=json.loads(row['payload']);a.update(state='complete',result=result)
        a['input']['files']=[{'name':n,'content':v} for n,v in files.items()]
        db.execute('UPDATE investigations SET payload=? WHERE id=?',(json.dumps(a),id))
    bad=c.post(url+'/confirm-binding',json={'confirm':True,'reviewer':'human','binding_hash':'0'*64},headers=HEADERS)
    assert bad.status_code==409
    before=c.get(url+'/export')
    with zipfile.ZipFile(io.BytesIO(before.content)) as z:
        assert json.loads(z.read('result.json'))['verdict']['verdict']=='clear_pending_confirmation'
    body={'confirm':True,'binding_hash':result['pending_binding']['binding_hash']}
    assert c.post(url+'/confirm-binding',json=body,headers=HEADERS).status_code==422
    assert c.post(url+'/confirm-binding',json={**body,'reviewer':'automated'},headers=HEADERS).status_code==422
    assert c.get(url).json()['result']['verdict']['verdict']=='clear_pending_confirmation'
    body['reviewer']='human'
    assert c.post(url+'/confirm-binding',json={**body,'confirm':False},headers=HEADERS).status_code==422
    assert c.post(url+'/confirm-binding',json=body,headers=HEADERS).status_code==200
    assert c.post(url+'/confirm-binding',json=body,headers=HEADERS).status_code==409
    with zipfile.ZipFile(io.BytesIO(c.get(url+'/export').content)) as z:
        saved=json.loads(z.read('result.json'))
        assert saved['verdict']['verdict']=='clear'
        assert saved['binding_confirmation']['confirmed_at']
        assert saved['verdict_before_confirmation']['verdict']=='clear_pending_confirmation'

def test_v4_binding_review_rejects_wrong_roles_stale_hash_and_foreign_session(setup):
    c,jobs=setup;id=create(c);url=f'/api/investigations/{id}'
    c.post(url+'/propose',json={'confirm_upload':True},headers=HEADERS);jobs.pop()()
    wrong=c.post(url+'/binding-preview',json={'arguments':{**ARGS,'sample_column':'part'}},headers=HEADERS)
    assert wrong.status_code==422 and '2 distinct values across 3 rows' in wrong.text
    assert c.post(url+'/accept-binding',json={'arguments':ARGS,'confirm':False},headers=HEADERS).status_code==422
    assert c.post(url+'/accept-binding',json={'arguments':ARGS,'confirm':True,'binding_hash':'0'*64},headers=HEADERS).status_code==409
    with TestClient(main.app) as other:
        other.get('/api/session')
        for suffix in ('binding-preview','accept-binding'):
            assert other.post(url+'/'+suffix,json={'arguments':ARGS,'confirm':True},headers=HEADERS).status_code==404
    assert c.get(url).json().get('preflight_confirmation') is None

def test_v4_model_and_category_surface_are_narrow(setup):
    c,_=setup;config=c.get('/api/investigations/config').json()
    assert list(config['models'])==['super']
    assert config['supported_categories']==['entity_overlap']
    assert c.post('/api/investigations',json={**PAYLOAD,'model':'ultra'},headers=HEADERS).status_code==422

def test_witness_api_is_read_only_owned_and_hash_checked(setup):
    from app.primitives import measure
    c,_=setup;id=create(c);url=f'/api/investigations/{id}'
    with main.connect() as db:
        a=json.loads(db.execute('SELECT payload FROM investigations WHERE id=?',(id,)).fetchone()['payload'])
        a['result']={'primitive_measurements':{'measurement-1':measure('entity_overlap',FILES,ARGS)}}
        db.execute('UPDATE investigations SET payload=? WHERE id=?',(json.dumps(a),id))
    endpoint=url+'/measurements/measurement-1/witnesses/0'
    before=c.get(url).json()
    response=c.get(endpoint)
    assert response.status_code==200,response.text
    assert response.json()['entity']=='u'
    assert c.get(url).json()==before
    assert c.get(endpoint[:-1]+'99').status_code==404
    assert c.get(endpoint.replace('measurement-1','missing')).status_code==404
    with TestClient(main.app) as other:
        other.get('/api/session')
        assert other.get(endpoint).status_code==404
    with main.connect() as db:
        a['input']['files'][0]['content']+='d,test\n'
        db.execute('UPDATE investigations SET payload=? WHERE id=?',(json.dumps(a),id))
    assert c.get(endpoint).status_code==409


def test_revisions_cannot_offer_unsupported_category(setup):
    c,jobs=setup;id=create(c);url=f'/api/investigations/{id}'
    c.post(url+'/propose',json={'confirm_upload':True},headers=HEADERS);jobs.pop()()
    response=c.post(url+'/with-plan',json={'plan':{**PLAN,'kind':'checkpoint_selection'},'note':'Change category'},headers=HEADERS)
    assert response.status_code==422


def test_history_is_summary_and_worksheet_is_bound_and_owner_scoped(setup):
    from tests.test_researcher_handoff import investigation
    from app.probes import sha
    c,_=setup;id=create(c);url=f'/api/investigations/{id}'
    assert c.get(url+'/review-worksheet').status_code==409
    result=investigation()['result']
    with main.connect() as db:
        a=json.loads(db.execute('SELECT payload FROM investigations WHERE id=?',(id,)).fetchone()['payload'])
        a.update(state='complete',result=result)
        db.execute('UPDATE investigations SET payload=? WHERE id=?',(json.dumps(a),id))
    response=c.get(url+'/review-worksheet')
    assert response.status_code==200
    assert sha(json.dumps(result,sort_keys=True,separators=(',',':'))) in response.text
    rows=c.get('/api/investigations').json()
    assert 'primitive_measurements' not in json.dumps(rows)
    assert 'input' not in json.dumps(rows)
    with TestClient(main.app) as other:
        other.get('/api/session')
        assert other.get(url+'/review-worksheet').status_code==404


def test_walkthrough_is_persistent_guidance_not_confirmation(setup):
    c,jobs=setup
    id=create(c,{**PAYLOAD,'walkthrough':'specimen-v1','saved_binding':ARGS})
    url=f'/api/investigations/{id}'
    assert c.get(url).json()['walkthrough']=='specimen-v1'
    assert c.get(url+'/inputs').json()['walkthrough']=='specimen-v1'
    plan=c.post(url+'/manual-plan',headers=HEADERS).json()
    assert plan['plan']['binding']==ARGS
    assert not plan.get('preflight_confirmation')
    assert not jobs
    assert c.post(url+'/run',json={'confirm_upload':True},headers=HEADERS).status_code==409
    invalid=c.post('/api/investigations',json={**PAYLOAD,'walkthrough':'anything-else'},headers=HEADERS)
    assert invalid.status_code==422


def test_rejected_manual_setup_retains_diagnostics_without_inference(setup):
    c,jobs=setup
    files=[{'name':'broken.csv','content':'sample,partition\na,train,extra\n'}]
    id=create(c,{**PAYLOAD,'files':files})
    url=f'/api/investigations/{id}'
    response=c.post(url+'/manual-plan',headers=HEADERS)
    assert response.status_code==422
    saved=c.get(url).json()
    assert saved['state']=='draft' and saved['plan'] is None
    assert saved['setup_mode']=='manual'
    assert saved['binding_profiles']['broken.csv']['error']=='CSV row 2 does not match its headers.'
    assert saved['error']=='Add a usable CSV before manual setup.'
    assert c.get(url+'/inputs').json()['files']==files
    assert not jobs and not saved.get('preflight_confirmation')

@pytest.mark.parametrize('reviewer,origin',[(None,'unrecorded'),('human','human_preflight_review'),('automated','agent_developer_review')])
def test_binding_reviewer_is_explicit_and_cannot_be_relabelled(setup,reviewer,origin):
    c,_=setup;url='/api/investigations/'+create(c)
    assert c.post(url+'/manual-plan',headers=HEADERS).status_code==200
    binding=c.post(url+'/binding-preview',json={'arguments':ARGS},headers=HEADERS).json()
    body={'arguments':ARGS,'binding_hash':binding['binding_hash'],'confirm':True}
    if reviewer is not None:body['reviewer']=reviewer
    r=c.post(url+'/accept-binding',json=body,headers=HEADERS)
    assert r.status_code==200,r.text
    recorded=r.json()['preflight_confirmation']
    assert recorded['origin']==origin
    assert recorded['reviewer_identity_verified'] is False
    assert c.post(url+'/accept-binding',json=body,headers=HEADERS).status_code==200
    body['reviewer']='automated' if reviewer=='human' else 'human'
    assert c.post(url+'/accept-binding',json=body,headers=HEADERS).status_code==409
    assert c.get(url).json()['preflight_confirmation']==recorded
