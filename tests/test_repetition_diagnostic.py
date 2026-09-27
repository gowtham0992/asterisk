import copy
import json
import pytest
from app.preparation.intake import open_inputs
from app.preparation.review import executor,prepare
from app.preparation.choice_errors import choice_error
from app.preparation.repetition_diagnostic import annotate_repetition_error,DUPLICATE_ERROR

SPEC={'status':'extract','sources':[{'file':'data.csv','format':'csv','sample':{'column':'reading'},'entity':{'column':'fixture'},'partition':{'column':'phase','map':{'fit':'train','check':'test'}}}],'citations':[{'file':'notes.txt','start_line':1,'end_line':1}]}

def files(last='r1,u1,fit'):
    return {'data.csv':'reading,fixture,phase\nr1,u1,fit\nr2,u2,fit\nr3,u3,check\n'+last+'\n','notes.txt':'reading is the observation; fixture is the subject. Repeated IDs are retransmissions only when subject and partition agree.'}

@pytest.mark.parametrize('last,phrase',[('r1,u1,fit','Combining them passes'),('r1,u9,fit','different subjects or partitions'),('r1,u1,check','different subjects or partitions')])
def test_intake_explains_repetition_without_accepting_or_changing_policy(last,phrase):
    spec=copy.deepcopy(SPEC);inputs=files(last);before=copy.deepcopy((spec,inputs))
    session=open_inputs(json.dumps(spec),inputs)
    assert phrase in session.proposal_issue
    assert session.confirmation is None
    assert (spec,inputs)==before
    assert 'deduplicate' not in session.spec['sources'][0]
    with pytest.raises(executor.ExtractionError,match=DUPLICATE_ERROR):executor.extract(session.spec,inputs)
    policies={'data.csv':{'sample':{'column':'reading'},'repeats':'distinct','evidence':SPEC['citations']}}
    with pytest.raises(executor.ExtractionError) as caught:prepare(spec,inputs,policies)
    assert phrase in choice_error(caught.value)


def test_later_unrelated_blocker_does_not_claim_combining_is_sufficient():
    inputs=files();inputs['data.csv']+='r4,u4,unknown\n'
    session=open_inputs(json.dumps(SPEC),inputs)
    assert session.proposal_issue==choice_error(ValueError(DUPLICATE_ERROR))
    assert 'passes the structural checks' not in session.proposal_issue


def test_diagnostic_does_not_retry_other_errors_or_surface_source_values():
    class NoExecution:
        def extract(*args):raise AssertionError('Should not execute')
    exc=ValueError('Column missing')
    assert annotate_repetition_error(exc,{}, {},NoExecution()) is exc
    assert choice_error(ValueError('private source values')) is None


def test_uninspectable_later_record_preserves_original_rejection():
    spec=copy.deepcopy(SPEC);spec['sources'][0].update(file='data.json',format='json')
    rows=[{'reading':'r1','fixture':'u1','phase':'fit'},{'reading':'r1','fixture':'u1','phase':'fit'},
          {'reading':'r2','fixture':'u2','phase':[]}]
    inputs={'data.json':json.dumps(rows),'notes.txt':'identity definitions'}
    session=open_inputs(json.dumps(spec),inputs)
    assert session.proposal_issue==choice_error(ValueError(DUPLICATE_ERROR))


def test_rejected_intake_releases_executor_frame_before_diagnostic(monkeypatch):
    import weakref
    class ParsedTables:pass
    references=[]
    def extract(spec,inputs):
        if not references:
            tables=ParsedTables();references.append(weakref.ref(tables))
            raise executor.ExtractionError(DUPLICATE_ERROR)
        assert references[0]() is None, 'Original parse must be released before the second pass'
        return {}
    monkeypatch.setattr(executor,'extract',extract)
    session=open_inputs(json.dumps(SPEC),files())
    assert 'Combining them passes' in session.proposal_issue
