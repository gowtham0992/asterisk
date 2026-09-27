import json
import pytest
from app.preparation.proposal import ProposalRequest


@pytest.mark.parametrize('documentation', [None, ['README.md']])
def test_identity_definition_after_line_100_reaches_approved_payload(documentation):
    lines = ['Background information.'] * 140 + ['source identifies the original recording.']
    request = ProposalRequest({'rows.csv': 'sample,source,split\na,r1,train\nb,r1,test\n',
                               'README.md': '\n'.join(lines)},
                              'Original recordings must be unseen in evaluation.',
                              documentation=documentation)
    preview = request.preview()
    doc = json.loads(preview['messages'][1]['content'])['files']['README.md']
    assert doc['lines'][-1] == {'line': 141, 'text': lines[-1]}
    assert doc['truncated'] is False
    assert doc['total_lines'] == 141
    calls = []
    def complete(messages, *_):
        calls.append(messages)
        return {'content': '{"status":"insufficient","missing":["test evidence"]}'}
    request.submit(preview['payload_hash'], True, complete)
    assert calls == [preview['messages']]


@pytest.mark.parametrize('documentation', [None, ['README.md']])
def test_large_document_is_rejected_rather_than_silently_truncated(documentation):
    with pytest.raises(ValueError, match='[Dd]ocumentation|preview exceeds'):
        ProposalRequest({'rows.csv': 'sample\na\n', 'README.md': 'x' * 101_000},
                        'Original recordings must be unseen in evaluation.',
                        documentation=documentation)
