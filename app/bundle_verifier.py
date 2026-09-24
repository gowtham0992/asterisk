"""Standalone byte/inventory verifier. Does not execute any bundled checker code."""
import hashlib
import json
import re
from pathlib import Path, PurePosixPath


def unique_object(pairs):
    value={}
    for key,item in pairs:
        if key in value:raise ValueError('Duplicate JSON key: '+key)
        value[key]=item
    return value


def read_json(path):
    if path.stat().st_size>64_000_000:raise ValueError('JSON artifact exceeds verification limit')
    return json.loads(path.read_bytes(),object_pairs_hook=unique_object)


def safe_path(root,name):
    if not isinstance(name,str):raise ValueError('Invalid artifact path')
    path=PurePosixPath(name)
    if not name or path.is_absolute() or '..' in path.parts or str(path)!=name or '\\' in name or any(ord(c)<32 for c in name):
        raise ValueError('Invalid artifact path')
    candidate=root/name
    if any(p.is_symlink() for p in [candidate,*candidate.parents] if p!=root and p.is_relative_to(root)):
        raise ValueError('Symlink artifact is not permitted')
    if not candidate.resolve().is_relative_to(root) or not candidate.is_file():raise ValueError('Missing or unsafe artifact: '+name)
    return candidate


def verify_bundle(directory):
    root=Path(directory).resolve()
    manifest=read_json(safe_path(root,'manifest.json'))
    entries=manifest.get('files') if isinstance(manifest,dict) else None
    if not isinstance(manifest,dict) or manifest.get('version')!=1 or not isinstance(entries,dict) or not entries or len(entries)>500:
        raise ValueError('Invalid or empty manifest')
    if not {'result.json','claim.txt','receipt.html','verify.py','README.txt'}<=entries.keys():
        raise ValueError('Required receipt artifacts are missing from the manifest')
    total=0
    for name,digest in entries.items():
        if name=='manifest.json' or not isinstance(digest,str) or not re.fullmatch('[0-9a-f]{64}',digest):raise ValueError('Invalid manifest digest')
        path=safe_path(root,name);total+=path.stat().st_size
        if total>128_000_000:raise ValueError('Bundle exceeds verification byte limit')
        h=hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda:stream.read(65536),b''):h.update(block)
        if h.hexdigest()!=digest:raise ValueError('Hash mismatch: '+name)
    result=read_json(root/'result.json')
    if not isinstance(result,dict):raise ValueError('Result must be an object')
    hashes=result.get('input_hashes')
    if not isinstance(hashes,dict) or not 1<=len(hashes)<=80:raise ValueError('Input inventory is missing or invalid')
    for name,digest in hashes.items():
        if not isinstance(name,str) or entries.get('inputs/'+name)!=digest:raise ValueError('Input is not bound by both result and manifest')
        safe_path(root,'inputs/'+name)
    if {n for n in entries if n.startswith('inputs/')}!={'inputs/'+n for n in hashes}:
        raise ValueError('Manifest input inventory differs from result')
    return result


if __name__=='__main__':
    try:verify_bundle(Path(__file__).resolve().parent)
    except (ValueError,OSError,TypeError,KeyError) as exc:raise SystemExit('FAILED: '+str(exc))
    print('PASS: required receipt artifacts and input hashes match. Byte consistency only; scientific correctness and authorship are not authenticated.')
