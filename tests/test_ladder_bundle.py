import io
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from app.ladder_bundle import verify
from tests.test_ladder_receipts import save
from tests.test_api import client


def downloaded(client):
    record = save(client)
    response = client.get('/api/ladder/receipts/'+record['id']+'/export?format=zip')
    assert response.status_code == 200, response.text
    assert response.headers['content-type']=='application/zip'
    return record,response.content


def rewrite(data,change,rebuild_manifest=False):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        entries={n:z.read(n) for n in z.namelist()}
    change(entries)
    if rebuild_manifest:
        import hashlib
        entries['manifest.json']=json.dumps({n:hashlib.sha256(v).hexdigest() for n,v in entries.items() if n!='manifest.json'}).encode()
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w') as z:
        for n,v in entries.items():z.writestr(n,v)
    return out.getvalue()


def test_bundle_recomputes_after_saved_record_deleted_and_cli_is_offline(client,tmp_path):
    record,data=downloaded(client)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        meta=json.loads(z.read('bundle.json'));assert meta['inputs']
        assert all(n.endswith('.txt') for n in meta['inputs'].values())
        assert not any(n.endswith('.py') for n in z.namelist())
        assert 'separately' in z.read('README.txt').decode()
    client.delete('/api/ladder/receipts/'+record['id'],headers=__import__('tests.test_api',fromlist=['HEADERS']).HEADERS)
    path=tmp_path/'bundle.zip';path.write_bytes(data)
    assert verify(path)['finding']['status']=='violation'
    run=subprocess.run([sys.executable,'-m','asterisk','verify-ladder',str(path)],capture_output=True,text=True)
    assert run.returncode==0,run.stderr
    assert json.loads(run.stdout)['matches'] is True


def test_bundle_export_denies_other_owner(client):
    from fastapi.testclient import TestClient
    from app import main
    rid=save(client)['id']
    with TestClient(main.app) as other:
        other.get('/api/session')
        assert other.get('/api/ladder/receipts/'+rid+'/export?format=zip').status_code==404


@pytest.mark.parametrize('rehash',[False,True])
def test_tampered_verdict_refused_even_when_manifest_regenerated(client,tmp_path,rehash):
    _,data=downloaded(client)
    def tamper(entries):
        r=json.loads(entries['measurement.json']);r['result']['finding']['status']='held_out'
        entries['measurement.json']=json.dumps(r).encode()
    path=tmp_path/'bad.zip';path.write_bytes(rewrite(data,tamper,rehash))
    with pytest.raises(ValueError,match='hash mismatch|differs'):
        verify(path)


def test_wrong_engine_and_unexpected_archive_files_refused(client,tmp_path):
    _,data=downloaded(client)
    def engine(entries):
        m=json.loads(entries['bundle.json']);m['engine_files']['app/ladder.py']='0'*64
        entries['bundle.json']=json.dumps(m).encode()
    for change,reason in [(engine,'trusted'),(lambda e:e.update({'../attack.py':b'raise Exception()'}),'unexpected')]:
        path=tmp_path/'bad.zip';path.write_bytes(rewrite(data,change,True))
        with pytest.raises(ValueError,match=reason):verify(path)


def test_bundle_handles_partition_presentation_order_without_ignoring_counts(client,tmp_path):
    from tests.test_api import HEADERS
    folder=Path(__file__).resolve().parents[1]/'static/ladder-example'
    body={'spec':json.loads((folder/'spec.json').read_text()),'files':[{'name':n,'content':(folder/n).read_text()} for n in ('split.csv','subjects.csv','README.md')]}
    rid=save(client,body)['id']
    r=client.get('/api/ladder/receipts/'+rid+'/export?format=zip');assert r.status_code==200,r.text
    path=tmp_path/'example.zip';path.write_bytes(r.content);assert verify(path)['matches']
    def wrong_count(entries):
        v=json.loads(entries['measurement.json']);v['result']['review_context']['partitions'][0]['rows']+=1
        entries['measurement.json']=json.dumps(v).encode()
    path.write_bytes(rewrite(r.content,wrong_count,True))
    with pytest.raises(ValueError,match='differs'):verify(path)
