import json
import pytest
from scripts.run_benchmark_smoke import CASES, digest, run
from app.preparation.proposal import ProposalRequest


@pytest.fixture
def packet(tmp_path):
    directory = tmp_path / 'packets'
    directory.mkdir()
    entries = []
    for name in CASES:
        files = {'rows.csv': 'sample,person,split\na,p,train\nb,p,test\n',
                 'documentation.txt': 'person identifies the generating individual.'}
        claim = 'Test people should not occur in training.'
        request = ProposalRequest(files, claim, ['documentation.txt'], [])
        preview = request.preview()
        raw = json.dumps({'case': name, 'files': files, 'claim': claim,
                          'projection': [], 'preview': preview}).encode()
        (directory / (name + '.json')).write_bytes(raw)
        entries.append({'case': name, 'packet_sha256': digest(raw), 'payload_hash': preview['payload_hash']})
    inventory = json.dumps({'trials': 3, 'retries': 0, 'cases': entries}).encode()
    (directory / 'inventory.json').write_bytes(inventory)
    approval = tmp_path / 'approval.json'
    approval.write_text(json.dumps({'approved': True, 'inventory_sha256': digest(inventory)}))
    return directory, approval, tmp_path / 'results'


def test_wrong_approval_never_initializes_provider(packet):
    directory, approval, output = packet
    approval.write_text('{}')
    with pytest.raises(ValueError, match='approval'):
        run(directory, approval, output, completion_factory=lambda: pytest.fail('Provider initialized'))


def test_tampered_packet_never_initializes_provider(packet):
    directory, approval, output = packet
    with (directory / 'wsi.json').open('a') as stream:
        stream.write(' ')
    with pytest.raises(ValueError, match='bytes changed'):
        run(directory, approval, output, completion_factory=lambda: pytest.fail('Provider initialized'))


def test_invalid_completion_retained_without_retry(packet):
    directory, approval, output = packet
    calls = []
    def complete(*args):
        calls.append(args)
        return {'content': 'not JSON', 'estimated_usd': 0}
    result = run(directory, approval, output, completion_factory=lambda: complete)
    assert len(calls) == 3
    assert [item['status'] for item in result['outcomes']] == ['invalid_proposal'] * 3
    assert json.loads((output / 'dermamnist/completion.json').read_text())['content'] == 'not JSON'
    with pytest.raises(FileExistsError):
        run(directory, approval, output.parent / 'different-results', completion_factory=lambda: complete)
    assert len(calls) == 3


def test_timeout_stops_whole_batch(packet):
    directory, approval, output = packet
    calls = []
    def complete(*args):
        calls.append(args)
        raise TimeoutError('potentially sensitive transport detail')
    result = run(directory, approval, output, completion_factory=lambda: complete)
    assert len(calls) == len(result['outcomes']) == 1
    recorded = (output / 'dermamnist/provider-error.json').read_text()
    assert 'TimeoutError' in recorded and 'sensitive' not in recorded
    assert not (output / 'ptbxl').exists()


def test_insufficient_preserved_without_confirmation(packet):
    directory, approval, output = packet
    result = run(directory, approval, output, completion_factory=lambda:
                 lambda *args: {'content': '{"status":"insufficient","missing":["No identity evidence"]}'})
    assert [item['status'] for item in result['outcomes']] == ['insufficient'] * 3
    assert all('spec' not in item for item in result['outcomes'])


def test_valid_proposal_keeps_binding_and_requires_review(packet):
    directory, approval, output = packet
    spec = {'status': 'extract', 'sources': [{'file': 'rows.csv', 'format': 'csv',
            'sample': {'column': 'sample'}, 'entity': {'column': 'person'},
            'partition': {'column': 'split', 'map': {'train': 'train', 'test': 'test'}}}],
            'citations': [{'file': 'documentation.txt', 'start_line': 1, 'end_line': 1}]}
    result = run(directory, approval, output, completion_factory=lambda:
                 lambda *args: {'content': json.dumps(spec)})
    assert len(result['outcomes']) == 3
    for item in result['outcomes']:
        assert item['status'] == 'review_required'
        assert item['spec'] == spec
        assert item['scientific_confirmation'] is None
        assert (output / item['case'] / 'model-record.json').exists()


def test_recording_failure_stops_after_retaining_completion(packet, monkeypatch):
    import scripts.run_benchmark_smoke as runner
    directory, approval, output = packet
    spec = {'status': 'extract', 'sources': [{'file': 'rows.csv', 'format': 'csv',
            'sample': {'column': 'sample'}, 'entity': {'column': 'person'},
            'partition': {'column': 'split', 'map': {'train': 'train', 'test': 'test'}}}],
            'citations': [{'file': 'documentation.txt', 'start_line': 1, 'end_line': 1}]}
    original = runner.write_new
    def fail_record(path, value):
        if path.name == 'model-record.json':
            raise OSError('disk failure')
        original(path, value)
    monkeypatch.setattr(runner, 'write_new', fail_record)
    calls = []
    def complete(*args):
        calls.append(args)
        return {'content': json.dumps(spec)}
    result = run(directory, approval, output, completion_factory=lambda: complete)
    assert len(calls) == 1
    assert result['outcomes'][0]['status'] == 'stopped_provider_or_recording_failure'
    assert (output / 'dermamnist/completion.json').exists()
    assert not (output / 'ptbxl').exists()
