import json
import pytest
from app.probes import Investigation,validate_files,ProbeSandbox
from app.probe_evidence import bundle

def runner(code,files):return {'exit_code':0,'truncated':False,'stdout':'{"count": 2}','output':{'count':2}}
def verdict():return {'verdict':'violation','scope':'entity split','explanation':'overlap','probe_id':'probe-1','measurements':{'count':2},'citations':[{'file':'data.txt','quote':'entity'}],'limitations':['Only recorded IDs'],'missing_evidence':[]}
def test_no_host_path_reads_or_traversal():
    for path in ('../.env','/etc/passwd','a/../../secret','a\\secret','a/./b'):
        with pytest.raises(ValueError):validate_files({path:'x'})
    i=Investigation({'data.txt':'entity'},runner)
    with pytest.raises(ValueError):i.dispatch('read_file',{'path':'../.env','start':1,'count':1})
def test_citations_and_measured_output_are_enforced():
    i=Investigation({'data.txt':'entity'},runner)
    i.dispatch('write_probe',{'code':'print(1)'})
    with pytest.raises(ValueError):i.dispatch('submit_verdict',verdict())
    i.dispatch('run_probe',{'probe_id':'probe-1'})
    bad=verdict();bad['measurements']={'count':3}
    with pytest.raises(ValueError):i.dispatch('submit_verdict',bad)
    bad=verdict();bad['citations']=[{'file':'data.txt','quote':'invented'}]
    with pytest.raises(ValueError):i.dispatch('submit_verdict',bad)
    with pytest.raises(ValueError,match='Only retained'):i.dispatch('submit_verdict',verdict())
def test_failed_and_truncated_outputs_cannot_support_verdict():
    for output in ({'error':'service failed'},{'exit_code':1,'output':None},{'exit_code':0,'truncated':True,'output':None}):
        i=Investigation({'data.txt':'entity'},lambda *_:output);i.dispatch('write_probe',{'code':'x'});i.dispatch('run_probe',{'probe_id':'probe-1'})
        with pytest.raises(ValueError):i.dispatch('submit_verdict',verdict())
def test_abstention_requires_missing_evidence():
    i=Investigation({'data.txt':'entity'},runner);i.dispatch('write_probe',{'code':'x'});i.dispatch('run_probe',{'probe_id':'probe-1'})
    v=verdict();v['verdict']='insufficient'
    with pytest.raises(ValueError):i.dispatch('submit_verdict',v)
    v['missing_evidence']=['patient mapping']
    with pytest.raises(ValueError,match='Only retained'):i.dispatch('submit_verdict',v)
def test_bundle_captures_inputs_code_and_results(tmp_path):
    r={'claim':'test claim','probes':{'probe-1':'print(1)'}}
    out=bundle(r,{'data.txt':'entity'},tmp_path/'bundle')
    manifest=json.loads((out/'manifest.json').read_text())
    assert 'inputs/data.txt' in manifest['files'] and 'probes/probe-1.py' in manifest['files']
    import subprocess,sys
    assert subprocess.run([sys.executable,str(out/'verify.py')],capture_output=True).returncode==0
    (out/'inputs/data.txt').write_text('changed')
    assert subprocess.run([sys.executable,str(out/'verify.py')],capture_output=True).returncode!=0

def test_legacy_freeform_submission_is_rejected_even_without_retyped_measurements():
    i=Investigation({'data.txt':'entity'},runner);i.dispatch('write_probe',{'code':'print(1)'});i.dispatch('run_probe',{'probe_id':'probe-1'})
    v=verdict();v.pop('measurements')
    with pytest.raises(ValueError,match='Only retained'):i.dispatch('submit_verdict',v)

@pytest.mark.parametrize('args',[[],None,'not an object',42])
def test_malformed_tool_arguments_are_repairable_errors(args):
    with pytest.raises(ValueError):Investigation({'data.txt':'entity'},runner).dispatch('submit_verdict',args)

def test_malformed_citation_does_not_crash_the_investigation():
    i=Investigation({'data.txt':'entity'},runner);v=verdict();v['citations']=['data.txt: entity']
    with pytest.raises(ValueError):i.dispatch('submit_verdict',v)

def test_invalid_python_rejected_before_remote_execution():
    i=Investigation({'data.txt':'entity'},runner)
    with pytest.raises(ValueError,match='syntax error'):
        i.dispatch('write_probe',{'code':'if \\"bad\\": pass'})
    assert not i.probes and not i.runs

def test_literal_quote_alone_no_longer_satisfies_citation_contract():
    from app.primitives import citation
    with pytest.raises(ValueError):citation({'data.txt':'entity\nidentifier'},{'file':'data.txt','quote':'entity\\nidentifier'})
