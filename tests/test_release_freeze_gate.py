import json,zipfile
import pytest
from tests.test_api import client,HEADERS,create
from app.examples import example

def test_legacy_default_blocks_writes_examples_but_keeps_history(client,monkeypatch):
    monkeypatch.setenv('ASTERISK_LEGACY_AUDITS','1');aid=create(client)
    monkeypatch.delenv('ASTERISK_LEGACY_AUDITS',raising=False)
    assert client.post('/api/audits',json=example(),headers=HEADERS).status_code==404
    for suffix in ('propose','execute','with-inputs','with-rule'):
        assert client.post('/api/audits/'+aid+'/'+suffix,json={},headers=HEADERS).status_code==404
    assert client.delete('/api/audits/'+aid,headers=HEADERS).status_code==404
    assert client.get('/api/examples/overlap').status_code==404
    assert client.get('/api/audits/'+aid).status_code==200
    assert client.get('/api/audits/'+aid+'/inputs').status_code==200
    assert client.get('/api/session').json()['legacy_audits_enabled'] is False
    assert client.get('/api/session').json()['model']=='nvidia/nemotron-3-super-120b-a12b'
    monkeypatch.setenv('ASTERISK_LEGACY_AUDITS','true')
    assert client.post('/api/audits',json=example(),headers=HEADERS).status_code==404


def test_packet_uses_only_release_bytes_and_tests_elsewhere(tmp_path):
    from scripts.package_release import package
    from scripts.build_review_packet import build_packet
    source=tmp_path/'project';source.mkdir();(source/'app').mkdir();(source/'app/main.py').write_text('pass\n')
    release=package(source)
    def testing(scratch):
        (scratch/'.data').mkdir();(scratch/'.data/asterisk.sqlite').write_text('private test state')
        (scratch/'.env').write_text('SECRET=must-not-ship')
        (scratch/'app/main.py').write_text('test mutated source')
        return {'returncode':0,'output':'synthetic packaging test'}
    target=tmp_path/'review.zip';build_packet(release,target,tester=testing)
    with zipfile.ZipFile(target) as z:
        assert z.read('source/app/main.py')==b'pass\n'
        assert not any('.data' in n or n.endswith('.env') or '__pycache__' in n for n in z.namelist())
        assert all(b'must-not-ship' not in z.read(n) for n in z.namelist())
    # A manifest is not permission to export hidden runtime state.
    import hashlib
    bad=tmp_path/'bad.zip'
    with zipfile.ZipFile(bad,'w') as z:
        z.writestr('asterisk/.data/hidden.py','private')
        z.writestr('asterisk/RELEASE-MANIFEST.json',json.dumps({'.data/hidden.py':hashlib.sha256(b'private').hexdigest()}))
    with pytest.raises(ValueError,match='Forbidden'):build_packet(bad,tmp_path/'bad-review.zip',tester=testing)


def test_product_freeze_covers_cli_docs_and_refuses_drift(tmp_path,monkeypatch):
    import importlib.util,shutil
    from pathlib import Path
    from app.primitive_runtime import FILES,implementation_hash
    root=Path(__file__).parents[1]
    spec=importlib.util.spec_from_file_location('product_freeze',root/'evaluation/primitive-v4/freeze.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    (tmp_path/'app').mkdir()
    for name in FILES:shutil.copyfile(root/'app'/name,tmp_path/'app'/name)
    (tmp_path/'asterisk.py').write_text('pass\n');(tmp_path/'README.md').write_text('Frozen contract')
    d=tmp_path/'.data/primitive-v4';d.mkdir(parents=True);(d/'environment.json').write_text(json.dumps({'image':'test-only','implementation_hash':implementation_hash()}))
    out=d/'freeze-rc1';monkeypatch.chdir(tmp_path);digest=m.freeze(tmp_path,Path('.data/primitive-v4/freeze-rc1'))
    assert m.verify(tmp_path,out)==digest
    snap=json.loads((out/'snapshot.json').read_text());assert {'asterisk.py','README.md'}<=snap['files'].keys()
    (tmp_path/'asterisk.py').write_text('changed')
    with pytest.raises(ValueError,match='differs'):m.verify(tmp_path,out)
    with pytest.raises(FileExistsError):m.freeze(tmp_path,out)
