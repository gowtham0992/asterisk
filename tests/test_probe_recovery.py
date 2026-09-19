"""Recovery must construct reports from trusted records, never from model numbers."""
import json
import pytest
from types import SimpleNamespace
from app.probes import Investigation,investigate
from app.primitives import VERSION
from tests.test_primitives import FILES,ARGS,CITE,Trusted

def test_minimal_submission_uses_complete_harness_envelope():
    i=Investigation(FILES,Trusted(),category='entity_overlap');i.dispatch('entity_overlap',ARGS)
    i.dispatch('submit_verdict',{'citations':[CITE]})
    assert i.verdict['verdict']=='violation'
    assert i.verdict['measurement_ids']==['measurement-1']
    assert i.verdict['measurements']['measurement-1']['shared_entities']==1

def test_evidence_state_does_not_use_exploration_as_evidence():
    i=Investigation(FILES,Trusted(),category='entity_overlap');i.dispatch('write_probe',{'code':'print(1)'});i.dispatch('run_probe',{'probe_id':'probe-1'})
    assert i.evidence_state()['measurement_ids']==[]
    assert i.finalize() is None

def test_harness_finalization_includes_contradictory_retained_records():
    i=Investigation(FILES,Trusted(),category='entity_overlap');i.dispatch('entity_overlap',ARGS)
    i.dispatch('entity_overlap',{**ARGS,'entity_column':'absent'})
    v=i.finalize()
    assert v['verdict']=='violation' and len(v['measurement_ids'])==2
    assert v['report_origin']=='harness'

def test_wrong_explicit_verdict_still_rejected():
    i=Investigation(FILES,Trusted(),category='entity_overlap');i.dispatch('entity_overlap',ARGS)
    with pytest.raises(ValueError,match='permits violation'):
        i.dispatch('submit_verdict',{'citations':[CITE],'verdict':'clear'})

def test_dynamic_trace_cites_actual_fit_and_split_lines():
    files={'entry.py':'import numpy as np\nX = data\nfor a,b in cv.split(X):\n    scaler.fit(X[a])\n'}
    i=Investigation(files,Trusted(),category='preprocessing')
    i.measurements={'measurement-1':{'primitive':'fit_trace','version':VERSION,'arguments':{'entry_file':'entry.py'},'output':{
        'available':True,'executed_file':'entry.py','complete':True,
        'events':[{'line':4,'exact_train':True,'includes_test':False}], 'folds':[{'line':3}]}}}
    v=i.finalize()
    assert v['verdict']=='clear'
    assert [c['start_line'] for c in v['citations']]==[4,3]
    assert v['citations'][0]['quote']=='    scaler.fit(X[a])'

def fake_provider(monkeypatch):
    import app.probes as mod
    calls=[]
    class ToolCall:
        id='tool'
        def __init__(self,name,args):self.function=SimpleNamespace(name=name,arguments=json.dumps(args))
        def model_dump(self):return {'id':self.id,'type':'function','function':vars(self.function)}
    class Client:
        def __init__(self,**kwargs):self.chat=SimpleNamespace(completions=SimpleNamespace(create=self.create))
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def create(self,**kwargs):
            calls.append(kwargs)
            # Valid measurement, then an uncooperative model reading until cutoff.
            tc=ToolCall('entity_overlap',ARGS) if len(calls)==1 else ToolCall('read_file',{'path':'README.md','start':1,'count':1})
            return SimpleNamespace(usage=SimpleNamespace(prompt_tokens=10,completion_tokens=10),choices=[SimpleNamespace(message=SimpleNamespace(content=None,tool_calls=[tc]))])
    monkeypatch.setattr(mod,'OpenAI',Client)
    return calls

def test_call_budget_finalization_uses_replayed_measurements(monkeypatch):
    fake_provider(monkeypatch)
    r=investigate('Are specimens independent?',FILES,'test-key','stub',Trusted(),category='entity_overlap')
    assert r['status']=='completed' and r['verdict']['verdict']=='violation'
    assert r['tool_calls']<=15 and r['verdict']['report_origin']=='harness'
    assert r['loop_exit_reason']=='budget_exhausted'
    assert all(p['matches'] for p in r['primitive_replays'])
