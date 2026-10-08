"""Data-only evidence handoff. Recompute using a separately trusted installation."""
import hashlib
import io
import json
import zipfile
from pathlib import Path

from .ladder import canonical, measure

ROOT = Path(__file__).resolve().parents[1]
ENGINE_FILES = ('app/ladder.py', 'app/audit.py', 'evaluation/extraction-v1/executor.py')
MAX_BYTES = 48_000_000


def engine_hashes():
    return {n: hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ENGINE_FILES}


def comparable(result):
    # Saved JSON sorts object keys: partition-map iteration can reorder this display table.
    # Preserve every entry and field; only the display order is immaterial.
    value = json.loads(canonical(result))
    if 'review_context' in value:
        value['review_context']['partitions'] = sorted(value['review_context']['partitions'], key=canonical)
    return canonical(value)


def build(record, readable):
    files = record['files']
    # A bundle pins code that actually reproduces the saved measurement, including legacy records.
    if comparable(measure(record['spec'], files, record['result'].get('confirmed_levels', []))) != comparable(record['result']):
        raise ValueError('The installed engine does not reproduce this saved measurement.')
    public = {k: v for k, v in record.items() if k != 'files'}
    entries = {'measurement.json': (json.dumps(public, indent=2, ensure_ascii=False)+'\n').encode(),
               'receipt.html': readable.encode()}
    inputs = {}
    for i, (name, text) in enumerate(sorted(files.items())):
        path = f'inputs/{i:03d}.txt'
        entries[path] = text.encode('utf-8')
        inputs[name] = path
    metadata = {'schema': 'asterisk-ladder-evidence/1', 'inputs': inputs,
                'engine_files': engine_hashes(),
                'trust': 'Unsigned data bundle. Hashes detect byte changes, not authenticity. Recorded confirmations are not newly verified.'}
    entries['bundle.json'] = (json.dumps(metadata, indent=2)+'\n').encode()
    entries['README.txt'] = (
        'ASTERISK EVIDENCE BUNDLE\n\n'
        'Contains ALL uploaded source files, including columns not sent to the model. Share only with authorized recipients.\n'
        'No executable code, credentials or verified reviewer identity is included. Original file names map to numbered UTF-8 inputs in bundle.json.\n\n'
        'Obtain and verify a matching Asterisk release separately. From that trusted installation directory run:\n'
        '  python -m asterisk verify-ladder /absolute/path/to/this-bundle.zip\n'
        'The command reads this ZIP without extracting or executing it, checks every manifest entry, requires matching installed engine hashes, '
        'and recomputes the complete measurement, witnesses and finding. Partition-table display order is ignored; every entry is checked. No API key or network is needed.\n'
        'Exit 0 means the recorded measurement matches, including a violation; exit 2 means verification failed.\n'
        'Recorded meaning confirmations are reused as historical inputs, not endorsed by this verifier.\n'
        'An unsigned bundle can be replaced with new inputs and hashes together. It cannot authenticate original data or cloud execution.\n'
    ).encode()
    entries['manifest.json'] = (json.dumps({n: hashlib.sha256(v).hexdigest() for n, v in entries.items()}, indent=2)+'\n').encode()
    if sum(map(len, entries.values())) > MAX_BYTES:
        raise ValueError('Evidence bundle exceeds the 48 MB uncompressed limit.')
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries.items():
            archive.writestr(name, data)
    return stream.getvalue()


def verify(path):
    path = Path(path)
    if path.stat().st_size > MAX_BYTES:
        raise ValueError('Evidence ZIP is too large.')
    try:
        with zipfile.ZipFile(path) as archive:
            info = archive.infolist()
            names = [x.filename for x in info]
            if not 5 <= len(info) <= 85 or len(set(names)) != len(names) or sum(x.file_size for x in info) > MAX_BYTES:
                raise ValueError('Invalid evidence inventory or uncompressed size.')
            if any(x.flag_bits & 1 or x.is_dir() for x in info):
                raise ValueError('Encrypted files and directories are not supported.')
            data = {x.filename: archive.read(x) for x in info}
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError) as exc:
        raise ValueError('Invalid evidence ZIP.') from exc
    manifest = json.loads(data['manifest.json'])
    if not isinstance(manifest, dict) or set(manifest) != set(data)-{'manifest.json'}:
        raise ValueError('Evidence manifest inventory differs.')
    if any(hashlib.sha256(data[n]).hexdigest() != h for n, h in manifest.items()):
        raise ValueError('Evidence manifest hash mismatch.')
    metadata = json.loads(data['bundle.json'])
    if metadata.get('schema') != 'asterisk-ladder-evidence/1' or metadata.get('engine_files') != engine_hashes():
        raise ValueError('Use a separately trusted Asterisk installation matching this bundle’s engine hashes.')
    mapping = metadata['inputs']
    if not isinstance(mapping, dict) or not 1 <= len(mapping) <= 80:
        raise ValueError('Invalid input mapping.')
    expected = {'bundle.json','manifest.json','measurement.json','receipt.html','README.txt'} | set(mapping.values())
    if set(data) != expected or len(set(mapping.values())) != len(mapping) or any(not isinstance(n,str) or not isinstance(p,str) or p != f'inputs/{i:03d}.txt' for i,(n,p) in enumerate(sorted(mapping.items()))):
        raise ValueError('Invalid input paths or unexpected bundle files.')
    files = {n: data[p].decode('utf-8') for n, p in mapping.items()}
    from .probes import validate_files
    validate_files(files)
    record = json.loads(data['measurement.json'])
    recomputed = measure(record['spec'], files, record['result'].get('confirmed_levels', []))
    if comparable(recomputed) != comparable(record['result']):
        raise ValueError('Recomputed measurement differs from the saved result.')
    return {'matches': True, 'byte_integrity': True, 'finding': recomputed['finding'],
            'scope': recomputed['scope'], 'inputs': len(files), 'engine_hashes_match': True,
            'meaning_confirmation': 'Historical inputs reused; not newly verified.',
            'authenticity': 'Unsigned: original data and cloud execution are not authenticated.',
            'mode': 'Local trusted installation; no network, extraction or bundled code execution.'}
