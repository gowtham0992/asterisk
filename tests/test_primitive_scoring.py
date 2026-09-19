import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('primitive_scoring',Path(__file__).parents[1]/'evaluation/primitive-pilot/scoring.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def result():return {'verdict':{'verdict':'violation','gate':{'passed':True,'verdict':'violation'},'measurement_ids':['m']},'primitive_measurements':{'m':{'output':{'shared_entities':1}}},'primitive_replays':[{'measurement_id':'m','matches':True}]}
def test_correct_label_with_failed_gate_is_incorrect():
 r=result();r['verdict']['gate']['passed']=False
 assert not m.score(r,{'verdict':'violation'})['gated_correct']
def test_review_requirements_cannot_be_ignored():
 e={'verdict':'violation','metrics':{'shared_entities':1},'review_requires':['fit consumes evaluation rows']}
 assert m.score(result(),e)['review_status']=='unmeasured'
 assert not m.score(result(),e)['gated_correct']
 assert m.score(result(),e,{'requirements':{'fit consumes evaluation rows':True}})['gated_correct']
def test_missing_replay_is_not_success():
 r=result();r['primitive_replays']=[]
 assert not m.score(r,{'verdict':'violation'})['gated_correct']

def test_acceptance_is_unmeasured_without_cases_or_blind_review():
 assert m.summarize([],[])['status']=='unmeasured'
 rows=[]
 for trial in (1,2):
  for i in range(12):
   r=result();expected={'verdict':'violation'}
   rows.append({'trial':trial,'expected':expected,'result':r,'score':m.score(r,expected),'estimated_usd':.01})
 twins=[{'complete':True,'different':True,'false_clear':False,'replay_match':True} for _ in range(6)]
 report=m.summarize(rows,twins)
 assert report['metrics']['correct_each_trial']['status']=='pass'
 assert report['metrics']['blind_evidence_review']['status']=='unmeasured'
 assert report['status']=='unmeasured'
 assert m.summarize(rows,twins,{'unsupported_definitives':0,'corrections':[0]*24})['status']=='pass'
 twins[0]['different']=False
 assert m.summarize(rows,twins,{'unsupported_definitives':0,'corrections':[0]*24})['status']=='fail'
