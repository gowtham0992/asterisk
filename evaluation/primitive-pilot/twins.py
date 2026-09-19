"""Development twin sensitivity, NOT the twelve unseen acceptance cases."""
import concurrent.futures,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'evaluation/probe-pilot'))
from common import credentials
from app.primitive_runtime import PrimitiveSandbox,implementation_hash
from app.primitives import gate,citation
from tests.test_primitives import FILES,ARGS,BASE,CHAIN,chain_args,CITE
key,project=credentials();image=json.loads((ROOT/'.data/primitive-pilot/environment.json').read_text())['image']
pipeline='''from sklearn.datasets import make_regression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import Ridge
from sklearn.model_selection import cross_validate,KFold
X,y=make_regression(n_samples=30,n_features=3,random_state=19)
model=make_pipeline(StandardScaler(),Ridge())
result=cross_validate(model,X,y,cv=KFold(n_splits=3,shuffle=True,random_state=4),n_jobs=1)
'''
clean_chain=CHAIN.replace('test_labels = test_pack[1]','valid_labels = valid_pack[1]').replace('score = model.evaluate(test_pack[0], test_labels)','score = model.evaluate(valid_pack[0], valid_labels)')
pairs=[
 ('entity-reordered','entity_overlap','entity_overlap',FILES,{**FILES,'map.csv':'image,subject_id\nb,v\nc,w\na,u\n'},ARGS,ARGS),
 ('entity-test-first','entity_overlap','entity_overlap',{**FILES,'split.csv':'image,part\nb,test\nc,test\na,train\n'},{**FILES,'split.csv':'image,part\nb,test\nc,test\na,train\n','map.csv':'subject_id,image\nv,b\nv,c\nu,a\n'},ARGS,ARGS),
 ('fit-loop','preprocessing','fit_trace',{'entry.py':BASE.replace('scaler.fit(left)','scaler.fit(np.vstack([left,right]))')},{'entry.py':BASE},{'entry_file':'entry.py','class_names':['StandardScaler']},{'entry_file':'entry.py','class_names':['StandardScaler']}),
 ('fit-pipeline','preprocessing','fit_trace',{'entry.py':pipeline.replace('model=','X=StandardScaler().fit_transform(X)\nmodel=')},{'entry.py':pipeline},{'entry_file':'entry.py','class_names':['StandardScaler']},{'entry_file':'entry.py','class_names':['StandardScaler']}),
 ('checkpoint','checkpoint_selection','symbol_chain',{'entry.py':CHAIN},{'entry.py':clean_chain},chain_args(),chain_args('validation')),
 ('checkpoint-renamed','checkpoint_selection','symbol_chain',{'entry.py':CHAIN.replace('model','estimator').replace('score','metric')},{'entry.py':clean_chain.replace('model','estimator').replace('score','metric')},json.loads(json.dumps(chain_args()).replace('model','estimator').replace('score','metric')),json.loads(json.dumps(chain_args('validation')).replace('model','estimator').replace('score','metric')))
]
# Rename symbol values without changing the API property model_symbol.
for index in (5,):
 p=list(pairs[index])
 for pos in (5,6):p[pos]['model_symbol']=p[pos].pop('estimator_symbol')
 pairs[index]=tuple(p)
def run(pair):
 name,category,kind,bad,good,bargs,gargs=pair;records=[]
 for files,args in ((bad,bargs),(good,gargs)):
  runner=PrimitiveSandbox(key,project,image);r=runner.primitive(kind,args,files);again=runner.primitive(kind,args,files)
  match=not r.get('execution_error') and not again.get('execution_error') and all(r.get(k)==again.get(k) for k in ('primitive','version','arguments','input_hashes','implementation_hash','output'))
  cs=[citation(files,CITE)] if category=='entity_overlap' else []
  records.append({'record':r,'gate':gate(category,[r],cs),'replay_matches':match})
 # Provenance hashes must not make an unchanged measurement appear sensitive.
 def semantic(r):return {k:v for k,v in r['record']['output'].items() if k not in ('source_sha256','hashes','input_hashes')}
 passed=records[0]['gate']['verdict']=='violation' and records[1]['gate']['verdict']=='clear' and semantic(records[0])!=semantic(records[1]) and all(r['replay_matches'] for r in records)
 out={'name':name,'passed':passed,'runs':records};print(json.dumps({'pair':name,'passed':passed,'verdicts':[r['gate']['verdict'] for r in records]}),flush=True);return out
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(run,pairs))
report={'kind':'development twins, not unseen acceptance','implementation_hash':implementation_hash(),'image':image,'passed':all(r['passed'] for r in results),'pairs':results}
(ROOT/'.data/primitive-pilot/twins.json').write_text(json.dumps(report,indent=2));raise SystemExit(0 if report['passed'] else 1)
