"""Exactly twelve known-case attempts; no retries and no relabelled acceptance."""
import concurrent.futures,json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'evaluation/probe-pilot'))
from common import credentials
from budget import Budget
from app.probes import investigate,SYSTEM,TOOLS
from app.primitive_runtime import PrimitiveSandbox,implementation_hash
from app.primitives import digest
from app.probe_evidence import bundle
DATA=ROOT/'.data/primitive-v3';MODEL='nvidia/nemotron-3-super-120b-a12b'
CASES={'checkpoint-control':('checkpoint_selection','clear'),'checkpoint-planted-source':('checkpoint_selection','violation'),'checkpoint-planted-source-twin':('checkpoint_selection','clear'),'entity-control':('entity_overlap','clear_pending_confirmation'),'entity-source':('entity_overlap','violation'),'entity-source-twin':('entity_overlap','clear_pending_confirmation')}
def main():
 gate_a=json.loads((DATA/'gate-a.json').read_text())
 env=json.loads((DATA/'environment.json').read_text())
 if gate_a['status']!='pass' or gate_a['implementation_hash']!=implementation_hash() or env['implementation_hash']!=implementation_hash():raise SystemExit('Gate A or image does not match passing current implementation')
 destination=DATA/'gate-b'
 destination.mkdir(exist_ok=False)
 key,project=credentials()
 ledger_path=ROOT/'.data/probe-pilot/budget.json'
 if not ledger_path.exists():raise SystemExit('Existing cumulative ledger required; never reset prior spend')
 if json.loads(ledger_path.read_text())['limit_usd']>10:raise SystemExit('Authorized cap is $10')
 ledger=Budget(ledger_path,{MODEL:(.30,.90)})
 import fcntl
 with (ROOT/'.data/probe-pilot/batch.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  snapshot={'frozen_at':datetime.now(timezone.utc).isoformat(),'implementation_hash':implementation_hash(),'image':env['image'],'prompt':SYSTEM,'tools':TOOLS,'files':{str(p.relative_to(ROOT)):__import__('hashlib').sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'app').glob('*.py'))},'cases':CASES,'kind':'Gate B known cases, not unseen acceptance'}
  (destination/'snapshot.json').write_text(json.dumps(snapshot,indent=2))
  def run(job):
   name,trial=job;category,expected=CASES[name];out=destination/f'{name}-trial{trial}';out.mkdir()
   old=ROOT/'.data/primitive-v2/regression/regression-01/runs'/f'{name}-trial1'
   previous=json.loads((old/'evidence/result.json').read_text())
   files={str(p.relative_to(old/'inputs')):p.read_text() for p in (old/'inputs').rglob('*') if p.is_file()}
   (out/'attempt.json').write_text(json.dumps({'case':name,'trial':trial,'started_at':datetime.now(timezone.utc).isoformat(),'freeze_hash':digest(snapshot),'input_hashes':{n:__import__('hashlib').sha256(v.encode()).hexdigest() for n,v in files.items()}},indent=2))
   def event(e):
    with (out/'events.jsonl').open('a') as f:f.write(json.dumps(e)+'\n')
   try:
    r=investigate(previous['claim'],files,key,MODEL,PrimitiveSandbox(key,project,env['image']),budget=ledger,category=category,on_event=event)
    bundle(r,files,out/'evidence')
    verdict=(r.get('verdict') or {}).get('verdict');replay=bool(r['primitive_replays']) and all(x['matches'] for x in r['primitive_replays'])
    corrections=sum(isinstance(e.get('result'),dict) and 'error' in e['result'] for e in r['events'])
    row={'case':name,'trial':trial,'expected':expected,'verdict':verdict,'passed':r['status']=='completed' and verdict==expected and replay,'replay_matches':replay,'corrections':corrections,'estimated_usd':(r['tokens']['prompt']*.30+r['tokens']['completion']*.90)/1e6,'tokens':r['tokens']}
   except Exception as exc:
    row={'case':name,'trial':trial,'expected':expected,'passed':False,'error':type(exc).__name__}
   (out/'completion.json').write_text(json.dumps(row,indent=2));print(json.dumps(row),flush=True);return row
  jobs=[(name,trial) for name in CASES for trial in (1,2)]
  with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(run,jobs))
  import statistics
  median=statistics.median([r.get('corrections',15) for r in rows])
  report={'status':'pass' if all(r['passed'] for r in rows) and median<=1 else 'fail','implementation_hash':implementation_hash(),'freeze_hash':digest(snapshot),'kind':'known-case Gate B, not unseen acceptance','completed_at':datetime.now(timezone.utc).isoformat(),'rows':rows,'median_tool_corrections':median,'human_review':'unmeasured','estimated_usd':sum(r.get('estimated_usd',0) for r in rows)}
  (DATA/'gate-b.json').write_text(json.dumps(report,indent=2))
  print(json.dumps({k:v for k,v in report.items() if k!='rows'}),flush=True)
if __name__=='__main__':main()
