"""Mechanical protocol tests, not authored scientific acceptance cases."""
import importlib.util,json,sys
from pathlib import Path
from datetime import datetime,timedelta,timezone
import pytest
ROOT=Path(__file__).parents[1];sys.path.insert(0,str(ROOT/'evaluation/primitive-v3'))
import v3harness as h
import v3scoring as s

def manifest(tmp_path):
 for name,text in [('base','protocol-only'),('repair','protocol-twin')]:
  (tmp_path/name).mkdir();(tmp_path/name/'readme.txt').write_text(text)
 frozen={'frozen_at':(datetime.now(timezone.utc)-timedelta(days=2)).isoformat()};cases=[]
 for cat in h.CATEGORIES:
  clean='clear_pending_confirmation' if cat=='entity_overlap' else 'clear'
  for i,label in enumerate(['violation']*3+[clean]+['insufficient']*2):
   c={'id':cat+str(i),'category':cat,'claim':'mechanical fixture','author':'test','authored_at':(datetime.now(timezone.utc)-timedelta(days=1)).isoformat(),'source':{'family':'planted','url':'test','revision':'test','license':'test','transformations':'test','previously_used':False},'directory':'base','input_hashes':{'readme.txt':h.sha('protocol-only')},'expected':{'verdict':label,'review_requires':['inspect']}}
   if label=='violation':c['twin']={'directory':'repair','input_hashes':{'readme.txt':h.sha('protocol-twin')},'expected':{'verdict':clean,'review_requires':['inspect']}}
   cases.append(c)
 return {'freeze_hash':h.sha(h.canonical(frozen)),'authorship_constraint':'mechanical fixture, not independence evidence','cases':cases},frozen

def test_two_category_balance_and_postfreeze_contract(tmp_path):
 m,f=manifest(tmp_path);assert len(h.validate(m,f,tmp_path))==12
 m['cases'][0]['authored_at']=f['frozen_at']
 with pytest.raises(ValueError,match='after'):h.validate(m,f,tmp_path)

def test_missing_practitioner_cannot_pass_even_with_other_review():
 from tests.test_evaluation_v2 import rows,twins
 report=s.summarize(rows(human=True),twins(),{'unsupported_definitives':0,'corrections':[0]})
 assert report['status']=='unmeasured'
 assert report['metrics']['practitioner_comprehension']['status']=='unmeasured'

def test_freeze_snapshot_materializes_and_checks_all_bytes(tmp_path,monkeypatch):
 paths=['app/placeholder.py','evaluation/primitive-v3/protocol.md','evaluation/probe-pilot/common.py','evaluation/probe-pilot/budget.py']
 for name in paths:
  p=tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('fixture')
 monkeypatch.setattr(h,'runtime_state',lambda:{'implementation_hash':'fixture'})
 result=h.snapshot(tmp_path/'frozen',{'implementation_hash':'fixture','image':'fixture'},root=tmp_path)
 assert result['files']
 h.check(result,root=tmp_path)
 (tmp_path/paths[0]).write_text('changed')
 with pytest.raises(ValueError,match='changed'):h.check(result,root=tmp_path)
