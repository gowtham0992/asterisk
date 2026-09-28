import json

from fastapi.testclient import TestClient

from app import main
from app.ladder_receipts import Receipts
from tests.test_api import client, HEADERS
from tests.test_ladder import tcga


def payload():
    spec, files = tcga(['TCGA-AB-0001-01Z-DX1'], ['TCGA-AB-0001-01Z-DX2'])
    return {'spec': spec, 'files': [{'name': n, 'content': c} for n, c in files.items()]}


def save(client, body=None):
    response = client.post('/api/ladder/receipts', json=body or payload(), headers=HEADERS)
    assert response.status_code == 201, response.text
    return response.json()


def test_saved_ladder_survives_reopen_and_exports_full_measurement(client):
    record = save(client)
    assert record['result']['finding']['status'] == 'violation'
    assert record['execution'] == {'kind': 'local', 'provenance': None}
    assert 'files' not in record
    rid = record['id']
    assert client.get('/api/ladder/receipts/'+rid).json() == record
    assert client.get('/api/ladder/receipts').json()[0]['id'] == rid
    exported = client.get('/api/ladder/receipts/'+rid+'/export?format=json').json()
    assert exported['result']['levels'][1]['witnesses']
    html = client.get('/api/ladder/receipts/'+rid+'/export')
    assert 'text/html' in html.headers['content-type']
    assert 'No Sandbox replay' in html.text and 'TCGA-AB-0001' in html.text


def test_saved_ladders_are_owner_scoped_including_exports_and_deletion(client):
    rid = save(client)['id']
    with TestClient(main.app) as other:
        other.get('/api/session')
        assert other.get('/api/ladder/receipts').json() == []
        for path in [rid, rid+'/export', rid+'/export?format=json']:
            assert other.get('/api/ladder/receipts/'+path).status_code == 404
        assert other.delete('/api/ladder/receipts/'+rid, headers=HEADERS).status_code == 404
    assert client.delete('/api/ladder/receipts/'+rid, headers=HEADERS).status_code == 200
    assert client.get('/api/ladder/receipts/'+rid).status_code == 404


def test_saved_result_and_execution_cannot_be_supplied_by_client(client):
    for key, value in [('result', {'finding': {'status': 'held_out'}}), ('provenance', {'matches_local': True})]:
        assert client.post('/api/ladder/receipts', json={**payload(), key: value}, headers=HEADERS).status_code == 422
    assert client.post('/api/ladder/receipts', json=payload()).status_code == 403


def test_pending_confirmation_is_preserved_and_html_escapes_claim(client):
    spec, files = tcga(['TCGA-AB-0001-01Z-DX1', 'TCGA-AB-0001-01Z-DX2'], ['TCGA-AB-0002-01Z-DX1'])
    spec['claim']['text'] = '<script>alert("bad")</script> New patients'
    record = save(client, {'spec': spec, 'files': [{'name': n, 'content': c} for n, c in files.items()]})
    assert record['result']['finding']['status'] == 'held_out_pending_confirmation'
    html = client.get('/api/ladder/receipts/'+record['id']+'/export').text
    assert '<script>' not in html and '&lt;script&gt;' in html


def test_changed_database_record_cannot_be_displayed_or_exported(client):
    rid = save(client)['id']
    with main.connect() as db:
        row = db.execute('SELECT payload FROM ladder_receipts WHERE id=?', (rid,)).fetchone()
        value = json.loads(row['payload'])
        value['result']['finding']['status'] = 'held_out'
        db.execute('UPDATE ladder_receipts SET payload=? WHERE id=?', (json.dumps(value), rid))
    assert client.get('/api/ladder/receipts/'+rid).status_code == 409
    assert client.get('/api/ladder/receipts/'+rid+'/export').status_code == 409


def test_server_replay_is_saved_with_actual_provenance(tmp_path):
    import sqlite3
    from fastapi import FastAPI
    from app.ladder_api import register
    from app.ladder import measure
    def connect():
        db = sqlite3.connect(tmp_path/'saved.sqlite')
        db.row_factory = sqlite3.Row
        return db
    def sandbox(spec, files, confirmed, *_):
        return measure(spec, files, confirmed), {'matches_local': True, 'runtime': 'test-only-fake'}
    app = FastAPI()
    register(app, lambda request: 'owner', sandbox=sandbox, connect=connect)
    with TestClient(app) as c:
        replay = c.post('/api/ladder/replay', json=payload()).json()
        saved = c.get('/api/ladder/receipts/'+replay['receipt_id']).json()
        assert saved['execution']['kind'] == 'sandbox_replay'
        assert saved['execution']['provenance'] == replay['provenance']
        assert saved['result'] == replay['result']


def test_storage_failure_does_not_turn_successful_replay_into_retry(tmp_path, monkeypatch):
    import sqlite3
    from fastapi import FastAPI
    from app.ladder_api import register
    from app.ladder import measure
    calls = []
    def sandbox(spec, files, confirmed, *_):
        calls.append(1)
        return measure(spec, files, confirmed), {'matches_local': True}
    def unavailable(*args, **kwargs):
        raise sqlite3.OperationalError('private database path')
    monkeypatch.setattr(Receipts, 'save', unavailable)
    app = FastAPI()
    register(app, lambda request: 'owner', sandbox=sandbox, connect=lambda: sqlite3.connect(tmp_path/'limits.sqlite'))
    with TestClient(app) as c:
        response = c.post('/api/ladder/replay', json=payload())
    assert response.status_code == 200 and calls == [1]
    assert response.json()['provenance']['matches_local'] is True
    assert 'another replay is not needed' in response.json()['receipt_error']
    assert 'private database path' not in response.text


def test_saved_proposal_provenance_is_owner_scoped_and_edits_are_computed(client):
    store = Receipts(main.connect)
    # The proposer uses this server-owned method after its provider call.
    body = payload()
    files = {f['name']: f['content'] for f in body['files']}
    owner = 'record-owner'
    proposal = {'proposal': {'status': 'ladder', 'spec': body['spec']},
                'model': 'test-model', 'model_name': 'Nemotron test stub',
                'provider': 'test-only', 'payload_sha256': 'abc', 'attempts': [{'error': None}]}
    pid = store.record_proposal(owner, proposal, files, 'v4')
    origin = store.binding_origin(owner, pid, body['spec'], files)
    assert origin['edited'] is False and origin['prompt_version'] == 'v4'
    body['spec']['levels'][1]['meaning'] = 'edited meaning'
    assert store.binding_origin(owner, pid, body['spec'], files)['edited'] is True
    from fastapi import HTTPException
    import pytest
    with pytest.raises(HTTPException) as error:
        store.binding_origin('another-owner', pid, body['spec'], files)
    assert error.value.status_code == 404
    assert store.binding_origin(owner, None, body['spec'], files)['kind'] == 'user_supplied'


def test_propose_save_export_preserves_server_origin_and_rejects_foreign_id(tmp_path, monkeypatch):
    import sqlite3
    from fastapi import FastAPI
    from app.ladder_api import register
    from tests.test_ladder_proposal import CLAIM, FILES, spec
    monkeypatch.setenv('NEBIUS_API_KEY', 'fake-test-key')
    def connect():
        db = sqlite3.connect(tmp_path/'origin.sqlite')
        db.row_factory = sqlite3.Row
        return db
    def completion(*args):
        return lambda *args: json.dumps({'status': 'ladder', 'spec': spec()}), {'calls': 1, 'total_tokens': 100}
    calls = []
    def sandbox(*args):
        calls.append(1)
        raise AssertionError('Foreign proposal must be rejected before remote execution')
    app = FastAPI()
    register(app, lambda request: request.headers.get('test-owner', 'a'), completion=completion, sandbox=sandbox, connect=connect)
    files = [{'name': n, 'content': v} for n, v in FILES.items()]
    with TestClient(app) as c:
        proposed = c.post('/api/ladder/propose', json={'claim': CLAIM, 'files': files, 'documentation': ['README.md']})
        assert proposed.status_code == 200, proposed.text
        body = {'spec': spec(), 'files': files, 'proposal_id': proposed.json()['proposal_id']}
        saved = c.post('/api/ladder/receipts', json=body)
        assert saved.status_code == 201, saved.text
        origin = saved.json()['binding_origin']
        assert origin['edited'] is False and origin['inputs_changed'] is False
        page = c.get('/api/ladder/receipts/'+saved.json()['id']+'/export').text
        assert 'Proposed by Nemotron 3 Super' in page and 'Prompt v4' in page
        assert proposed.json()['payload_sha256'] in page
        body['spec']['levels'][1]['meaning'] = 'Person edited this'
        assert c.post('/api/ladder/receipts', json=body).json()['binding_origin']['edited'] is True
        for path in ('receipts', 'replay'):
            assert c.post('/api/ladder/'+path, json=body, headers={'test-owner':'b'}).status_code == 404
        assert calls == []


def test_receipt_cap_rejects_31st_and_delete_releases_capacity(client):
    records = [save(client) for _ in range(30)]
    assert client.post('/api/ladder/receipts', json=payload(), headers=HEADERS).status_code == 409
    assert client.delete('/api/ladder/receipts/'+records[0]['id'], headers=HEADERS).status_code == 200
    assert save(client)['id']


def test_global_storage_cap_also_covers_new_owners(client, monkeypatch):
    from app import ladder_receipts
    monkeypatch.setattr(ladder_receipts, 'MAX_RECEIPT_STORAGE_BYTES', 1)
    assert client.post('/api/ladder/receipts', json=payload(), headers=HEADERS).status_code == 409
    with TestClient(main.app) as other:
        other.get('/api/session')
        assert other.post('/api/ladder/receipts', json=payload(), headers=HEADERS).status_code == 409
    assert client.get('/api/ladder/receipts').json() == []


def test_shipped_clean_example_requires_confirmation_and_retains_it_on_export(client):
    from pathlib import Path
    folder = Path(__file__).resolve().parents[1]/'static/ladder-example-clean'
    body = {'spec': json.loads((folder/'spec.json').read_text()),
            'files': [{'name': n, 'content': (folder/n).read_text()} for n in ('split.csv','subjects.csv','README.md')]}
    pending = save(client, body)
    assert pending['result']['finding']['status'] == 'held_out_pending_confirmation'
    before = client.get('/api/ladder/receipts/'+pending['id']+'/export').text
    assert '<h1>No shared values;' in before and 'confirmation pending' in before
    confirmed = save(client, {**body, 'confirmed':['subject']})
    assert confirmed['result']['finding']['status'] == 'held_out'
    page = client.get('/api/ladder/receipts/'+confirmed['id']+'/export').text
    assert '<h1>Held out (meaning confirmed): subject</h1>' in page
    assert 'subject from subjects.csv' in page
    assert 'test → test (4 rows)' in page
    assert 'no server-recorded model proposal is linked' in page
    assert client.get('/api/ladder/receipts/'+pending['id']).json()['result']['confirmed_levels'] == []
