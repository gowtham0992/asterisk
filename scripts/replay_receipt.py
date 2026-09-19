"""Replay a v4 receipt remotely using installed trusted code, never uploaded Python."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'evaluation/probe-pilot'))
from common import credentials
from app.primitive_runtime import PrimitiveSandbox,implementation_hash
from app.probes import validate_files
if len(sys.argv)!=2:raise SystemExit('Usage: python scripts/replay_receipt.py EXTRACTED_RECEIPT_DIRECTORY')
root=Path(sys.argv[1]).resolve();manifest=json.loads((root/'manifest.json').read_text())
for name,digest in manifest['files'].items():
 p=(root/name).resolve()
 if not p.is_relative_to(root) or not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:raise SystemExit('Manifest mismatch: '+name)
result=json.loads((root/'result.json').read_text())
if result.get('engine_version')!='primitive-v4':raise SystemExit('Use the original release to replay historical results')
validate_files({n:'' for n in result['input_hashes']})
files={}
for n in result['input_hashes']:
 p=(root/'inputs'/n).resolve()
 if not p.is_relative_to(root/'inputs') or 'inputs/'+n not in manifest['files']:raise SystemExit('Input path is not retained by the manifest')
 files[n]=p.read_text()
validate_files(files)
key,project=credentials();env=json.loads((ROOT/'.data/primitive-v4/environment.json').read_text());runner=PrimitiveSandbox(key,project,env['image'])
rows=[]
for ident,record in result['primitive_measurements'].items():
 if record['primitive']!='entity_overlap' or record['implementation_hash']!=implementation_hash():raise SystemExit('Receipt implementation or category does not match installed v4 source')
 replay=runner.primitive(record['primitive'],record['arguments'],files)
 match=not replay.get('execution_error') and all(record.get(k)==replay.get(k) for k in ('primitive','version','arguments','input_hashes','implementation_hash','output'))
 rows.append({'measurement_id':ident,'matches':match})
print(json.dumps({'replays':rows,'meaning':'Repeatability only; scientific semantics remain human assumptions.'},indent=2))
if not rows or not all(r['matches'] for r in rows):raise SystemExit(1)
