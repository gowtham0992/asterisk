"""Run separately with the exact scientific Sandbox package versions installed."""
import importlib.util
from pathlib import Path
import pytest
pytest.importorskip('sklearn')
from app.primitives import measure,gate
spec=importlib.util.spec_from_file_location('v3cases',Path(__file__).parents[1]/'evaluation/primitive-v3/cases.py')
cases=importlib.util.module_from_spec(spec);spec.loader.exec_module(cases)
@pytest.mark.parametrize('name,bad,good',cases.trace_pairs())
def test_adversarial_pair(name,bad,good):
 for text,expected in [(bad,'violation'),(good,'clear')]:
  r=measure('fit_trace',{'entry.py':text},{'entry_file':'entry.py','class_names':[]})
  assert gate('preprocessing',[r],[])['verdict']==expected,r

def test_unobserved_instance_of_observed_class_blocks_completeness():
 good=cases.trace_pairs()[0][2]+'unused=PCA(n_components=2)\n'
 r=measure('fit_trace',{'entry.py':good},{'entry_file':'entry.py','class_names':[]})
 assert not r['output']['complete']
 assert gate('preprocessing',[r],[])['verdict']=='insufficient'

def test_dictionary_learning_and_partial_fit_entrypoints():
 for expr,imports,method in [('DictionaryLearning(n_components=2,random_state=2)','from sklearn.decomposition import DictionaryLearning\n','fit_transform'),('StandardScaler()','','partial_fit')]:
  source=cases.PREFIX+imports+f't={expr}\nt.{method}(X,y)\nfor a,b in cv.split(X):\n    s=StandardScaler()\n    s.fit(X[a])\n'
  r=measure('fit_trace',{'entry.py':source},{'entry_file':'entry.py','class_names':[]})
  assert gate('preprocessing',[r],[])['verdict']=='violation',r
