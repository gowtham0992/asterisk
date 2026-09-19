"""Bake the reviewed trusted source inventory into a separate v3 image."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'evaluation/probe-pilot'))
from common import credentials
from app.primitive_runtime import FILES,DRIVER,implementation_hash
from app.primitives import digest
from contree_sdk import ContreeSync
from contree_sdk.auth import IAMAuth
from contree_sdk.config import ContreeConfig
DATA=ROOT/'.data/primitive-v3';DATA.mkdir(exist_ok=True)
files={'/opt/asterisk/app/'+n:(ROOT/'app'/n).read_bytes() for n in FILES}
files.update({'/opt/asterisk/app/__init__.py':b'','/opt/asterisk/primitive_main.py':DRIVER.encode()})
inventory={n:{'bytes':len(v),'sha256':__import__('hashlib').sha256(v).hexdigest()} for n,v in files.items()}
(DATA/'upload-inventory.json').write_text(json.dumps(inventory,indent=2))
if '--execute' not in sys.argv:
 print(json.dumps(inventory,indent=2));raise SystemExit()
key,project=credentials();base=json.loads((ROOT/'.data/probe-pilot/environment.json').read_text())['image']
client=ContreeSync(ContreeConfig(auth=IAMAuth(token=key,project_id=project),operation_timeout=150,transport_timeout=30))
r=client.images.use(base).run('python',args=['-c',"import sys;sys.path.insert(0,'/opt/asterisk');from app.primitives import VERSION;print(VERSION)"],files=files,timeout=30,disposable=False).wait()
if r.exit_code:raise SystemExit('Bake import check failed')
env={'image':str(r.uuid),'base_image':base,'implementation_hash':implementation_hash(),'version':r.stdout.strip(),'inventory_hash':digest(inventory)}
with (DATA/('environment-'+str(r.uuid)+'.json')).open('x') as f:json.dump(env,f,indent=2)
(DATA/'environment.json').write_text(json.dumps(env,indent=2));print(json.dumps(env,indent=2))
