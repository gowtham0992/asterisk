import copy
import pytest
from app.receipt import preview, execute_receipt
from app.repair import propose
from app.receipt_comparison import compare_receipts
from tests.test_primitives import FILES, ARGS, Trusted
from tests.test_investigations import setup, create, PAYLOAD, PLAN
from tests.test_api import client, HEADERS
from tests.test_repair_workflow import parent

INTENT={'target':'unseen_entities','unit':'specimens'}

def test_purpose_changes_confirmation_and_legacy_remains_compatible():
    legacy=preview(PAYLOAD['claim'],FILES,ARGS)
    assert legacy==preview(PAYLOAD['claim'],FILES,ARGS,None)
    declared=preview(PAYLOAD['claim'],FILES,ARGS,INTENT)
    assert declared['binding_hash']!=legacy['binding_hash']
    assert 'specimens' in declared['text']
    confirmation={**declared,'confirmed':True,'confirmed_at':'2026-09-18'}
    with pytest.raises(ValueError,match='no longer matches'):
        execute_receipt(PAYLOAD['claim'],FILES,PLAN,confirmation,'test',Trusted(),evaluation_intent={**INTENT,'unit':'patients'})

@pytest.mark.parametrize('target',['future_observations','new_sites','other'])
def test_unsupported_intent_cannot_start_either_setup_path(setup,target):
    c,jobs=setup
    id=create(c,{**PAYLOAD,'evaluation_intent':{'target':target}})
    for route,body in [('propose',{'confirm_upload':True}),('manual-plan',None)]:
        r=c.post('/api/investigations/'+id+'/'+route,json=body,headers=HEADERS)
        assert r.status_code==422 and 'cannot establish' in r.text
    assert jobs==[]

@pytest.mark.parametrize('policy,label,removed,added,identities',[('evaluation_to_training','train',2,0,1),('training_to_evaluation','test',0,1,2)])
def test_repair_counts_population_without_claiming_improvement(policy,label,removed,added,identities):
    a=parent();a['input']['evaluation_intent']=INTENT
    p,_=propose(a,policy,label)
    assert p['evaluation_population']=={'evaluation_rows_retained':3-removed,'evaluation_rows_removed':removed,'evaluation_rows_added':added,'evaluation_identities_before':2,'evaluation_identities_after':identities}
    assert p['evaluation_intent']==INTENT and p['original_claim']==a['input']['claim']
    assert 'does not establish a better' in p['scientific_consequence']

def test_changed_purpose_is_not_a_like_for_like_repair():
    a=parent();b=copy.deepcopy(a);b['input']['evaluation_intent']=INTENT
    result=compare_receipts(a,b)
    assert not result['same_intent'] and not result['shared_identity_comparison_available']

def test_intent_survives_setup_configuration_and_confirmation(setup):
    c,_=setup;id=create(c,{**PAYLOAD,'evaluation_intent':INTENT});url='/api/investigations/'+id
    assert c.post(url+'/manual-plan',headers=HEADERS).status_code==200
    r=c.post(url+'/binding-preview',json={'arguments':ARGS},headers=HEADERS)
    assert r.status_code==200 and r.json()['evaluation_intent']==INTENT
    assert c.post(url+'/accept-binding',json={'arguments':ARGS,'binding_hash':r.json()['binding_hash'],'confirm':True},headers=HEADERS).status_code==200
    assert c.get(url+'/configuration').json()['evaluation_intent']==INTENT


def test_offline_receipt_retains_and_escapes_purpose():
    from app.receipt_view import render_receipt
    a=parent();a['result']['evaluation_intent']={**INTENT,'unit':'<script>patients</script>'}
    page=render_receipt(a['result'],{f['name']:f['content'] for f in a['input']['files']})
    assert '&lt;script&gt;patients&lt;/script&gt;' in page
    assert 'not independent semantic validation' in page
    assert '<script>patients</script>' not in page
