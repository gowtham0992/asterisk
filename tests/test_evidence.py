import hashlib
import io
import json
import subprocess
import sys
import zipfile
import pytest
from app import main
from tests.test_api import client, HEADERS
from tests.test_revisions import proposed


def completed(client, monkeypatch):
    aid=proposed(client,monkeypatch)
    client.post('/api/audits/'+aid+'/execute',json={},headers=HEADERS)
    return aid


def unpack(client, aid, dest):
    response=client.get('/api/audits/'+aid+'/export')
    assert response.status_code==200
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:z.extractall(dest)


def test_export_retains_execution_checker_after_application_upgrade(client,monkeypatch,tmp_path):
    original=main.ENGINE_SOURCE
    aid=completed(client,monkeypatch)
    monkeypatch.setattr(main,'ENGINE_SOURCE','# hypothetical future checker')
    monkeypatch.setattr(main,'ENGINE_SHA256','future')
    unpack(client,aid,tmp_path)
    assert (tmp_path/'audit.py').read_text()==original
    report=json.loads((tmp_path/'report.json').read_text())
    assert report['execution_provenance']['capture']=='at_execution'
    assert report['execution_provenance']['engine_sha256']==hashlib.sha256(original.encode()).hexdigest()
    replay=subprocess.run([sys.executable,str(tmp_path/'verify.py')],capture_output=True,text=True)
    assert replay.returncode==0


@pytest.mark.parametrize('filename',['audit.py','rule.json','report.json'])
def test_manifest_detects_changes_that_do_not_change_counts(client,monkeypatch,tmp_path,filename):
    aid=completed(client,monkeypatch);unpack(client,aid,tmp_path)
    p=tmp_path/filename;p.write_text(p.read_text()+'\n')
    replay=subprocess.run([sys.executable,'-O',str(tmp_path/'verify.py')],capture_output=True,text=True)
    assert replay.returncode!=0 and 'integrity check failed' in replay.stderr


def test_replay_result_check_remains_active_with_python_optimization(client,monkeypatch,tmp_path):
    aid=completed(client,monkeypatch);unpack(client,aid,tmp_path)
    p=tmp_path/'report.json';report=json.loads(p.read_text());report['result']['shared_entities']=999;p.write_text(json.dumps(report))
    manifest_path=tmp_path/'manifest.json';manifest=json.loads(manifest_path.read_text())
    manifest['files']['report.json']=hashlib.sha256(p.read_bytes()).hexdigest();manifest_path.write_text(json.dumps(manifest))
    replay=subprocess.run([sys.executable,'-O',str(tmp_path/'verify.py')],capture_output=True,text=True)
    assert replay.returncode!=0 and 'differs from the recorded result' in replay.stderr


def make_legacy(aid):
    with main.connect() as db:
        row=db.execute('SELECT payload FROM audits WHERE id=?',(aid,)).fetchone();audit=json.loads(row['payload'])
        audit.pop('engine_source');audit.pop('execution_provenance')
        db.execute('UPDATE audits SET payload=? WHERE id=?',(json.dumps(audit),aid))


def test_legacy_export_discloses_revalidation_without_rewriting_history(client,monkeypatch,tmp_path):
    aid=completed(client,monkeypatch);make_legacy(aid)
    unpack(client,aid,tmp_path)
    report=json.loads((tmp_path/'report.json').read_text())
    assert report['execution_provenance']['capture']=='legacy_revalidated_at_export'
    assert 'execution_provenance' not in client.get('/api/audits/'+aid).json()


def test_incompatible_legacy_result_cannot_export_current_checker(client,monkeypatch):
    aid=completed(client,monkeypatch);make_legacy(aid)
    monkeypatch.setattr(main,'execute',lambda *args:{'status':'different'})
    assert client.get('/api/audits/'+aid+'/export').status_code==409
