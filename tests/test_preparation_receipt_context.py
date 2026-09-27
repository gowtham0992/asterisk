import json
from tests.test_preparation_package import prepared
from app.preparation.handoff import files_for
from app.preparation.receipt_context import retained_preparation


def inputs():
    s=prepared()
    record=s.confirm(s.review['review_hash'],True)
    return files_for(record)


def test_retained_preparation_recomputes_and_exposes_original_passage():
    files=inputs();context=retained_preparation(files)
    assert 'error' not in context
    record=json.loads(files['preparation-review.json'])
    assert context['spec']==record['review']['extraction']['spec']
    for passage in context['passages']:
        assert passage['quote']=='\n'.join(record['inputs'][passage['file']].splitlines()[passage['first']-1:passage['last']])


def test_changed_tables_or_forged_record_cannot_borrow_preparation_context():
    files=inputs();files['splits.csv']+='forged,test\n'
    assert 'error' in retained_preparation(files)
    files=inputs();record=json.loads(files['preparation-review.json']);record['confirmation']['actor']='forged'
    files['preparation-review.json']=json.dumps(record)
    assert 'error' in retained_preparation(files)
    assert retained_preparation({}) is None
    assert 'error' in retained_preparation({'preparation-review.json':'{}'})


def test_proposal_attribution_requires_recomputed_preparation_and_matching_tables():
    from app.preparation.proposal import ProposalRequest
    s = prepared()
    request = ProposalRequest(s.files, 'Evaluation units must be absent from training.')
    proposed = request.submit(request.preview()['payload_hash'], True,
        lambda *_: {'content': json.dumps(s.spec)})['session']
    proposed.preview({'data.csv': {'sample': {'column': 'sample'}, 'repeats': 'distinct',
                                  'evidence': s.spec['citations']}})
    record = proposed.confirm(proposed.review['review_hash'], True)
    files = files_for(record)
    context = retained_preparation(files)
    assert context['model_proposal']['model'] == 'nvidia/nemotron-3-super-120b-a12b'
    assert context['model_proposal']['provider'] == 'Nebius Token Factory'
    assert context['model_proposal']['payload_hash'] == request.preview()['payload_hash']
    assert 'messages' not in context['model_proposal']
    files['entities.csv'] += 'forged,p3\n'
    assert 'model_proposal' not in retained_preparation(files)
