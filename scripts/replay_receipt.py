"""Replay a v4 receipt remotely using installed trusted code, never uploaded Python."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'evaluation/probe-pilot'))
from common import credentials
from app.primitive_runtime import PrimitiveSandbox,implementation_hash,configured_image
from app.probes import validate_files
from app.receipt_verification import verify_verdict
if len(sys.argv)!=2:raise SystemExit('Usage: python scripts/replay_receipt.py EXTRACTED_RECEIPT_DIRECTORY')
from app.bundle_verifier import verify_bundle
root=Path(sys.argv[1]).resolve()
try:result=verify_bundle(root)
except (ValueError,OSError,TypeError,KeyError) as exc:raise SystemExit('Bundle verification failed: '+str(exc))
manifest=json.loads((root/'manifest.json').read_text())
if result.get('engine_version')!='primitive-v4':raise SystemExit('Use the original release to replay historical results')
validate_files({n:'' for n in result['input_hashes']})
files={}
for n in result['input_hashes']:
 p=(root/'inputs'/n).resolve()
 if not p.is_relative_to(root/'inputs') or 'inputs/'+n not in manifest['files']:raise SystemExit('Input path is not retained by the manifest')
 files[n]=p.read_bytes().decode('utf-8')
validate_files(files)
image=configured_image(ROOT)
if not image:raise SystemExit('No verified Sandbox image configured')
key,project=credentials();runner=PrimitiveSandbox(key,project,image)
rows=[];replayed={}
for ident,record in result['primitive_measurements'].items():
 if record['primitive']!='entity_overlap' or record['implementation_hash']!=implementation_hash():raise SystemExit('Receipt implementation or category does not match installed v4 source')
 replay=runner.primitive(record['primitive'],record['arguments'],files)
 match=not replay.get('execution_error') and all(record.get(k)==replay.get(k) for k in ('primitive','version','arguments','input_hashes','implementation_hash','output'))
 rows.append({'measurement_id':ident,'matches':match})
 replayed[ident]=replay
verdict=verify_verdict(result,replayed,files)
print(json.dumps({'replays':rows,'verdict':verdict,'meaning':'Repeatability only; scientific semantics remain human assumptions.'},indent=2))
if not rows or not all(r['matches'] for r in rows) or not verdict['matches']:raise SystemExit(1)
