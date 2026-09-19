"""Prepare an immutable remote environment without research inputs or keys."""
import json,time
from common import DATA,credentials
from contree_sdk import ContreeSync
from contree_sdk.auth import IAMAuth
from contree_sdk.config import ContreeConfig
key,project=credentials()
client=ContreeSync(ContreeConfig(auth=IAMAuth(token=key,project_id=project),operation_timeout=600,transport_timeout=30))
packages=['numpy==2.2.6','pandas==2.2.3','scipy==1.15.3','scikit-learn==1.6.1']
start=time.monotonic()
try:
    image=client.images.use('python:3.12-slim').run('python',args=['-m','pip','install','--no-cache-dir',*packages],timeout=300,disposable=False,truncate_output_at=12000).wait()
    if image.exit_code:raise RuntimeError('Package installation failed')
    check=image.run('python',args=['-c','import sys,numpy,pandas,scipy,sklearn,json;print(json.dumps(dict(python=sys.version,numpy=numpy.__version__,pandas=pandas.__version__,scipy=scipy.__version__,sklearn=sklearn.__version__)))'],timeout=30).wait()
    if check.exit_code:raise RuntimeError('Import check failed')
    result={'image':str(image.uuid),'base':'python:3.12-slim','packages':packages,'versions':json.loads(check.stdout),'seconds':time.monotonic()-start}
    DATA.mkdir(parents=True,exist_ok=True);(DATA/'environment.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result),flush=True)
except Exception as exc:
    print(json.dumps({'error_type':type(exc).__name__}),flush=True);raise SystemExit(1)
