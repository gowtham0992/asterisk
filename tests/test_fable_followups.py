import copy,json
import pytest
from app.receipt import preview
from app.primitives import measure,gate
from app.receipt_view import render_receipt
from tests.test_primitives import FILES,ARGS
from tests.test_repair_workflow import DATA
from tests.test_researcher_handoff import investigation
from app.repair import propose

@pytest.mark.parametrize('left,right',[('P1','p1'),('José','Jose\u0301'),('P1','P1 '),('Ａ','A')])
def test_identity_warning_does_not_normalize_or_grant_a_verdict(left,right):
    files={**FILES,'split.csv':'image,part\na,train\nb,test\n','map.csv':f'subject_id,image\n{left},a\n{right},b\n'}
    original=copy.deepcopy(files);p=preview('Unseen specimens',files,ARGS)
    d=p['identity_diagnostics'];assert d['identity_count']==2 and d['collision_groups']==1
    m=measure('entity_overlap',files,ARGS);assert m['output']['shared_entities']==0
    assert gate('entity_overlap',[m],[])['verdict']=='clear_pending_confirmation'
    assert files==original
    result={'claim':'Unseen specimens','input_hashes':p['input_hashes'],'primitive_measurements':{'m':m},'verdict':{'verdict':'clear_pending_confirmation'}}
    assert 'Review similar-looking identity values' in render_receipt(result,files)
    assert 'Review similar-looking identity values' not in render_receipt(result,{**files,'map.csv':'tampered'})


def test_warning_excludes_surplus_mapping_and_repeated_exact_values():
    files={**FILES,'split.csv':'image,part\na,train\nb,test\n','map.csv':'subject_id,image\nP1,a\nP1,b\np1,unused\n'}
    assert preview('claim',files,ARGS)['identity_diagnostics']['identity_count']==0


def test_repair_preserves_crlf_and_discloses_quoting_normalization():
    files={**DATA,'split.csv':DATA['split.csv'].replace('\n','\r\n')}
    p,revised=propose(investigation(files),'evaluation_to_training','train')
    assert p['csv_format']['line_ending']=='CRLF'
    assert '\n' not in revised['split.csv'].replace('\r\n','')
    assert 'quoting is normalized' in p['scope'] and p['after']['shared_entities']==0

@pytest.mark.parametrize('right',['P\u200b1','P\u200d1','P\ufeff1','P\u00ad1','P\u04301'])
def test_invisible_and_mixed_script_warnings_do_not_change_exact_measurement(right):
    files={**FILES,'split.csv':'image,part\na,train\nb,test\n','map.csv':f'subject_id,image\nP1,a\n{right},b\n'}
    assert preview('claim',files,ARGS)['identity_diagnostics']['identity_count']>0
    assert measure('entity_overlap',files,ARGS)['output']['shared_entities']==0
