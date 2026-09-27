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
    def unavailable(*args):
        raise sqlite3.OperationalError('private database path')
    monkeypatch.setattr(Receipts, 'save', unavailable)
    app = FastAPI()
    register(app, lambda request: 'owner', sandbox=sandbox, connect=lambda: None)
    with TestClient(app) as c:
        response = c.post('/api/ladder/replay', json=payload())
    assert response.status_code == 200 and calls == [1]
    assert response.json()['provenance']['matches_local'] is True
    assert 'another replay is not needed' in response.json()['receipt_error']
    assert 'private database path' not in response.text
