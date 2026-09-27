"""Fresh-process public-preview lifecycle, without inference or Sandbox calls."""
import json
import os
from pathlib import Path
import subprocess
import sys


SCRIPT = r'''
import json, sys
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

state_path = Path(sys.argv[2])
auth = ('reviewer', 'fictional-preview-password-only')
base = 'https://review.example.org'
headers = {'X-Asterisk-Request': '1', 'Origin': base}
with TestClient(app, base_url=base) as c:
    assert c.get('/healthz').status_code == 200
    assert c.get('/api/ladder/receipts').status_code == 401
    assert c.get('/static/ladder.html').status_code == 401
    assert c.get('/api/session', auth=('reviewer', 'wrong')).status_code == 401
    c.auth = auth
    if sys.argv[1] == 'create':
        from tests.test_ladder_receipts import payload
        response = c.get('/api/session')
        assert response.status_code == 200
        cookie = response.headers['set-cookie']
        assert 'Secure' in cookie and 'HttpOnly' in cookie and 'samesite=strict' in cookie.lower()
        body = payload()
        assert c.post('/api/ladder/receipts', json=body).status_code == 403
        assert c.post('/api/ladder/receipts', json=body,
                      headers={**headers, 'Origin': 'https://other.example.org'}).status_code == 403
        response = c.post('/api/ladder/receipts', json=body, headers=headers)
        assert response.status_code == 201, response.text
        record = response.json()
        state_path.write_text(json.dumps({'cookie': c.cookies.get('asterisk_session'), 'record': record}))
        state_path.chmod(0o600)
    else:
        state = json.loads(state_path.read_text())
        record = state['record']
        c.cookies.set('asterisk_session', state['cookie'], domain='review.example.org', path='/')
        rid = record['id']
        assert c.get('/api/ladder/receipts/'+rid).json() == record
        assert c.get('/api/ladder/receipts').json()[0]['id'] == rid
        response = c.get('/api/ladder/receipts/'+rid+'/export?format=json')
        assert response.json() == record
        assert response.headers['cache-control'] == 'no-store'
        html = c.get('/api/ladder/receipts/'+rid+'/export').text
        assert 'No Sandbox replay' in html and 'TCGA-AB-0001' in html
        with TestClient(app, base_url=base) as other:
            other.auth = auth
            other.get('/api/session')
            assert other.get('/api/ladder/receipts').json() == []
            assert other.get('/api/ladder/receipts/'+rid).status_code == 404
            assert other.get('/api/ladder/receipts/'+rid+'/export').status_code == 404
            assert other.delete('/api/ladder/receipts/'+rid, headers=headers).status_code == 404
        assert c.delete('/api/ladder/receipts/'+rid, headers=headers).status_code == 200
        assert c.get('/api/ladder/receipts/'+rid).status_code == 404
    assert c.get('/healthz', headers={'Host': 'unapproved.example.org'}).status_code == 400
print('public lifecycle phase passed')
'''


def test_public_ladder_survives_process_restart_and_preserves_owner_boundaries(tmp_path):
    root = Path(__file__).resolve().parents[1]
    env = {k: v for k, v in os.environ.items() if not k.startswith(('ASTERISK_', 'NEBIUS_'))}
    env.update(ASTERISK_PUBLIC='1', ASTERISK_ALLOWED_HOSTS='review.example.org',
               ASTERISK_PREVIEW_PASSWORD='fictional-preview-password-only',
               ASTERISK_DB=str(tmp_path/'preview.sqlite'))
    state = tmp_path/'session.json'
    for phase in ('create', 'reopen'):
        result = subprocess.run([sys.executable, '-c', SCRIPT, phase, str(state)],
                                cwd=root, env=env, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == 'public lifecycle phase passed'
    # Deletion removes both the receipt and its retained inputs from SQLite.
    import sqlite3
    with sqlite3.connect(tmp_path/'preview.sqlite') as db:
        assert db.execute('SELECT COUNT(*) FROM ladder_receipts').fetchone()[0] == 0
