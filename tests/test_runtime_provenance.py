import copy,json,subprocess,sys
from pathlib import Path
import pytest
from app import primitive_runtime as runtime
from app.probe_evidence import bundle
from app.probes import sha
from tests.test_researcher_handoff import investigation
from tests.test_primitives import FILES


def test_new_receipt_exports_actual_runtime_and_old_receipt_does_not_invent_it(tmp_path):
    r=investigation()['result']
    r['runtime_sources']={'bootstrap.py':runtime.BOOTSTRAP,'primitive_main.py':runtime.DRIVER}
    dest=bundle(r,FILES,tmp_path/'new')
    assert (dest/'bootstrap.py').read_text()==runtime.BOOTSTRAP
    assert (dest/'primitive_main.py').read_text()==runtime.DRIVER
    del r['runtime_sources'];old=bundle(r,FILES,tmp_path/'old')
    assert not (old/'bootstrap.py').exists()
    assert 'not retained' in (old/'README.txt').read_text()


def test_image_configuration_rejects_missing_or_wrong_driver(tmp_path):
    resolve=runtime.configured_image
    d=tmp_path/'.data/primitive-v4';d.mkdir(parents=True)
    env={'image':'image','implementation_hash':runtime.implementation_hash(),'driver_sha256':sha(runtime.DRIVER)}
    for bad in [None,'0'*64]:
        (d/'environment.json').write_text(json.dumps({**env,'driver_sha256':bad}))
        with pytest.raises(ValueError):resolve(tmp_path,{})
    (d/'environment.json').write_text(json.dumps(env))
    assert resolve(tmp_path,{})=='image'
    with pytest.raises(ValueError):resolve(tmp_path,{'ASTERISK_PROBE_IMAGE':'override'})
    assert resolve(tmp_path,{'ASTERISK_PROBE_IMAGE':'override','ASTERISK_PROBE_DRIVER_SHA256':sha(runtime.DRIVER)})=='override'


def test_bootstrap_checks_actual_driver_before_execution(tmp_path):
    # Execute the exact preflight prefix without network namespace / setuid operations.
    prefix=runtime.BOOTSTRAP.split('libc=')[0]
    assert 'primitive_main.py' in prefix
    for driver,expected in [('wrong',79),(runtime.DRIVER,0)]:
        p=tmp_path/'primitive_main.py';p.write_text(driver)
        code=prefix.replace('/opt/asterisk/primitive_main.py',str(p)).replace('/work',str(tmp_path))
        r=subprocess.run([sys.executable,'-c',code],input='{}',text=True,capture_output=True)
        assert r.returncode==expected


def test_replay_verdict_rederived_and_confirmation_bound():
    from app.receipt_verification import verify_verdict
    r=investigation()['result'];records=r['primitive_measurements']
    assert verify_verdict(r,records,FILES)['matches']
    edited=copy.deepcopy(r);edited['verdict']['verdict']='clear'
    assert not verify_verdict(edited,records,FILES)['matches']
    clean={**FILES,'map.csv':'subject_id,image\nx,a\ny,b\nz,c\n'}
    r=investigation(clean)['result'];assert r['verdict']['verdict']=='clear'
    assert verify_verdict(r,r['primitive_measurements'],clean)['matches']
    r['binding_confirmation']['binding_hash']='wrong'
    assert not verify_verdict(r,r['primitive_measurements'],clean)['matches']


def test_export_rejects_runtime_provenance_mismatch(tmp_path):
    r=investigation()['result']
    r['runtime_sources']={'bootstrap.py':runtime.BOOTSTRAP,'primitive_main.py':runtime.DRIVER}
    r['primitive_measurements']['measurement-1']['execution']={'bootstrap_hash':'bad'}
    with pytest.raises(ValueError,match='provenance'):bundle(r,FILES,tmp_path/'bad')

