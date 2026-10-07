import base64
import sqlite3
from datetime import datetime, timezone, timedelta
import pytest
from fastapi import HTTPException
from app.release import ReleaseSettings
from app.ladder_limits import Limits
from tests.test_api import client


def header(name, password):
    return 'Basic '+base64.b64encode(f'{name}:{password}'.encode()).decode()


def test_judge_auth_requires_its_own_configured_secret(monkeypatch):
    monkeypatch.setenv('ASTERISK_PUBLIC', '1')
    monkeypatch.setenv('ASTERISK_PREVIEW_PASSWORD', 'r'*32)
    monkeypatch.setenv('ASTERISK_JUDGE_PASSWORD', 'j'*32)
    monkeypatch.setenv('ASTERISK_LADDER_JUDGE_UNTIL', (datetime.now(timezone.utc)+timedelta(days=30)).isoformat())
    settings = ReleaseSettings.from_env()
    assert settings.authorized(header('judge', 'j'*32))
    assert settings.is_judge(header('judge', 'j'*32))
    assert not settings.is_judge(header('reviewer', 'r'*32))
    assert not settings.authorized(header('judge', 'r'*32))
    monkeypatch.setenv('ASTERISK_JUDGE_PASSWORD', 'r'*32)
    with pytest.raises(RuntimeError): ReleaseSettings.from_env()


def test_judge_reserve_is_separate_persistent_and_not_daily(tmp_path, monkeypatch):
    monkeypatch.setenv('ASTERISK_LADDER_JUDGE_UNTIL', (datetime.now(timezone.utc)+timedelta(days=30)).isoformat())
    monkeypatch.setenv('ASTERISK_LADDER_JUDGE_TOTAL_CALLS', '3')
    connect = lambda: sqlite3.connect(tmp_path/'usage.db')
    limits = Limits(connect, session_cap=0, global_cap=0)
    with limits.operation('one', 2, judge=True): pass
    with Limits(connect, session_cap=0, global_cap=0).operation('two', 1, judge=True): pass
    with pytest.raises(HTTPException):
        with limits.operation('fresh', 1, judge=True): pass
    with pytest.raises(HTTPException):
        with limits.operation('reviewer', 1): pass
    assert limits.status('one', judge=True)['remaining_calls'] == 0


def test_expired_judge_reserve_cannot_call_provider(tmp_path, monkeypatch):
    monkeypatch.setenv('ASTERISK_LADDER_JUDGE_UNTIL', '2020-01-01T00:00:00+00:00')
    monkeypatch.setenv('ASTERISK_LADDER_JUDGE_TOTAL_CALLS', '100')
    limits = Limits(lambda: sqlite3.connect(tmp_path/'usage.db'))
    with pytest.raises(HTTPException):
        with limits.operation('one', 1, judge=True): raise AssertionError('must not execute')


def test_judge_cannot_use_legacy_provider_routes_or_spoof_role(client, monkeypatch):
    from app import main
    monkeypatch.setattr(main, 'RELEASE', ReleaseSettings(True, ('testserver',), 'r'*32, 'j'*32, datetime.now(timezone.utc)+timedelta(days=30)))
    client.base_url='https://testserver'
    assert client.get('/api/session', auth=('judge','j'*32)).status_code == 200
    assert client.get('/api/ladder/allowance', auth=('judge','j'*32)).status_code == 200
    assert client.post('/api/preparations', auth=('judge','j'*32), headers={'X-Asterisk-Request':'1'}, json={}).status_code == 403
    r=client.get('/api/ladder/allowance', auth=('reviewer','r'*32), headers={'X-Judge':'1'})
    assert r.json()['mode']=='preview'


def test_benchmark_projection_is_owner_gated_and_rejects_changed_bytes(client, tmp_path, monkeypatch):
    import json, hashlib
    monkeypatch.setenv('ASTERISK_BENCHMARK_DIR', str(tmp_path))
    folder=tmp_path/'wsibench';folder.mkdir()
    manifest={}
    for n in ['train.json','test.json']:
        content='[{"image":"fake-slide"}]\n';(folder/n).write_text(content)
        manifest[n]={'rows':1,'projection_sha256':hashlib.sha256(content.encode()).hexdigest()}
    (folder/'README.md').write_text('Fictional fixture.')
    (folder/'provenance.json').write_text(json.dumps(manifest))
    other=__import__('fastapi.testclient', fromlist=['TestClient']).TestClient(__import__('app.main',fromlist=['app']).app)
    assert other.get('/api/ladder/benchmark-inputs').status_code==401
    client.get('/api/session')
    r=client.get('/api/ladder/benchmark-inputs');assert r.status_code==200
    assert all(set(json.loads(f['content'])[0])=={'image'} for f in r.json()['files'] if f['name'].endswith('.json'))
    (folder/'train.json').write_text('changed')
    assert client.get('/api/ladder/benchmark-inputs').status_code==503


def test_expired_judge_login_cannot_read_receipts():
    settings=ReleaseSettings(True, ('testserver',), 'r'*32, 'j'*32, datetime.now(timezone.utc)-timedelta(seconds=1))
    assert not settings.authorized(header('judge','j'*32))
    assert settings.authorized(header('reviewer','r'*32))
