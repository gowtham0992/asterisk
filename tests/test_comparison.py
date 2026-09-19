from fastapi.testclient import TestClient
from app import main
from app.examples import example
from tests.test_api import client, create, HEADERS
from tests.test_revisions import proposed
from tests.test_audit import RULE


def test_comparison_flags_changed_rule_even_when_files_are_identical(client,monkeypatch):
    aid=proposed(client,monkeypatch)
    client.post('/api/audits/'+aid+'/execute',json={},headers=HEADERS)
    body={'rule':{**RULE,'entity_column':'capture','unit':'image'},'note':'Compare image rather than specimen identity.'}
    child=client.post('/api/audits/'+aid+'/with-rule',json=body,headers=HEADERS).json()['id']
    client.post('/api/audits/'+child+'/execute',json={},headers=HEADERS)
    data=client.get('/api/audits/'+child+'/comparison').json()
    assert data['contract_changed'] and data['both_complete']
    assert all(f['change']=='unchanged' for f in data['files'])
    assert next(m for m in data['metrics'] if m['field']=='shared_entities')=={'field':'shared_entities','before':16,'after':0}


def test_comparison_does_not_turn_missing_measurements_into_zero(client):
    aid=client.post('/api/audits',json=example('missing'),headers=HEADERS).json()['id']
    child=client.post('/api/audits/'+aid+'/with-inputs',json=example(),headers=HEADERS).json()['id']
    data=client.get('/api/audits/'+child+'/comparison').json()
    assert not data['both_complete'] and all(m['before'] is None and m['after'] is None for m in data['metrics'])
    assert next(f for f in data['files'] if f['name']=='specimens.csv')['change']=='added'


def test_comparison_cannot_reveal_another_browser_parent(client):
    aid=create(client)
    child=client.post('/api/audits/'+aid+'/with-inputs',json=example(),headers=HEADERS).json()['id']
    with TestClient(main.app) as other:
        other.get('/api/session')
        assert other.get('/api/audits/'+child+'/comparison').status_code==404


def test_comparison_handles_missing_or_deleted_parent(client):
    aid=create(client)
    assert client.get('/api/audits/'+aid+'/comparison').status_code==409
    child=client.post('/api/audits/'+aid+'/with-inputs',json=example(),headers=HEADERS).json()['id']
    client.delete('/api/audits/'+aid,headers=HEADERS)
    assert client.get('/api/audits/'+child+'/comparison').status_code==404
    assert client.get('/api/audits/'+child).status_code==200
