"""Synthetic primitive twins, run only in isolated Nebius environments."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'evaluation/probe-pilot'))
from common import credentials
from app.primitive_runtime import PrimitiveSandbox
from app.primitives import gate
from tests.test_primitives import FILES,ARGS,BASE
key,project=credentials();image=json.loads((ROOT/'.data/primitive-pilot/environment.json').read_text())['image'];runner=PrimitiveSandbox(key,project,image)
CLEAN='''from sklearn.datasets import make_regression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold, cross_validate
X,y = make_regression(n_samples=30,n_features=3,random_state=19)
model = make_pipeline(StandardScaler(),Ridge())
result = cross_validate(model,X,y,cv=KFold(n_splits=3,shuffle=True,random_state=4),n_jobs=1)
'''
cases=[('entity','entity_overlap',FILES,ARGS),('loop-clean','fit_trace',{'entry.py':BASE},{'entry_file':'entry.py','class_names':['StandardScaler']}),('loop-leaky','fit_trace',{'entry.py':BASE.replace('scaler.fit(left)','scaler.fit(X)')},{'entry_file':'entry.py','class_names':['StandardScaler']}),('pipeline-clean','fit_trace',{'entry.py':CLEAN},{'entry_file':'entry.py','class_names':['StandardScaler']}),('pipeline-leaky','fit_trace',{'entry.py':CLEAN.replace('model =','X = StandardScaler().fit_transform(X)\nmodel =')},{'entry_file':'entry.py','class_names':['StandardScaler']})]
reports=[]
for name,kind,files,args in cases:
 r=runner.primitive(kind,args,files);reports.append({'name':name,'record':r,'gate':gate('entity_overlap' if kind=='entity_overlap' else 'preprocessing',[r],[])})
 print(json.dumps(reports[-1]),flush=True)
(ROOT/'.data/primitive-pilot/smoke.json').write_text(json.dumps(reports,indent=2))
