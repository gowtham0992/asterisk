"""Bake trusted measurement implementation into the existing scientific image."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'evaluation/probe-pilot'))
from common import credentials,DATA
from app.primitive_runtime import FILES,DRIVER,implementation_hash
from contree_sdk import ContreeSync
from contree_sdk.auth import IAMAuth
from contree_sdk.config import ContreeConfig
key,project=credentials();base=json.loads((DATA/'environment.json').read_text())['image']
client=ContreeSync(ContreeConfig(auth=IAMAuth(token=key,project_id=project),operation_timeout=150,transport_timeout=30))
files={'/opt/asterisk/app/'+n:(ROOT/'app'/n).read_bytes() for n in FILES}
files['/opt/asterisk/app/__init__.py']=b'';files['/opt/asterisk/primitive_main.py']=DRIVER.encode()
r=client.images.use(base).run('python',args=['-c',"import sys;sys.path.insert(0,'/opt/asterisk');from app.primitives import VERSION;print(VERSION)"],files=files,timeout=30,disposable=False).wait()
if r.exit_code:raise SystemExit('Primitive image failed validation.')
out={'image':str(r.uuid),'base_image':base,'implementation_hash':implementation_hash(),'version':r.stdout.strip()}
p=ROOT/'.data/primitive-pilot';p.mkdir(exist_ok=True);(p/'environment.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
