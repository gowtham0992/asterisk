import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from study import cases,correct,summarize
from app import ladder_proposal as lp


def proposed(expression):
    return {'status':'ladder','spec':{'schema':'asterisk-ladder/1','claim':{'text':'Evaluation material batches are unseen in training.','level':'batch'},
      'sources':[{'file':'runs.csv','format':'csv','sample':{'column':'capture'},'partition':{'column':'partition','map':{'train':'train','test':'test'}}}],
      'levels':[{'name':'capture','kind':'observation','expression':{'column':'capture'}},{'name':'batch','kind':'unit','expression':expression}],
      'citations':[{'file':'README.md','start_line':1,'end_line':2}]}}


def test_full_grouping_not_overlap_headline():
    case=cases()[1]
    assert correct(proposed({'column':'capture','characters':{'from':3,'to':5}}),case)
    assert not correct(proposed({'column':'capture','prefix':2}),case)
    assert not correct(proposed({'column':'capture'}),case)
    assert not correct({'status':'abstain','missing':'unknown'},case)


def test_controls_require_abstention_and_supported_cases_do_not():
    assert correct({'status':'abstain','missing':'No mapping'},cases()[-1])
    assert not correct(proposed({'column':'capture'}),cases()[-1])


def test_incomplete_and_wrong_candidate_do_not_promote():
    rows=[dict(id=c['id'],version=v,trial=t,first_correct=True,final_correct=True,trace=[{'reply':'x'}],tokens=1) for c in cases() for v in ['v4','v8'] for t in [1,2]]
    assert not summarize(rows)['promote']  # no improvement over baseline
    for r in rows:
        if r['version']=='v4' and r['id']=='namespaced-lines':r['first_correct']=False
    assert summarize(rows)['promote']
    assert not summarize(rows[:-1])['promote']
    rows[-1]['final_correct']=False
    assert not summarize(rows)['promote']


def test_candidate_is_separate_and_has_source_grammar():
    assert lp.PROMPT_VERSION=='v4'
    assert 'EXAMPLE (fictional).' not in lp.PROMPTS['v8']
    assert 'SOURCE SAMPLE GRAMMAR' in lp.PROMPTS['v8']
