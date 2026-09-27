import json
import pytest
from app.receipt import preview,execute_receipt
from app.probes import Investigation
from tests.test_primitives import FILES,ARGS,CITE,Trusted

def confirmation(files=FILES,args=ARGS):
    return {**preview('Specimens must be absent from training.',files,args),'confirmed':True,'origin':'human_preflight_review','confirmed_at':'2026-09-18T00:00:00+00:00'}

def test_wrong_binding_reports_actual_column_and_cardinality():
    with pytest.raises(ValueError,match=r'split.csv.part has 2 distinct values across 3 rows'):
        preview('Specimens must be absent from training.',FILES,{**ARGS,'sample_column':'part'})

def test_other_nonunique_sample_column_is_rejected():
    files={**FILES,'split.csv':'image,part,device\na,train,Q\nb,test,Q\nc,test,R\n'}
    with pytest.raises(ValueError,match=r'device has 2 distinct'):
        preview('Specimens must be absent from training.',files,{**ARGS,'sample_column':'device'})

def test_harness_does_not_repeat_model_missing_evidence_claim():
    inv=Investigation(FILES,Trusted(),'entity_overlap','Specimens must be absent from training.')
    inv.dispatch('entity_overlap',{**ARGS,'sample_column':'part'})
    inv.dispatch('submit_verdict',{'citations':[CITE],'explanation':'image has duplicate values','missing_evidence':['unique image IDs']})
    assert 'image has duplicate' not in inv.verdict['explanation']
    assert 'unique image IDs' not in inv.verdict['missing_evidence']
    assert inv.verdict['unverified_interpretation']['explanation']=='image has duplicate values'

def test_receipt_runs_only_confirmed_binding_and_retains_preconfirmation():
    files={**FILES,'map.csv':'image,subject_id\na,u\nb,v\nc,w\n'}
    result=execute_receipt('Specimens must be absent from training.',files,{'citations':[CITE]},confirmation(files),'test',Trusted())
    assert result['verdict']['verdict']=='clear'
    assert result['verdict_before_confirmation']['verdict']=='clear_pending_confirmation'
    assert result['binding_confirmation']['origin']=='human_preflight_review'
    assert result['primitive_measurements']['measurement-1']['arguments']==ARGS

def test_tampered_inputs_cannot_reuse_confirmation():
    with pytest.raises(ValueError,match='no longer matches'):
        execute_receipt('Specimens must be absent from training.',{**FILES,'README.md':'Changed'}, {'citations':[CITE]},confirmation(),'test',Trusted())

def test_replay_mismatch_suppresses_definitive():
    class Changed(Trusted):
        calls=0
        def primitive(self,*args):
            self.calls+=1;r=super().primitive(*args)
            if self.calls==2:r['output']['shared_entities']=99
            return r
    r=execute_receipt('Specimens must be absent from training.',FILES,{'citations':[CITE]},confirmation(),'test',Changed())
    assert r['status']=='incomplete' and r['verdict'] is None


def test_agent_review_never_claims_human_validation_or_unlocks_clear():
    files={**FILES,'map.csv':'image,subject_id\na,u\nb,v\nc,w\n'}
    reviewed={**confirmation(files),'origin':'agent_developer_review'}
    result=execute_receipt('Specimens must be absent from training.',files,
                           {'citations':[CITE]},reviewed,'manual',Trusted())
    assert result['verdict']['verdict']=='clear_pending_confirmation'
    assert 'binding_confirmation' not in result
    assert result['preflight_confirmation']['origin']=='agent_developer_review'
    assert result['semantic_validation'].startswith('Non-human binding review')


def test_agent_review_retains_verified_overlap_without_claiming_human_review():
    reviewed={**confirmation(),'origin':'agent_developer_review'}
    result=execute_receipt('Specimens must be absent from training.',FILES,
                           {'citations':[CITE]},reviewed,'manual',Trusted())
    assert result['verdict']['verdict']=='violation'
    assert result['primitive_replays'][0]['matches'] is True
    assert result['semantic_validation'].startswith('Non-human binding review')


def test_missing_reviewer_cannot_default_to_human_clear():
    files={**FILES,'map.csv':'image,subject_id\na,u\nb,v\nc,w\n'}
    reviewed=confirmation(files)
    reviewed.pop('origin')
    result=execute_receipt('Specimens must be absent from training.',files,
                           {'citations':[CITE]},reviewed,'manual',Trusted())
    assert result['verdict']['verdict']=='clear_pending_confirmation'
    assert 'binding_confirmation' not in result
