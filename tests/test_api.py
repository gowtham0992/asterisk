import io
import json
import sqlite3
import subprocess
import sys
import zipfile
import pytest
from fastapi.testclient import TestClient
from app import main
from app.examples import example
from app.agent import AgentError
from tests.test_audit import RULE

HEADERS={'X-Asterisk-Request':'1'}

@pytest.fixture
def client(tmp_path, monkeypatch):
    # Historical workflow tests opt in; production defaults keep mutations disabled.
    monkeypatch.setenv('ASTERISK_LEGACY_AUDITS','1')
    monkeypatch.setattr(main,'DB',tmp_path/'test.sqlite')
    with main.connect() as db:
        db.executescript('CREATE TABLE sessions (id TEXT PRIMARY KEY); CREATE TABLE audits (id TEXT PRIMARY KEY, owner TEXT NOT NULL, payload TEXT NOT NULL);')
    with TestClient(main.app) as c:
        c.get('/api/session')
        yield c


def create(c):
    r=c.post('/api/audits',json=example(),headers=HEADERS)
    assert r.status_code==201
    return r.json()['id']


def test_other_browser_cannot_access_audit_or_export(client):
    aid=create(client)
    with TestClient(main.app) as other:
        other.get('/api/session')
        assert other.get('/api/audits/'+aid).status_code==404
        assert other.get('/api/audits/'+aid+'/export').status_code==404
        assert other.post('/api/audits/'+aid+'/execute',json={},headers=HEADERS).status_code==404


def test_cross_origin_posts_and_missing_header_rejected(client):
    assert client.post('/api/audits',json=example()).status_code==403
    assert client.post('/api/audits',json=example(),headers={**HEADERS,'Origin':'https://evil.example'}).status_code==403


def test_path_traversal_filename_rejected(client):
    payload=example();payload['files'][0]['name']='../secret.csv'
    assert client.post('/api/audits',json=payload,headers=HEADERS).status_code==422


def test_oversized_body_rejected(client):
    assert client.post('/api/audits',content='x'*4_200_001,headers=HEADERS).status_code==413


def test_cannot_execute_unreviewed_draft(client):
    aid=create(client)
    assert client.post('/api/audits/'+aid+'/execute',json={},headers=HEADERS).status_code==409


def test_api_failure_preserves_draft(client,monkeypatch):
    def fail(*args):raise AgentError('Provider unavailable')
    monkeypatch.setattr(main,'propose',fail)
    monkeypatch.setenv('NEBIUS_API_KEY','test-key')
    aid=create(client)
    assert client.post('/api/audits/'+aid+'/propose',json={},headers=HEADERS).status_code==502
    assert client.get('/api/audits/'+aid).json()['state']=='draft'


def test_complete_audit_export_replays_and_detects_tampering(client,monkeypatch,tmp_path):
    monkeypatch.setattr(main,'propose',lambda *args: ({'status':'ready','rule':RULE,'questions':[]},{'model':'test-stub','seconds':0,'tokens':0}))
    monkeypatch.setenv('NEBIUS_API_KEY','test-key')
    aid=create(client)
    assert client.post('/api/audits/'+aid+'/propose',json={},headers=HEADERS).json()['state']=='review'
    run=client.post('/api/audits/'+aid+'/execute',json={},headers=HEADERS)
    assert run.json()['result']['shared_entities']==16
    assert client.post('/api/audits/'+aid+'/execute',json={},headers=HEADERS).json()==run.json()
    archive=client.get('/api/audits/'+aid+'/export')
    dest=tmp_path/'export';dest.mkdir()
    with zipfile.ZipFile(io.BytesIO(archive.content)) as z:z.extractall(dest)
    result=subprocess.run([sys.executable,str(dest/'verify.py')],capture_output=True,text=True)
    assert result.returncode==0 and 'reproduced exactly' in result.stdout
    p=dest/'inputs'/'specimens.csv';p.write_text(p.read_text().replace('frame_0081,specimen_0001','frame_0081,specimen_9000'))
    result=subprocess.run([sys.executable,str(dest/'verify.py')],capture_output=True,text=True)
    assert result.returncode!=0


def test_static_routes_do_not_expose_secrets(client):
    for path in ['/.env','/static/../.env','/static/%2e%2e/.env','/.data/asterisk.sqlite']:
        assert client.get(path).status_code==404
