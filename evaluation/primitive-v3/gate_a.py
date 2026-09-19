"""Ten adversarial development pairs; every measurement is replayed remotely."""
import concurrent.futures,json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'evaluation/probe-pilot'))
from cases import trace_pairs
from common import credentials
from app.primitive_runtime import PrimitiveSandbox,implementation_hash
from app.primitives import gate,citation
DATA=ROOT/'.data/primitive-v3'
def build_pairs():
 pairs=[]
 for name,bad,good in trace_pairs():
  pairs.append((name,'preprocessing',[( 'fit_trace',{'entry.py':s},{'entry_file':'entry.py','class_names':[]},expected) for s,expected in [(bad,'violation'),(good,'clear')]]))
 files={'split.csv':'sample,partition\na,train\nb,test\n','identity.csv':'sample,origin\na,A\nb,B\n'}
 args={'split_file':'split.csv','sample_column':'sample','partition_column':'partition','train_values':['train'],'test_values':['test'],'mapping_file':'identity.csv','mapping_sample_column':'sample','entity_column':'origin'}
 pairs.append(('entity-binding','entity_overlap',[('entity_overlap',{**files,'README.md':text},args,'clear_pending_confirmation') for text in ['origin is the scanner device id, NOT the patient identity. No patient mapping is supplied.','origin is the generating patient identity.']]))
 path=ROOT/'.data/primitive-v2/regression/regression-01/runs/checkpoint-control-trial1/inputs'
 files={str(p.relative_to(path)):p.read_text() for p in path.rglob('*') if p.is_file()}
 pairs.append(('checkpoint-candidates','checkpoint_selection',[('symbol_chain',files,{'file':'main.py','test_symbol':symbol,'validation_symbol':'val_loader','model_symbol':'model','selection_role':'auto'},expected) for symbol,expected in [('df','insufficient'),('test_loader','clear')]]))
 return pairs

def main():
 key,project=credentials();env=json.loads((DATA/'environment.json').read_text())
 if env['implementation_hash']!=implementation_hash():raise SystemExit('Stale image')
 if (DATA/'gate-a.json').exists():raise SystemExit('Gate A already recorded; preserve it. No silent rerun.')
 def run(pair):
  name,category,variants=pair;rows=[]
  for kind,files,args,expected in variants:
   runner=PrimitiveSandbox(key,project,env['image']);r=runner.primitive(kind,args,files);again=runner.primitive(kind,args,files)
   match=not r.get('execution_error') and not again.get('execution_error') and all(r.get(k)==again.get(k) for k in ('primitive','version','arguments','input_hashes','implementation_hash','output'))
   citations=[citation(files,{'file':'README.md','start_line':1,'end_line':1})] if 'README.md' in files else []
   d=gate(category,[r],citations)
   extra=True
   if name=='checkpoint-candidates' and expected=='insufficient':extra={'test_loader','val_loader'}<={x['symbol'] for x in r['output'].get('structural_candidates',[])}
   rows.append({'record':r,'replay':again,'replay_matches':match,'gate':d,'expected':expected,'passed':match and d['verdict']==expected and extra})
  result={'name':name,'passed':all(r['passed'] for r in rows),'runs':rows}
  print(json.dumps({'pair':name,'passed':result['passed'],'verdicts':[r['gate']['verdict'] for r in rows]}),flush=True)
  return result
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,build_pairs()))
 report={'status':'pass' if all(r['passed'] for r in rows) else 'fail','kind':'adversarial development, not unseen acceptance','implementation_hash':implementation_hash(),'image':env['image'],'completed_at':datetime.now(timezone.utc).isoformat(),'pairs':rows,'inference_spend':0,'human_review':'unmeasured','entity_pair_contract':'Both documentation variants remain pending. Documentation cannot confirm a human binding. The confirmation transition is tested separately as a simulated API action.'}
 with (DATA/'gate-a.json').open('x') as f:json.dump(report,f,indent=2)
 raise SystemExit(0 if report['status']=='pass' else 1)
if __name__=='__main__':main()
