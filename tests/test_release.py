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
