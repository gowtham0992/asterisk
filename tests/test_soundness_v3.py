import importlib.util
from pathlib import Path
import pytest
from app.primitives import measure,gate,citation
from app.bindings import pending_binding,confirm_binding
from tests.test_primitives import FILES,ARGS,Trusted

spec=importlib.util.spec_from_file_location('gate_a_cases',Path(__file__).parents[1]/'evaluation/primitive-v3/cases.py')
cases=importlib.util.module_from_spec(spec);spec.loader.exec_module(cases)
@pytest.mark.parametrize('name,bad,good',cases.trace_pairs())
def test_transformer_and_partition_pairs(name,bad,good):
    pytest.importorskip('sklearn')
    for source,expected in ((bad,'violation'),(good,'clear')):
        r=measure('fit_trace',{'entry.py':source},{'entry_file':'entry.py','class_names':[]})
        assert gate('preprocessing',[r],[])['verdict']==expected,r
        if expected=='clear':assert all(e['partition_ids'] for e in r['output']['events'])

def pending_result():
    files={**FILES,'map.csv':'image,subject_id\na,u\nb,v\nc,w\n','README.md':'subject_id is NOT the patient identity.'}
    r=measure('entity_overlap',files,ARGS);d=gate('entity_overlap',[r],[citation(files,{'file':'README.md','start_line':1,'end_line':1})])
    return files,{'claim':'Patients must be absent from training.','primitive_measurements':{'measurement-1':r},'verdict':{'category':'entity_overlap','verdict':d['verdict'],'gate':d,'citations':[],'missing_evidence':d['missing']}}

def test_denying_documentation_never_confirms_clear():
    files,result=pending_result()
    assert result['verdict']['verdict']=='clear_pending_confirmation'
    from app.probes import Investigation
    inv=Investigation(files,Trusted(),'entity_overlap','Patients must be absent from training.')
    inv.dispatch('entity_overlap',ARGS)
    assert inv.finalize()['verdict']=='clear_pending_confirmation'
    with pytest.raises(ValueError):inv.dispatch('submit_verdict',{'verdict':'clear','citations':[{'file':'README.md','start_line':1,'end_line':1}]})

def test_confirmation_binds_exact_claim_inputs_and_arguments():
    _,result=pending_result();b=pending_binding(result)
    with pytest.raises(ValueError):confirm_binding(result,'0'*64)
    confirmed=confirm_binding(result,b['binding_hash'])
    assert confirmed['verdict']['verdict']=='clear'
    assert result['verdict']['verdict']=='clear_pending_confirmation'
    assert confirmed['binding_confirmation']['origin']=='human_review'
    assert confirmed['verdict_before_confirmation']['verdict']=='clear_pending_confirmation'
    with pytest.raises(ValueError):confirm_binding(confirmed,b['binding_hash'])
    result['claim']='A different claim'
    with pytest.raises(ValueError):confirm_binding(result,b['binding_hash'])
