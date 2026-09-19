"""Verify a retained bundle and optionally replay successful probes in Nebius.

No generated code runs on this machine. Provide an extracted bundle directory.
Credentials stay on the host. An image override must provide the same pinned
Python/packages; deviations are explicitly recorded in the replay report.
"""
import argparse,hashlib,json,sys
from pathlib import Path
from common import ROOT,credentials
sys.path.insert(0,str(ROOT))
from app.probes import ProbeSandbox,validate_files
from app.primitive_runtime import PrimitiveSandbox
p=argparse.ArgumentParser();p.add_argument('bundle',type=Path);p.add_argument('--confirm-upload',action='store_true');p.add_argument('--image');args=p.parse_args()
root=args.bundle.resolve();manifest=json.loads((root/'manifest.json').read_text())
for name,digest in manifest['files'].items():
    target=(root/name).resolve()
    if not target.is_relative_to(root) or not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest()!=digest:raise SystemExit('Manifest mismatch: '+name)
print('All manifest bytes match. Hashes do not certify interpretation or authenticity.')
if not args.confirm_upload:raise SystemExit('Remote replay requires --confirm-upload to send retained inputs and probes to Nebius. No generated code has run locally.')
result=json.loads((root/'result.json').read_text());files={name.removeprefix('inputs/'):(root/name).read_text() for name in manifest['files'] if name.startswith('inputs/')};validate_files(files)
key,project=credentials();reports=[]
for id,record in result.get('primitive_measurements',{}).items():
    image=args.image or record['execution']['image']
    replay=PrimitiveSandbox(key,project,image).primitive(record['primitive'],record['arguments'],files)
    matches=not replay.get('execution_error') and all(replay.get(k)==record.get(k) for k in ('primitive','version','arguments','input_hashes','implementation_hash','output'))
    reports.append({'measurement_id':id,'image_override':args.image,'matches':matches,'record':replay})
for id,code in result['probes'].items():
    original=next((r for r in reversed(result['runs']) if r['probe_id']==id and r.get('exit_code')==0 and not r.get('truncated')),None)
    if original is None:continue
    image=args.image or original['image'];run=ProbeSandbox(key,project,image)(code,files)
    reports.append({'probe_id':id,'image_override':args.image,'bootstrap_changed':run.get('bootstrap_sha256')!=original.get('bootstrap_sha256'),'matches':run.get('exit_code')==0 and not run.get('truncated') and run.get('stdout')==original['stdout'],'run':run})
print(json.dumps(reports,indent=2))
raise SystemExit(0 if reports and all(r['matches'] for r in reports) else 1)
