import base64
import pytest
from app import main
from app.release import ReleaseSettings
from tests.test_api import client

def test_public_configuration_fails_closed(monkeypatch):
    monkeypatch.setenv('ASTERISK_PUBLIC','1')
    monkeypatch.delenv('ASTERISK_PREVIEW_PASSWORD',raising=False)
    with pytest.raises(RuntimeError):ReleaseSettings.from_env()
    monkeypatch.setenv('ASTERISK_PREVIEW_PASSWORD','a'*24)
    monkeypatch.setenv('ASTERISK_ALLOWED_HOSTS','*')
    with pytest.raises(RuntimeError):ReleaseSettings.from_env()

def test_preview_gate_protects_api_and_exports_and_sets_secure_cookie(client,monkeypatch):
    monkeypatch.setattr(main,'RELEASE',ReleaseSettings(True,('testserver',),'a'*24))
    for path in ('/','/api/session','/api/investigations','/api/audits/unknown/export'):
        assert client.get(path).status_code==401
    assert client.get('/healthz').json()=={'status':'ok'}
    assert client.get('/api/session',headers={'Authorization':'Basic !!!'}).status_code==401
    assert client.get('/api/session',auth=('reviewer','wrong')).status_code==401
    response=client.get('/api/session',auth=('reviewer','a'*24))
    assert response.status_code==200
    assert 'Secure' in response.headers['set-cookie']
    assert 'HttpOnly' in response.headers['set-cookie']

def test_database_failure_is_readiness_failure(client,monkeypatch):
    def unavailable():raise main.sqlite3.OperationalError('private filesystem path')
    monkeypatch.setattr(main,'connect',unavailable)
    response=client.get('/healthz')
    assert response.status_code==503 and 'private' not in response.text

def test_release_archive_excludes_secrets_databases_and_symlinks(tmp_path):
    from scripts.package_release import package
    import zipfile
    (tmp_path/'app').mkdir();(tmp_path/'app/main.py').write_text('pass')
    (tmp_path/'.env').write_text('SECRET=never-publish')
    (tmp_path/'app/leak.py').symlink_to(tmp_path/'.env')
    (tmp_path/'.data').mkdir();(tmp_path/'.data/research.csv').write_text('private')
    with zipfile.ZipFile(package(tmp_path)) as z:
        assert sorted(z.namelist())==['asterisk/RELEASE-MANIFEST.json','asterisk/app/main.py']
        assert all(b'never-publish' not in z.read(n) for n in z.namelist())

def test_public_case_assets_and_current_docs_ship_without_arbitrary_json(tmp_path):
    from scripts.package_release import package
    import zipfile
    required=('static/reproductions/dermamnist-summary.json','docs/current-readiness.md',
              'docs/design/published-example-2026-09-23.md','docs/design/guided-example-2026-09-23.md')
    for name in required:
        p=tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('{}')
    (tmp_path/'static/reproductions/private-rows.json').write_text('do-not-ship')
    with zipfile.ZipFile(package(tmp_path)) as z:
        assert all('asterisk/'+n in z.namelist() for n in required)
        assert 'asterisk/static/reproductions/private-rows.json' not in z.namelist()


def test_ladder_runtime_assets_ship_but_private_run_records_do_not(tmp_path):
    from scripts.package_release import package
    import zipfile
    required=('static/ladders/index.json','static/ladders/experiment.json',
              'static/ladder-example/spec.json','static/ladder-example/subjects.csv',
              'static/ladder-example/README.md','static/ladder-example-propose/train.json',
              'examples/ladders/docs/esc50.md')
    for name in required:
        path=tmp_path/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('{}')
    (tmp_path/'static/ladders/private-rows.json').write_text('do-not-ship')
    runs=tmp_path/'evaluation/ladder-proposal-v5';runs.mkdir(parents=True)
    (runs/'raw-reply.json').write_text('do-not-ship')
    with zipfile.ZipFile(package(tmp_path)) as z:
        assert all('asterisk/'+name in z.namelist() for name in required)
        assert not any(b'do-not-ship' in z.read(name) for name in z.namelist())


def test_only_exact_readonly_public_assets_bypass_preview_auth(client, monkeypatch):
    monkeypatch.setattr(main, 'RELEASE', ReleaseSettings(True, ('testserver',), 'a'*24))
    for path in ('/public/', '/public/index.html', '/public/site.css', '/public/evidence.json'):
        response = client.get(path)
        assert response.status_code == 200, path
        assert 'set-cookie' not in response.headers
        assert response.headers['X-Content-Type-Options'] == 'nosniff'
    assert 'One patient. Two different slides.' in client.get('/public/').text
    for path in ('/public/private.txt', '/public/README.md', '/public/../api/session',
                 '/public/%2e%2e/api/session', '/api/session', '/static/ladder.html', '/static/product.html'):
        assert client.get(path).status_code == 401, path
    for method in ('post', 'put', 'delete'):
        assert getattr(client, method)('/public/').status_code == 401
