import json
import pytest
from app.primitives import measure,gate,citation
from app.probes import Investigation
FILES={'split.csv':'image,part\na,train\nb,test\nc,test\n','map.csv':'subject_id,image\nu,b\nu,c\nu,a\n','README.md':'subject_id is the physical specimen identity.'}
ARGS={'split_file':'split.csv','sample_column':'image','partition_column':'part','train_values':['train'],'test_values':['test'],'mapping_file':'map.csv','mapping_sample_column':'image','entity_column':'subject_id'}
CITE={'file':'README.md','start_line':1,'end_line':1}
class Trusted:
    def primitive(self,kind,args,files):return measure(kind,files,args)
    def __call__(self,*args):return {'exit_code':0,'truncated':False,'stdout':'{"shared_entities":0}','output':{'shared_entities':0}}
def test_entity_witness_is_train_test_even_when_first_two_mappings_are_test():
    r=measure('entity_overlap',FILES,ARGS);o=r['output']
    assert o['shared_entities']==1 and o['affected_test_rows']==2
    w=o['witnesses'][0];assert w['train']['sample']=='a' and w['test']['sample']=='b'
    assert gate('entity_overlap',[r],[citation(FILES,CITE)])['verdict']=='violation'
def test_entity_twin_reordered_columns_and_full_coverage():
    twin={**FILES,'map.csv':'image,subject_id\nb,v\nc,w\na,u\n'}
    r=measure('entity_overlap',twin,ARGS)
    assert r['output']['shared_entities']==0
    assert gate('entity_overlap',[r],[citation(twin,CITE)])['verdict']=='clear_pending_confirmation'
    incomplete={**twin,'map.csv':'image,subject_id\na,u\n'}
    r=measure('entity_overlap',incomplete,ARGS)
    assert r['output']['coverage']['train']['complete'] and not r['output']['coverage']['test']['complete']
    assert gate('entity_overlap',[r],[citation(incomplete,CITE)])['verdict']=='insufficient'
def test_clear_requires_declared_column_documentation():
    files={**FILES,'map.csv':'image,subject_id\na,u\nb,v\nc,w\n'}
    r=measure('entity_overlap',files,ARGS)
    assert gate('entity_overlap',[r],[])['verdict']=='clear_pending_confirmation'
def test_exploration_json_cannot_support_any_verdict():
    i=Investigation(FILES,Trusted());i.dispatch('write_probe',{'code':'print(1)'});i.dispatch('run_probe',{'probe_id':'probe-1'})
    with pytest.raises(ValueError,match='Only retained'):
        i.dispatch('submit_verdict',{'scope':'x','explanation':'x','limitations':[],'missing_evidence':[],'measurement_ids':['probe-1']})
def test_host_gate_rejects_model_override_and_attaches_trusted_measurements():
    i=Investigation(FILES,Trusted());i.dispatch('entity_overlap',ARGS)
    v={'category':'entity_overlap','scope':'Specimen overlap','explanation':'Shared specimen','limitations':[],'missing_evidence':[],'measurement_ids':['measurement-1'],'citations':[CITE],'verdict':'clear'}
    with pytest.raises(ValueError,match='permits violation'):i.dispatch('submit_verdict',v)
    v['verdict']='violation';i.dispatch('submit_verdict',v)
    assert i.verdict['gate']['passed'] and i.verdict['measurements']['measurement-1']['shared_entities']==1
@pytest.mark.parametrize('c',[{'file':'README.md','start_line':0,'end_line':1},{'file':'README.md','start_line':1,'end_line':2},{'file':'README.md','quote':'invented'}])
def test_invalid_line_ranges_fail(c):
    with pytest.raises(ValueError):citation(FILES,c)
BASE='''import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold
X = np.array([[1.,2.],[3.,4.],[5.,6.],[7.,8.]])
cv = KFold(n_splits=2)
scaler = StandardScaler()
for a,b in cv.split(X):
    left = X[a]
    right = X[b]
    scaler.fit(left)
'''
def static(source):return measure('fit_sites',{'entry.py':source},{'file':'entry.py','class_names':['StandardScaler']})
def test_constructor_position_is_not_fit_leakage():
    r=static(BASE);f=r['output']['fit_calls'][0]
    assert f['fold_index_slice'] and not f['violation']
    assert gate('preprocessing',[r],[])['verdict']=='insufficient'
def test_full_matrix_inside_loop_and_mixed_rows_are_violations():
    for source in [BASE.replace('scaler.fit(left)','scaler.fit(X)'),BASE.replace('scaler.fit(left)','scaler.fit(np.vstack([left,right]))'),BASE.replace('cv = KFold','X_train_full = X\ncv = KFold').replace('scaler.fit(left)','scaler.fit(X_train_full)')]:
        r=static(source)
        assert gate('preprocessing',[r],[])['verdict']=='violation',r

def test_static_unknown_or_no_split_never_clear():
    for source in ['model.fit(mystery)','from sklearn.preprocessing import StandardScaler\ns = StandardScaler()\ns.fit(unknown)']:
        assert gate('preprocessing',[static(source)],[])['verdict']=='insufficient'

def test_symbol_words_and_logging_are_not_a_checkpoint_chain():
    source='test = [1]\nscore = model.score(X,test)\nbest = score\nprint(best)\nmodel.evaluate(X,test)\n'
    args={'file':'entry.py','test_symbol':'test','validation_symbol':'valid','model_symbol':'model','selection_role':'test','links':[{'line':i,'required_symbols':syms} for i,syms in enumerate([['test'],['test','score'],['score','best'],['best'],['model','test']],1)]}
    r=measure('symbol_chain',{'entry.py':source},args)
    assert not r['output']['violation'] and 4 in r['output']['failed_links']
    assert gate('checkpoint_selection',[r],[])['verdict']=='insufficient'
CHAIN='''test_labels = test_pack[1]
score = model.evaluate(test_pack[0], test_labels)
if score > best_score:
    best_score, best_weights = score, model.get_weights()
model.set_weights(best_weights)
model.evaluate(test_pack[0], test_labels)
'''
def chain_args(role='test'):
    label='test_labels' if role=='test' else 'valid_labels'
    return {'file':'entry.py','test_symbol':'test_labels','validation_symbol':'valid_labels','model_symbol':'model','selection_role':role,'links':[{'line':line,'required_symbols':syms} for line,syms in [(1,[label]),(2,[label,'score']),(4,['score','best_weights']),(5,['best_weights','model']),(6,['model','test_labels'])]]}
def test_checkpoint_verified_chain_and_validation_twin():
    bad=measure('symbol_chain',{'entry.py':CHAIN},chain_args())
    assert gate('checkpoint_selection',[bad],[])['verdict']=='violation',bad
    clean=CHAIN.replace('test_labels = test_pack[1]','valid_labels = valid_pack[1]').replace('score = model.evaluate(test_pack[0], test_labels)','score = model.evaluate(valid_pack[0], valid_labels)')
    good=measure('symbol_chain',{'entry.py':clean},chain_args('validation'))
    g=gate('checkpoint_selection',[good],[])
    assert g['verdict']=='clear',good
    assert 'validation and test disjointness not established' in g['limitations']
    assert bad['output']!=good['output']
def test_checkpoint_missing_persistence_or_different_model_fails_gate():
    for source in (CHAIN.replace('model.set_weights(best_weights)','print(best_weights)'),CHAIN.replace('model.evaluate(test_pack[0], test_labels)\n','other.evaluate(test_pack[0], test_labels)\n')):
        r=measure('symbol_chain',{'entry.py':source},chain_args())
        assert gate('checkpoint_selection',[r],[])['verdict']=='insufficient'
def test_clear_selection_alias_cannot_hide_test_labels():
    source='test_labels = pack[1]\nvalid_labels = test_labels\nscore = model.evaluate(pack[0], valid_labels)\nif score > best_score:\n    best_score, best_weights = score, model.get_weights()\nmodel.set_weights(best_weights)\nmodel.evaluate(pack[0], test_labels)\n'
    args=chain_args('validation')
    for link in args['links']:link['line']+=1
    r=measure('symbol_chain',{'entry.py':source},args)
    assert gate('checkpoint_selection',[r],[])['verdict']=='insufficient'
def test_measurement_cherry_picking_rejected():
    i=Investigation(FILES,Trusted());i.dispatch('entity_overlap',ARGS);i.dispatch('entity_overlap',ARGS)
    with pytest.raises(ValueError,match='all retained'):
        i.dispatch('submit_verdict',{'category':'entity_overlap','verdict':'violation','scope':'x','explanation':'x','limitations':[],'missing_evidence':[],'measurement_ids':['measurement-1'],'citations':[CITE]})

def test_named_loaded_matrix_resolves_against_its_split_not_its_variable_name():
    source=BASE.replace('X = np.array([[1.,2.],[3.,4.],[5.,6.],[7.,8.]])','X = load_matrix()').replace('scaler.fit(left)','scaler.fit(X)')
    assert gate('preprocessing',[static(source)],[])['verdict']=='violation'
def test_conditional_dead_fit_is_not_asserted_as_executed_violation():
    source=BASE.replace('    scaler.fit(left)','    if False:\n        scaler.fit(X)')
    assert gate('preprocessing',[static(source)],[])['verdict']=='insufficient'
