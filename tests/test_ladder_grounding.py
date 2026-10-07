import json
import pytest
from app import ladder_proposal as lp
from app.ladder import LadderError
from tests.test_ladder_proposal import CLAIM, FILES


def test_grounding_candidate_uses_explicit_original_line_numbers():
    files = {**FILES, 'notes.md': 'First.\n\nThird.\n'}
    body = lp.payload(CLAIM, files, version='v5')
    assert body['documentation']['notes.md'] == [
        {'line': 1, 'text': 'First.'}, {'line': 2, 'text': ''}, {'line': 3, 'text': 'Third.'}]
    assert lp.payload(CLAIM, files, version='v4')['documentation']['notes.md'] == ['First.', '', 'Third.']
    assert json.loads(lp.request(CLAIM, files, version='v5')[1]['content']) == body


def test_model_request_refuses_oversize_profiles_before_provider_call():
    files = {'README.md': 'Each identifier is one observation.', **{
        f'data-{i}.csv': ','.join('column-'+str(c)+'x'*250 for c in range(80))+'\n'+','.join('a' for c in range(80))+'\n'
        for i in range(12)}}
    called = []
    with pytest.raises(LadderError, match='model request'):
        lp.propose(CLAIM, files, lambda *a: called.append(a))
    assert not called
