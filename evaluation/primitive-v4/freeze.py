"""Freeze the entire allowlisted product; preserve old snapshots and verify current bytes."""
import argparse,datetime,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from app.primitive_runtime import FILES,implementation_hash
from scripts.package_release import release_files
from scripts.build_review_packet import permitted

def sha(data):return hashlib.sha256(data).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()
def inventory(root):
    result={}
    for p in release_files(root):
        name=p.relative_to(root).as_posix();permitted(name)
        if p.is_symlink():raise ValueError('Symlinks cannot be frozen')
        result[name]=sha(p.read_bytes())
    return result

def freeze(root,out):
    root=Path(root).resolve();out=Path(out).resolve()
    out.relative_to(root)  # Validate before creating any snapshot.
    image=json.loads((root/'.data/primitive-v4/environment.json').read_text())
    disk_hash=sha(json.dumps({n:sha((root/'app'/n).read_bytes()) for n in FILES},sort_keys=True).encode())
    if image['implementation_hash']!=disk_hash or disk_hash!=implementation_hash():raise ValueError('Running trusted code, source and image must match before freezing')
    files=inventory(root);superseded=[]
    for p in sorted((root/'.data/primitive-v4').glob('freeze*/snapshot.json')):
        prior=json.loads(p.read_text());superseded.append({'path':str(p.relative_to(root)),'snapshot_hash':sha(canonical(prior)),'reason':'Earlier product version; preserved unchanged, not the current release.'})
    snapshot={'version':'primitive-v4-release-rc2','frozen_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'implementation_hash':disk_hash,'image':image['image'],'files':files,'purpose':'Feature-frozen entity-only product for human sessions and submission preparation; not an acceptance pass.','new_cases_authored':False,'v3_acceptance':'failed; never relabeled','supersedes':superseded}
    out.mkdir(parents=True,exist_ok=False)
    for name in files:
        target=out/'source'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((root/name).read_bytes())
    (out/'snapshot.json').write_text(json.dumps(snapshot,indent=2));digest=sha(canonical(snapshot));(out/'snapshot.sha256').write_text(digest+'\n')
    verify(root,out)
    (root/'.data/primitive-v4/current-freeze.json').write_text(json.dumps({'path':str(out.relative_to(root)),'snapshot_hash':digest,'implementation_hash':disk_hash,'image':image['image']},indent=2))
    return digest

def verify(root,out):
    root=Path(root).resolve();out=Path(out).resolve();s=json.loads((out/'snapshot.json').read_text());digest=sha(canonical(s))
    if digest!=(out/'snapshot.sha256').read_text().strip():raise ValueError('Snapshot hash mismatch')
    if inventory(root)!=s['files']:raise ValueError('Current release differs from freeze')
    for name,h in s['files'].items():
        permitted(name)
        if sha((out/'source'/name).read_bytes())!=h:raise ValueError('Frozen source changed')
    image=json.loads((root/'.data/primitive-v4/environment.json').read_text())
    if image['implementation_hash']!=s['implementation_hash'] or image['image']!=s['image'] or implementation_hash()!=s['implementation_hash']:raise ValueError('Running image/source mismatch')
    return digest

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--verify',action='store_true');a=p.parse_args()
    print(verify(ROOT,a.output) if a.verify else freeze(ROOT,a.output))
