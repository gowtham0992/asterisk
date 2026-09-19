"""Read the same saved v4 receipt through v4/v3/v4 APIs on a database copy."""
import json,os,sqlite3,subprocess,sys,tempfile,time,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'.data/primitive-v3/acceptance/frozen-source'
if len(sys.argv)!=2:raise SystemExit('Usage: python scripts/check_rollback.py SAVED_V4_RECEIPT_ID (requires the retained v3 source archive)')
ID=sys.argv[1]
started=time.monotonic();out=[]
with tempfile.TemporaryDirectory(prefix='asterisk-v4-rollback-') as directory:
 work=Path(directory);db=work/'copy.sqlite'
 with sqlite3.connect(ROOT/'.data/asterisk.sqlite') as source,sqlite3.connect(db) as target:source.backup(target)
 # Only read the copied session/receipt. Never expose its session cookie.
 code='''import json,os,sqlite3
from pathlib import Path
from fastapi.testclient import TestClient
from app import main
main.DB=Path(os.environ['QA_DB'])
with sqlite3.connect(main.DB) as d:uid=d.execute('SELECT owner FROM investigations WHERE id=?',(os.environ['QA_ID'],)).fetchone()[0]
with TestClient(main.app) as c:
 c.cookies.set('asterisk_session',uid)
 r=c.get('/api/investigations/'+os.environ['QA_ID']);r.raise_for_status()
 a=r.json();print(json.dumps({'id':a['id'],'state':a['state'],'verdict':a['result']['verdict']['verdict'],'engine':a['result']['engine_version']}))
'''
 old=work/'old';old.mkdir();shutil.copytree(OLD/'app',old/'app');shutil.copytree(ROOT/'static',old/'static')
 for label,cwd in [('v4',ROOT),('v3',old),('v4-restored',ROOT)]:
  env={**os.environ,'QA_DB':str(db),'QA_ID':ID}
  r=subprocess.run([str(ROOT/'.venv/bin/python'),'-c',code],cwd=cwd,env=env,text=True,capture_output=True)
  if r.returncode:raise RuntimeError(label+': '+r.stderr[-1000:])
  result=json.loads(r.stdout.strip());assert result['state']=='complete' and result['verdict']=='violation' and result['engine']=='primitive-v4';out.append({'code':label,**result})
record={'status':'pass','seconds':round(time.monotonic()-started,3),'checks':out,'scope':'Local code/database compatibility on SQLite backup. Does not test cloud proxy or deployment.'}
(ROOT/'.data/primitive-v4/rollback-check.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))
