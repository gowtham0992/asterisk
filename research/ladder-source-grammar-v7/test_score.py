import copy,importlib.util
from pathlib import Path
p=Path(__file__).with_name('score.py');s=importlib.util.spec_from_file_location('grammar_score',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def rows():
    names=['ucf101-exposed','qualified-lines','middle-characters','lookup-distractor','denied-specimen','actor-missing']
    result=[]
    for trial in (1,2):
        for name in names:
            for version in ('v4','v7'):
                r={'id':name,'trial':trial,'version':version,'first_valid':True,'first_correct':True,'final_correct':True,
                   'unsupported':False,'wrong_reassurance':False,'rejected_calls':0,'usage':{'total_tokens':10},'trace':[{'reply':'{}'}]}
                if version=='v4' and name in ('qualified-lines','middle-characters'):
                    r.update(first_correct=False,rejected_calls=1);r['trace'].append({'reply':'{}'})
                result.append(r)
    return result

def test_invalid_model_reply_is_completed_inference_but_not_correct():
    r=rows();r[0].update(error='LadderError: invalid JSON',first_valid=False,first_correct=False,final_correct=False)
    assert m.summarize(r)['inference_complete'] is True
    assert m.summarize(r)['v4']['final_correct']==11

def test_missing_or_duplicate_rows_cannot_complete_a_study():
    r=rows();assert m.summarize(r[:-1])['inference_complete'] is False
    r[-1]=copy.deepcopy(r[0]);assert m.summarize(r)['inference_complete'] is False

def test_provider_failure_is_incomplete_even_if_a_later_reply_is_present():
    r=rows();r[0]['trace'].insert(0,{'error':'TimeoutError'})
    assert m.summarize(r)['inference_complete'] is False
    assert m.summarize(r)['promote'] is False

def test_candidate_must_pass_ucf101_twice_and_no_regression_not_just_total_score():
    r=rows();assert m.summarize(r)['promote'] is True
    r[1].update(first_correct=False)
    assert m.summarize(r)['promote'] is False
    r=rows();r[1].update(final_correct=False)
    assert m.summarize(r)['paired_regressions']==[('ucf101-exposed',1)]
    assert m.summarize(r)['promote'] is False
