import io
import json
import subprocess
import sys
import zipfile
import pytest
from app import main, sandbox
from tests.test_api import client, HEADERS
from tests.test_revisions import proposed


def remote_replay(program, payload, key, project):
    assert key not in program and key not in payload
    assert project not in program and project not in payload
    completed = subprocess.run([sys.executable, '-c', program], input=payload, text=True, capture_output=True)
    return {'exit_code':completed.returncode, 'stdout':completed.stdout, 'truncated':False, 'seconds':0.01, 'sdk_version':'test'}


def setup_remote(client, monkeypatch):
    monkeypatch.setattr(main, 'EXECUTOR', 'nebius-sandbox')
    monkeypatch.setenv('NEBIUS_PROJECT_ID', 'test-project-secret-boundary')
    return proposed(client, monkeypatch)


def test_remote_result_export_and_retry_are_reproducible(client, monkeypatch, tmp_path):
    aid = setup_remote(client, monkeypatch)
    calls = []
    def run(*args):
        calls.append(1)
        return remote_replay(*args)
    monkeypatch.setattr(sandbox, 'run_remote', run)
    response = client.post(f'/api/audits/{aid}/execute', json={'remote':True,'confirm_upload':True}, headers=HEADERS)
    assert response.status_code == 200
    record = response.json()
    assert record['execution_provenance']['runtime'] == 'nebius-sandbox'
    assert record['execution_provenance']['local_cross_check'] is True
    assert 'sandbox_program' not in record
    assert client.post(f'/api/audits/{aid}/execute', json={'remote':True,'confirm_upload':True}, headers=HEADERS).json() == record
    assert len(calls) == 1
    archive = client.get(f'/api/audits/{aid}/export')
    with zipfile.ZipFile(io.BytesIO(archive.content)) as z:
        assert 'sandbox_program.py' in z.namelist()
        z.extractall(tmp_path)
    replay = subprocess.run([sys.executable, str(tmp_path/'verify.py')], capture_output=True, text=True)
    assert replay.returncode == 0, replay.stderr


@pytest.mark.parametrize('bad', [
    {'exit_code':1,'stdout':'private stderr'},
    {'truncated':True,'stdout':'{}'},
    {'stdout':'not json'},
    {'stdout':'{"status":"clear"}'},
])
def test_invalid_remote_output_never_completes_and_can_retry(client, monkeypatch, bad):
    aid = setup_remote(client, monkeypatch)
    monkeypatch.setattr(sandbox,'run_remote', lambda *args: {'exit_code':0,'stdout':'{}','truncated':False,'seconds':1,'sdk_version':'test',**bad})
    response = client.post(f'/api/audits/{aid}/execute', json={'remote':True,'confirm_upload':True}, headers=HEADERS)
    assert response.status_code == 502
    audit = client.get(f'/api/audits/{aid}').json()
    assert audit['state'] == 'review' and not audit.get('result')
    monkeypatch.setattr(sandbox, 'run_remote', remote_replay)
    assert client.post(f'/api/audits/{aid}/execute', json={'remote':True,'confirm_upload':True}, headers=HEADERS).status_code == 200


def test_sdk_failure_redacts_details_without_local_fallback(client, monkeypatch):
    aid = setup_remote(client, monkeypatch)
    def fail(*args):
        raise RuntimeError('test-key private input and provider request')
    monkeypatch.setattr(sandbox, 'run_remote', fail)
    response = client.post(f'/api/audits/{aid}/execute', json={'remote':True,'confirm_upload':True}, headers=HEADERS)
    assert response.status_code == 502 and 'test-key' not in response.text and 'private input' not in response.text
    assert client.get(f'/api/audits/{aid}').json()['state'] == 'review'


def test_concurrent_execution_is_rejected(client, monkeypatch):
    aid = setup_remote(client, monkeypatch)
    main.execution_lock.acquire()
    try:
        assert client.post(f'/api/audits/{aid}/execute', json={'remote':True,'confirm_upload':True}, headers=HEADERS).status_code == 409
    finally:
        main.execution_lock.release()


def test_remote_requires_explicit_upload_confirmation(client, monkeypatch):
    aid = setup_remote(client, monkeypatch)
    called = []
    monkeypatch.setattr(sandbox, 'run_remote', lambda *args: called.append(1))
    response = client.post(f'/api/audits/{aid}/execute', json={'remote':True}, headers=HEADERS)
    assert response.status_code == 422 and not called
    assert client.get(f'/api/audits/{aid}').json()['state'] == 'review'


def test_remote_is_not_the_default(client, monkeypatch):
    aid = setup_remote(client, monkeypatch)
    called = []
    monkeypatch.setattr(sandbox, 'run_remote', lambda *args: called.append(1))
    response = client.post(f'/api/audits/{aid}/execute', json={}, headers=HEADERS)
    assert response.status_code == 200 and not called
    assert response.json()['execution_provenance']['runtime'] == 'local'


def test_deleted_audit_is_not_restored_after_remote_completion(client, monkeypatch):
    aid = setup_remote(client, monkeypatch)
    def run(*args):
        result = remote_replay(*args)
        with main.connect() as db:
            db.execute('DELETE FROM audits WHERE id=?', (aid,))
        return result
    monkeypatch.setattr(sandbox, 'run_remote', run)
    response = client.post(f'/api/audits/{aid}/execute', json={'remote':True,'confirm_upload':True}, headers=HEADERS)
    assert response.status_code == 404
    assert client.get(f'/api/audits/{aid}').status_code == 404
