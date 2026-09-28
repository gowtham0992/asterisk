import sqlite3
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import pytest
from fastapi import HTTPException
from app.ladder_limits import Limits


def connect_at(path):
    def connect():
        return sqlite3.connect(path, timeout=10)
    return connect


def test_limits_persist_failed_operations_and_do_not_reset_with_new_sessions(tmp_path):
    connect = connect_at(tmp_path/'limit.db')
    limits = Limits(connect, session_cap=2, global_cap=3)
    with pytest.raises(RuntimeError):
        with limits.operation('a', 2):
            raise RuntimeError('provider failed after receiving request')
    with pytest.raises(HTTPException) as error:
        with Limits(connect, session_cap=2, global_cap=3).operation('a', 1): pass
    assert error.value.status_code == 429
    with limits.operation('b', 1): pass
    with pytest.raises(HTTPException) as error:
        with limits.operation('fresh-session', 1): pass
    assert error.value.status_code == 429


def test_one_inflight_operation_per_session(tmp_path):
    limits = Limits(connect_at(tmp_path/'limit.db'))
    with limits.operation('a', 1):
        with pytest.raises(HTTPException) as error:
            with limits.operation('a', 1): pass
        assert error.value.status_code == 429
        with limits.operation('b', 1): pass
    with limits.operation('a', 1): pass


def test_global_reservation_is_atomic_across_instances(tmp_path):
    connect = connect_at(tmp_path/'limit.db')
    Limits(connect).initialize()
    barrier = Barrier(2)
    def run(owner):
        barrier.wait()
        try:
            with Limits(connect, session_cap=1, global_cap=1).operation(owner, 1): return 'allowed'
        except HTTPException as exc:
            return exc.status_code
    with ThreadPoolExecutor(2) as pool:
        results=list(pool.map(run, ['a', 'b']))
    assert sorted(map(str,results)) == ['429', 'allowed']


def test_api_rejection_prevents_provider_calls_and_manual_measurement_still_works(tmp_path, monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.ladder_api import register
    from tests.test_ladder_proposal import CLAIM, FILES, spec
    from app.ladder import measure
    import json
    monkeypatch.setenv('NEBIUS_API_KEY', 'fake-key')
    monkeypatch.setenv('ASTERISK_LADDER_GLOBAL_DAILY_CALLS', '2')
    calls = []
    def completion(*args):
        def complete(*args):
            calls.append('model')
            return json.dumps({'status':'ladder','spec':spec()})
        return complete, {'calls':1,'total_tokens':10}
    def sandbox(*args):
        calls.append('sandbox')
        raise AssertionError('quota must stop this call')
    def connect():
        db=sqlite3.connect(tmp_path/'api.sqlite')
        db.row_factory=sqlite3.Row
        return db
    app=FastAPI()
    register(app, lambda request: request.headers.get('test-owner','a'), completion=completion,sandbox=sandbox,connect=connect)
    files=[{'name':n,'content':v} for n,v in FILES.items()]
    with TestClient(app) as c:
        proposed={'claim':CLAIM,'files':files,'documentation':['README.md']}
        assert c.post('/api/ladder/propose',json=proposed).status_code==200
        assert c.post('/api/ladder/propose',json=proposed).status_code==429
        body={'spec':spec(),'files':files}
        assert c.post('/api/ladder/replay',json=body,headers={'test-owner':'new-owner'}).status_code==429
        assert c.post('/api/ladder',json=body).status_code==200
        assert calls==['model']
