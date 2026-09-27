"""The ladder chain over HTTP with fake Token Factory and Sandbox functions: no network, no credits."""
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import ladder_api
from app.sandbox import SandboxError
from tests.test_ladder_proposal import CLAIM, FILES, spec
from tests.test_ladder_sandbox import local_python
from app import ladder_sandbox

UPLOAD = [{'name': n, 'content': c} for n, c in FILES.items()]
BODY = {'claim': CLAIM, 'files': UPLOAD, 'documentation': ['README.md'], 'share_examples': [['train.json', 'image']]}


def client(replies=None, sandbox=None, monkeypatch=None):
    calls = []

    def completion(model, key):
        usage = {'calls': 0, 'total_tokens': 0}

        def complete(messages, maximum, timeout):
            usage['calls'] += 1
            usage['total_tokens'] += 100
            calls.append((model, messages))
            return replies.pop(0)
        return complete, usage
    app = FastAPI()
    ladder_api.register(app, lambda request: 'owner', completion=completion,
                        sandbox=sandbox or (lambda s, f, c, k, p: ladder_sandbox.replay(s, f, c, k, p, run=local_python)))
    return TestClient(app), calls


def test_preview_shows_exactly_what_would_be_sent_and_calls_nothing():
    c, calls = client(replies=[])
    r = c.post('/api/ladder/preview', json=BODY)
    assert r.status_code == 200 and calls == []
    body = r.json()
    assert body['provider'] == 'Nebius Token Factory' and body['model_name'] == 'Nemotron 3 Super'
    assert body['messages'][0]['content'] == __import__('app.ladder_proposal', fromlist=['x']).SYSTEM_V4
    assert '61' not in json.dumps(body['messages'])  # the unapproved age column's values never leave
    assert c.post('/api/ladder/preview', json={**BODY, 'model': 'gpt-4o'}).status_code == 422


def test_propose_repairs_once_then_returns_a_validated_ladder(monkeypatch):
    monkeypatch.setenv('NEBIUS_API_KEY', 'test-key')
    c, calls = client(replies=['{"status":"ladder"}', json.dumps({'status': 'ladder', 'spec': spec()})])
    r = c.post('/api/ladder/propose', json={**BODY, 'model': 'nvidia/Nemotron-3-Ultra-550b-a55b'})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body['proposal']['spec']['claim']['level'] == 'patient' and body['calls'] == 2
    assert [a['error'] is None for a in body['attempts']] == [False, True]
    assert calls[0][0] == 'nvidia/Nemotron-3-Ultra-550b-a55b' and body['model_name'] == 'Nemotron 3 Ultra'


def test_propose_reports_an_unusable_reply_without_echoing_it(monkeypatch):
    monkeypatch.setenv('NEBIUS_API_KEY', 'test-key')
    c, _ = client(replies=['nonsense', 'still nonsense'])
    r = c.post('/api/ladder/propose', json=BODY)
    assert r.status_code == 422 and 'after one repair' in r.json()['detail'] and 'nonsense' not in r.json()['detail']
    monkeypatch.delenv('NEBIUS_API_KEY')
    assert client(replies=[])[0].post('/api/ladder/propose', json=BODY).status_code == 503


def test_replay_returns_the_sandbox_matched_result_and_hides_failures(monkeypatch):
    c, _ = client(replies=[])
    payload = {'spec': spec(), 'files': UPLOAD, 'confirmed': ['patient']}
    monkeypatch.setenv('NEBIUS_PROJECT_ID', 'project')
    monkeypatch.setenv('NEBIUS_API_KEY', 'key')
    r = c.post('/api/ladder/replay', json=payload)
    assert r.status_code == 200, r.text
    assert r.json()['provenance']['matches_local'] is True and r.json()['result']['confirmed_levels'] == ['patient']

    def broken(*args):
        raise SandboxError('The Sandbox did not return a result. Nothing was recorded; retry the replay.')
    bad, _ = client(replies=[], sandbox=broken)
    r = bad.post('/api/ladder/replay', json=payload)
    assert r.status_code == 502 and 'Nothing was recorded' in r.json()['detail']
