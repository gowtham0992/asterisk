import json
import subprocess
import sys
from pathlib import Path
import pytest
from app.primitive_runtime import DRIVER, FILES
from app.primitives import measure
from tests.test_primitives import FILES as INPUTS, ARGS

@pytest.mark.parametrize('newline', ['\r\n', '\n'])
def test_baked_driver_preserves_original_input_bytes(tmp_path, newline):
    inputs=tmp_path/'inputs';inputs.mkdir()
    files={n:t.replace('\n',newline) for n,t in INPUTS.items()}
    for n,t in files.items():(inputs/n).write_bytes(t.encode())
    request=tmp_path/'request.json'
    request.write_text(json.dumps({'kind':'entity_overlap','arguments':ARGS,'input_names':list(files)}))
    root=Path(__file__).resolve().parents[1]
    driver=DRIVER.replace('/work/request.json',str(request)).replace('/work/inputs',str(inputs)).replace('/opt/asterisk',str(root))
    result=subprocess.run([sys.executable,'-c',driver],capture_output=True,text=True,check=True)
    actual=json.loads(result.stdout);expected=measure('entity_overlap',files,ARGS)
    assert actual['input_hashes']==expected['input_hashes']
    assert actual['output']==expected['output']


@pytest.mark.parametrize('tamper_verdict',[False,True])
def test_export_replay_preserves_crlf_bytes(tmp_path, monkeypatch, capsys,tamper_verdict):
    import hashlib
    import runpy
    import types
    from app import primitive_runtime as runtime
    files={n:t.replace('\n','\r\n') for n,t in INPUTS.items()}
    (tmp_path/'inputs').mkdir()
    record=measure('entity_overlap',files,ARGS)
    record['implementation_hash']=runtime.implementation_hash()
    result={'verdict':{'verdict':'violation'},'engine_version':'primitive-v4','input_hashes':record['input_hashes'],'primitive_measurements':{'m1':record}}
    if tamper_verdict:result['verdict']['verdict']='clear'
    (tmp_path/'result.json').write_text(json.dumps(result))
    for n,t in files.items():(tmp_path/'inputs'/n).write_bytes(t.encode())
    for name in ['claim.txt','receipt.html','verify.py','README.txt']:(tmp_path/name).write_text('Synthetic CLI test artifact')
    retained=['claim.txt','receipt.html','verify.py','README.txt','result.json']+['inputs/'+n for n in files]
    (tmp_path/'manifest.json').write_text(json.dumps({'version':1,'files':{n:hashlib.sha256((tmp_path/n).read_bytes()).hexdigest() for n in retained}}))
    class Runner:
        def __init__(self,*args):pass
        def primitive(self,kind,args,actual):
            assert actual==files
            return record
    common=types.ModuleType('common');common.credentials=lambda:('test-key','test-project')
    monkeypatch.setitem(sys.modules,'common',common)
    monkeypatch.setenv('ASTERISK_PROBE_IMAGE','test-image')
    monkeypatch.setenv('ASTERISK_PROBE_DRIVER_SHA256',hashlib.sha256(runtime.DRIVER.encode()).hexdigest())
    monkeypatch.setattr(runtime,'PrimitiveSandbox',Runner)
    monkeypatch.setattr(sys,'argv',['replay_receipt.py',str(tmp_path)])
    script=str(Path(__file__).resolve().parents[1]/'scripts/replay_receipt.py')
    if tamper_verdict:
        with pytest.raises(SystemExit) as caught:runpy.run_path(script,run_name='__main__')
        assert caught.value.code==1
    else:runpy.run_path(script,run_name='__main__')
    assert json.loads(capsys.readouterr().out)['replays']==[{'measurement_id':'m1','matches':True}]
