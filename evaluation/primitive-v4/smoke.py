"""One known-case v4 smoke. Never relabel as acceptance or human review."""
import json,sys,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'evaluation/probe-pilot'))
from common import credentials
from budget import Budget
from app.investigations import propose_plan,MODELS
from app.receipt import preview,execute_receipt
from app.primitive_runtime import PrimitiveSandbox
from app.probe_evidence import bundle
DATA=ROOT/'.data/primitive-v4';destination=DATA/'ptbxl-known-smoke';destination.mkdir(exist_ok=False)
source=ROOT/'.data/primitive-v3/authored-packet/acceptance-cases'
case=next(c for c in json.loads((source/'manifest.json').read_text())['cases'] if c['id']=='E1-ptbxl-random')
files={n:(source/case['directory']/n).read_text() for n in case['input_hashes']}
model=MODELS['super'];budget=Budget(ROOT/'.data/probe-pilot/budget.json',{model:(.3,.9)})
reservation=budget.reserve(model,90000,2500)
if not reservation:raise SystemExit('Existing spending cap reached')
key,project=credentials()
try:
 plan,usage=propose_plan(case['claim'],files,key,model)
 if usage.get('prompt_tokens') is None:raise ValueError('Usage unavailable')
 budget.settle(reservation,usage['prompt_tokens'],usage['completion_tokens'])
except Exception:
 budget.uncertain(reservation);raise
(destination/'proposal.json').write_text(json.dumps({'plan':plan,'usage':usage},indent=2))
checked=preview(case['claim'],files,plan['binding'])
# This exercises the post-confirmation path using an automated fixture. It is NOT
# a human confirmation, user study, independent evidence review or acceptance.
confirmation={**checked,'confirmed':True,'confirmed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'origin':'automated_development_fixture'}
image=json.loads((DATA/'environment.json').read_text())['image']
result=execute_receipt(case['claim'],files,plan,confirmation,model,PrimitiveSandbox(key,project,image))
result['evaluation_class']='known-case automated development smoke; not human reviewed'
bundle(result,files,destination/'evidence')
o=next(iter(result['primitive_measurements'].values()))['output']
summary={'case':case['id'],'verdict':result['verdict']['verdict'] if result['verdict'] else None,'shared_entities':o.get('shared_entities'),'affected_test_rows':o.get('affected_test_rows'),'replay_match':all(r['matches'] for r in result['primitive_replays']),'proposed_sample_column':plan['binding']['sample_column'],'human_review':'unmeasured','estimated_usd':(usage['prompt_tokens']*.3+usage['completion_tokens']*.9)/1e6}
(destination/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary))
if (summary['verdict'],summary['shared_entities'],summary['affected_test_rows'],summary['replay_match'])!=('violation',623,692,True):raise SystemExit('Known-case smoke failed; preserve without replacement')
