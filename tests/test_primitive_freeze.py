"""Protocol mechanics use dummy metadata, not acceptance cases."""
import importlib.util,sys,copy
from pathlib import Path
import pytest
ROOT=Path(__file__).parents[1]
sys.path.insert(0,str(ROOT/'evaluation/primitive-pilot'))
spec=importlib.util.spec_from_file_location('primitive_runner',ROOT/'evaluation/primitive-pilot/run.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def manifest(tmp_path):
 frozen={'frozen_at':'2026-09-17T00:00:00+00:00'}
 (tmp_path/'readme.txt').write_text('protocol mechanics fixture only')
 cases=[]
 for category in ('entity_overlap','preprocessing','checkpoint_selection'):
  for i,label in enumerate(('violation','violation','clear','insufficient')):
   c={'id':category+str(i),'category':category,'author':'test','authored_at':'2026-09-18T00:00:00+00:00','source':{'family':('yang','drug_response','planted','planted')[i],'url':'test','revision':'test','license':'test','transformations':'test'},'directory':'.','input_hashes':{'readme.txt':m.sha('protocol mechanics fixture only')},'expected':{'verdict':label,'review_requires':['test obligation']}}
   if label=='violation':c['twin']={'directory':'.','input_hashes':c['input_hashes'],'expected':{'verdict':'clear','review_requires':['repair obligation']}}
   cases.append(c)
 return {'freeze_hash':m.sha(__import__('json').dumps(frozen,sort_keys=True)),'cases':cases},frozen

def test_case_protocol_rejects_pre_freeze_case_and_input_mutation(tmp_path):
 cases,frozen=manifest(tmp_path)
 assert len(m.validate(cases,frozen,tmp_path))==12
 old=copy.deepcopy(cases);old['cases'][0]['authored_at']='2026-09-16T00:00:00+00:00'
 with pytest.raises(ValueError,match='after'):m.validate(old,frozen,tmp_path)
 (tmp_path/'readme.txt').write_text('mutated')
 with pytest.raises(ValueError,match='changed'):m.validate(cases,frozen,tmp_path)

def test_twins_need_evidence_obligations(tmp_path):
 cases,frozen=manifest(tmp_path);cases['cases'][0]['twin']['expected']['review_requires']=[]
 with pytest.raises(ValueError,match='review requirements'):m.validate(cases,frozen,tmp_path)
