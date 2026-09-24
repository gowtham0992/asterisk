import copy,json,subprocess,sys,stat
from pathlib import Path
import pytest
from app.probe_evidence import bundle,VERIFY
from app.receipt_view import render_receipt
from tests.test_researcher_handoff import investigation
from tests.test_primitives import FILES

@pytest.mark.parametrize('change',['empty','omit_result','omit_input','duplicate'])
def test_hash_verifier_rejects_incomplete_manifests(tmp_path,change):
    out=bundle(investigation()['result'],FILES,tmp_path/'receipt')
    p=out/'manifest.json';m=json.loads(p.read_text())
    if change=='empty':m['files']={}
    if change=='omit_result':del m['files']['result.json']
    if change=='omit_input':del m['files']['inputs/split.csv']
    p.write_text(json.dumps(m))
    if change=='duplicate':p.write_text('{"version":1,"files":{},"files":'+json.dumps(m['files'])+'}')
    r=subprocess.run([sys.executable,str(out/'verify.py')],capture_output=True,text=True)
    assert r.returncode!=0

@pytest.mark.parametrize('change',['verdict','count','confirmation','replay'])
def test_receipt_does_not_promote_inconsistent_retained_record(change):
    files=FILES
    if change=='confirmation':files={**FILES,'map.csv':'subject_id,image\nx,a\ny,b\nz,c\n'}
    r=investigation(files)['result']
    if change=='verdict':r['verdict']['verdict']='clear'
    if change=='count':r['primitive_measurements']['measurement-1']['output']['affected_test_rows']=0
    if change=='confirmation':r['binding_confirmation']['binding_hash']='wrong'
    if change=='replay':r['primitive_replays'][0]['record']['output']['shared_entities']=999
    page=render_receipt(r,files)
    assert 'The retained receipt is inconsistent.' in page
    assert '<h1>No recorded overlap within the confirmed binding.</h1>' not in page
    assert '<h1>Recorded identities appear on both sides.</h1>' not in page


def test_database_setup_does_not_chmod_existing_parent(tmp_path):
    from app.storage import prepare_database_path
    shared=tmp_path/'shared';shared.mkdir(mode=0o755)
    before=stat.S_IMODE(shared.stat().st_mode)
    prepare_database_path(shared/'app.sqlite')
    assert stat.S_IMODE(shared.stat().st_mode)==before
    private=tmp_path/'new-private'
    prepare_database_path(private/'app.sqlite')
    assert stat.S_IMODE(private.stat().st_mode)==0o700

@pytest.mark.parametrize('tamper',[False,True])
def test_installed_cli_recomputes_receipt_even_with_rehashed_manifest(tmp_path,tamper):
    import hashlib
    out=bundle(investigation()['result'],FILES,tmp_path/'receipt')
    if tamper:
        p=out/'result.json';r=json.loads(p.read_text());r['verdict']['verdict']='clear';p.write_text(json.dumps(r))
        m=json.loads((out/'manifest.json').read_text());m['files']['result.json']=hashlib.sha256(p.read_bytes()).hexdigest();(out/'manifest.json').write_text(json.dumps(m))
    run=subprocess.run([sys.executable,'-m','asterisk','verify',str(out)],cwd=Path(__file__).resolve().parents[1],capture_output=True,text=True)
    assert run.returncode==(1 if tamper else 0),run.stderr
    report=json.loads(run.stdout)
    assert report['byte_integrity'] is True
    assert report['matches'] is (not tamper)

@pytest.mark.parametrize('change',['coverage','witness','replay'])
def test_comparison_rejects_inconsistent_evidence_beyond_headline_counts(change):
    from app.receipt_comparison import compare_receipts
    a=investigation();b=copy.deepcopy(a)
    if change=='coverage':b['result']['primitive_measurements']['measurement-1']['output']['mapping_coverage']=0
    if change=='witness':b['result']['primitive_measurements']['measurement-1']['output']['witnesses']=[]
    if change=='replay':b['result']['primitive_replays'][0]['record']['output']['shared_entities']=999
    assert not compare_receipts(a,b)['available']
