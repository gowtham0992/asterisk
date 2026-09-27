import copy,io,json,zipfile
import pytest
from app.repair import propose,inventory_zip
from app.audit import table,execute
from tests.test_primitives import FILES,ARGS
from tests.test_researcher_handoff import investigation
from tests.test_investigations import setup,create
from tests.test_api import HEADERS,client
from app import main
from fastapi.testclient import TestClient

DATA={**FILES,'split.csv':'image,part\na,train\nb,test\nc,test\nd,test\ne,train\n','map.csv':'subject_id,image\nu,a\nu,b\nu,c\nv,d\nw,e\n'}

def parent():
    a=investigation(DATA);a['id']='a'*24;return a

@pytest.mark.parametrize('policy,target,moves',[('evaluation_to_training','train',2),('training_to_evaluation','test',1)])
def test_repair_changes_only_required_partition_values(policy,target,moves):
    a=parent();original=copy.deepcopy(a);p,files=propose(a,policy,target)
    assert a==original and len(p['moves'])==moves
    assert p['after']['shared_entities']==0 and p['after']['train_rows'] and p['after']['test_rows']
    assert files['map.csv']==DATA['map.csv']
    before={r['image']:r for r in table(DATA['split.csv'])[1]};after={r['image']:r for r in table(files['split.csv'])[1]}
    assert before.keys()==after.keys()
    assert {s for s in before if before[s]!=after[s]}=={r['sample'] for r in p['moves']}
    assert propose(a,policy,target)[0]['proposal_hash']==p['proposal_hash']

def test_repair_refuses_missing_mappings_empty_partition_and_stale_inputs():
    with pytest.raises(ValueError,match='Complete identity'):
        propose(investigation({**DATA,'map.csv':DATA['map.csv'].replace('v,d\n','')}),'evaluation_to_training','train')
    with pytest.raises(ValueError,match='at least one'):
        propose(investigation(FILES),'evaluation_to_training','train')
    a=parent();a['input']['files'][0]['content']+='tamper'
    with pytest.raises(ValueError,match='do not match'):propose(a,'evaluation_to_training','train')

def test_export_contains_all_missing_rows_and_both_sides():
    data={**DATA,'map.csv':DATA['map.csv'].replace('v,d\n','')};a=investigation(data)
    with zipfile.ZipFile(io.BytesIO(inventory_zip(a))) as z:
        r=json.loads(z.read('rows.json'));assert len(r['affected'])==3
        assert {x['role'] for x in r['affected']}=={'training','evaluation'}
        assert r['unmapped'][0]['sample']=='d' and r['unmapped'][0]['split_row']==5

def test_approval_is_owner_scoped_hash_checked_idempotent_and_unconfirmed(setup):
    c,jobs=setup;id=create(c,{'title':'Repair test','claim':'Evaluation specimens must be absent from training.','files':[{'name':n,'content':t} for n,t in DATA.items()],'model':'super'})
    with main.connect() as db:
        a=json.loads(db.execute('select payload from investigations where id=?',(id,)).fetchone()['payload']);a.update(result=parent()['result'],state='complete');db.execute('update investigations set payload=? where id=?',(json.dumps(a),id))
    url='/api/investigations/'+id;body={'policy':'evaluation_to_training','target_label':'train'}
    preview=c.post(url+'/repair-preview',json=body,headers=HEADERS);assert preview.status_code==200,preview.text
    with TestClient(main.app) as other:
        other.get('/api/session');assert other.get(url+'/repair-files').status_code==404
        assert other.post(url+'/repair-preview',json=body,headers=HEADERS).status_code==404
    assert c.post(url+'/repair-approve',json=body,headers=HEADERS).status_code==422
    assert c.post(url+'/repair-approve',json={**body,'confirm':True,'proposal_hash':'0'*64},headers=HEADERS).status_code==409
    body.update(confirm=True,proposal_hash=preview.json()['proposal_hash'])
    r=c.post(url+'/repair-approve',json=body,headers=HEADERS);assert r.status_code==201,r.text
    assert r.json()['state']=='review' and not r.json().get('preflight_confirmation') and not r.json().get('result')
    assert c.post(url+'/repair-approve',json=body,headers=HEADERS).json()['id']==r.json()['id']
    retained=c.get('/api/investigations/'+r.json()['id']+'/repair-proposal').json()
    assert len(retained['proposal']['moves'])==2 and retained['approval']['confirmed_at']
    assert retained['approval']['proposal_hash']==body['proposal_hash']
    assert not jobs

def test_notebook_export_local_cli_and_saved_binding(tmp_path,setup):
    from asterisk import export_split,check,load_config
    cfg=export_split(tmp_path/'data',sample_ids=['001','002','003'],entity_ids=['A','A','B'],partitions=['train','test','test'],claim='Evaluation identities must be absent from training.',identity_definition='entity identifies the physical specimen.')
    report=check(cfg,tmp_path/'report');assert report['verdict']=='violation'
    r=json.loads((tmp_path/'report/result.json').read_text());assert not r['primitive_replays'] and not r.get('binding_confirmation')
    assert '001' in (tmp_path/'data/splits.csv').read_text()
    config,args,files=load_config(cfg);c,_=setup
    id=create(c,{'title':'Imported','claim':config['claim'],'files':[{'name':n,'content':t} for n,t in files.items()],'saved_binding':args})
    r=c.post('/api/investigations/'+id+'/manual-plan',headers=HEADERS);assert r.json()['plan']['binding']==args and not r.json().get('preflight_confirmation')
    assert c.get('/api/investigations/'+id+'/configuration').json()['arguments']==args
    config['files']=['../outside.csv'];cfg.write_text(json.dumps(config))
    with pytest.raises(ValueError,match='unsafe'):load_config(cfg)

def test_full_metadata_limit_and_cell_bound():
    assert len(table('sample,partition\n'+''.join(f'{i},train\n' for i in range(25000)))[1])==25000
    with pytest.raises(ValueError,match='100,000'):table('a\n'+'x\n'*100001)


def test_cli_repeat_compares_exact_inputs_and_refuses_tampered_parent(tmp_path):
    from asterisk import export_split,check
    claim='Evaluation identities must be absent from training.'
    first=export_split(tmp_path/'first',sample_ids=['a','b','c'],entity_ids=['u','u','v'],partitions=['train','test','test'],claim=claim,identity_definition='entity is the specimen.')
    second=export_split(tmp_path/'second',sample_ids=['a','b','c'],entity_ids=['u','u','v'],partitions=['train','train','test'],claim=claim,identity_definition='entity is the specimen.')
    check(first,tmp_path/'before');check(second,tmp_path/'after',tmp_path/'before')
    r=json.loads((tmp_path/'after/result.json').read_text())
    assert r['revision_comparison']['identity_membership_comparable'] and r['revision_comparison']['resolved_identities']==['u']
    assert (tmp_path/'after/comparison.json').exists()
    (tmp_path/'before/inputs/splits.csv').write_text('tamper')
    check(second,tmp_path/'tampered',tmp_path/'before')
    r=json.loads((tmp_path/'tampered/result.json').read_text())
    assert not r['revision_comparison']['available']

def test_cli_preserves_crlf_inputs_and_can_compare_them(tmp_path):
    from asterisk import export_split,check
    cfg=export_split(tmp_path/'source',sample_ids=['a','b','c'],entity_ids=['u','u','v'],partitions=['train','test','test'],claim='Evaluation specimens must be absent from training.',identity_definition='entity identifies the physical specimen.')
    for name in ('splits.csv','identities.csv','identity.md'):
        path=cfg.parent/name
        path.write_bytes(path.read_bytes().replace(b'\n',b'\r\n'))
    check(cfg,tmp_path/'first')
    for name in ('splits.csv','identities.csv','identity.md'):
        assert (tmp_path/'first/inputs'/name).read_bytes()==(cfg.parent/name).read_bytes()
    check(cfg,tmp_path/'second',tmp_path/'first')
    result=json.loads((tmp_path/'second/result.json').read_text())
    assert result['revision_comparison']['available']
    assert result['revision_comparison']['changed_files']==[]

@pytest.mark.parametrize('policy,target,side,counts',[
    ('evaluation_to_training','train','evaluation','3 training rows; 0 evaluation rows'),
    ('training_to_evaluation','test','training','0 training rows; 3 evaluation rows'),
])
def test_empty_repair_names_lost_partition_and_preserves_parent(policy,target,side,counts):
    a=investigation(FILES);before=copy.deepcopy(a)
    with pytest.raises(ValueError) as failure:propose(a,policy,target)
    message=str(failure.value)
    assert f'leave {side} empty' in message and counts in message
    assert 'No revision was created' in message
    assert 'each recorded identity stays entirely on one side' in message
    assert 'does not establish a suitable experiment' in message
    assert a==before
