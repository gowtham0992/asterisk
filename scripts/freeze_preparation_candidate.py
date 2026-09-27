"""Freeze preparation source recursively without copying runtime data or credentials."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUFFIXES = {'.py', '.js', '.mjs', '.css', '.html', '.md', '.sh'}
RUNTIME_FILES = ('evaluation/extraction-v1/executor.py',
                 'evaluation/extraction-v2/proposal.py',
                 'evaluation/extraction-v3/proposal.py')


def sources(root):
    paths = set()
    for folder in ('app', 'static', 'scripts', 'tests'):
        for path in (root / folder).rglob('*'):
            if path.suffix not in SUFFIXES or not path.is_file():
                continue
            if path.is_symlink() or any(p.is_symlink() for p in path.parents if p != root):
                raise ValueError('Refusing symlink in source: ' + str(path))
            if '__pycache__' not in path.parts:
                paths.add(path)
    for name in ('requirements.txt', 'requirements.lock.txt', 'requirements-sandbox.txt',
                 'asterisk.py', 'evaluation/real-preparation-v1/PROTOCOL.md') + RUNTIME_FILES:
        path = root / name
        if path.is_symlink() or not path.is_file():
            raise ValueError('Missing or unsafe required source: ' + name)
        paths.add(path)
    return sorted(paths)


def freeze(root, destination):
    # Read everything before creating output; never overwrite an earlier snapshot.
    contents = {p.relative_to(root).as_posix(): p.read_bytes() for p in sources(root)}
    hashes = {name: hashlib.sha256(data).hexdigest() for name, data in contents.items()}
    digest = hashlib.sha256(json.dumps(hashes, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    destination.mkdir(parents=True, exist_ok=False)
    for name, data in contents.items():
        target = destination / 'source' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    manifest = {'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'classification': 'candidate freeze before fresh real-case authorship; not acceptance',
                'snapshot_hash': digest, 'source_hashes': hashes}
    (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, required=True)
    args = parser.parse_args()
    result = freeze(ROOT, args.destination)
    print(json.dumps({'files': len(result['source_hashes']), 'snapshot_hash': result['snapshot_hash']}))
