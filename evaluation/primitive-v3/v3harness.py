"""Local protocol checks shared by the v2 freeze, inventory and runner commands."""
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / '.data/primitive-v3'
MODEL = 'nvidia/nemotron-3-super-120b-a12b'
RATES = {MODEL: (.30, .90)}
CATEGORIES = ('entity_overlap', 'checkpoint_selection')
SAFE_ID = re.compile(r'[A-Za-z0-9_-]{1,60}')
sys.path.insert(0, str(ROOT))


def sha(value):
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True,separators=(',',':'))


def now():
    return datetime.now(timezone.utc).isoformat()


def stamp(value):
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError('Use timestamps with an explicit UTC offset.')
    return parsed


def load_helper(name):
    """Import the preserved shared ledger/helpers without ambiguous module names."""
    path = ROOT / 'evaluation/probe-pilot' / (name + '.py')
    spec = importlib.util.spec_from_file_location('asterisk_v3_' + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def tracked(root=ROOT):
    # Snapshot all app modules, including future source-analysis/checkpoint helpers.
    paths = list((root / 'app').rglob('*.py'))
    paths += list((root / 'evaluation/primitive-v3').glob('*.py'))
    paths += [root / 'evaluation/primitive-v3/protocol.md']
    paths += list((root/'static').glob('*.js'))
    paths += [root / 'evaluation/probe-pilot' / name for name in ('budget.py', 'common.py')]
    return sorted(str(p.relative_to(root)) for p in paths)


def fingerprint(root=ROOT):
    return {name: sha((root / name).read_bytes()) for name in tracked(root)}


def runtime_state():
    from app.probes import SYSTEM, TOOLS, ENGINE_VERSION
    from app.primitive_runtime import FILES, SOURCES, implementation_hash
    from app.primitives import VERSION
    for filename in FILES:
        if (ROOT / 'app' / filename).read_text() != SOURCES[filename]:
            raise ValueError('Runtime sources changed after import; restart this command.')
    for name in ('source_analysis.py', 'checkpoint.py'):
        if (ROOT / 'app' / name).exists() and name not in FILES:
            raise ValueError(f'Trusted helper {name} is absent from the baked source inventory.')
    return {'engine_version': ENGINE_VERSION, 'primitive_version': VERSION,
            'implementation_hash': implementation_hash(), 'primitive_files': list(FILES),
            'prompt_hash': sha(SYSTEM), 'tools_hash': sha(canonical(TOOLS)),
            'prompt': SYSTEM, 'tools': TOOLS, 'model': MODEL,
            'trials': [1, 2], 'limits': {'tool_calls': 15, 'tokens': 400000, 'cumulative_estimated_usd': 10}}


def check(snapshot, root=ROOT):
    if snapshot['files'] != fingerprint(root):
        raise ValueError('Snapshot source changed; preserve this experiment and create a new one.')
    state = runtime_state()
    for key, value in state.items():
        if snapshot.get(key) != value:
            raise ValueError('Snapshot runtime changed: ' + key)
    stamp(snapshot['frozen_at'])


def snapshot(destination, environment, *, acceptance=False, twins=None, root=ROOT):
    state = runtime_state()
    if environment.get('implementation_hash') != state['implementation_hash']:
        raise ValueError('Bake a matching immutable primitive image first.')
    if not environment.get('image'):
        raise ValueError('Image ID is required.')
    if acceptance:
        if not twins or twins.get('implementation_hash') != state['implementation_hash']:
            raise ValueError('Development twins must match the current implementation.')
        if twins.get('status')!='pass' or len(twins.get('pairs',[]))!=10 or not all(p.get('passed') for p in twins['pairs']):
            raise ValueError('All ten Gate A pairs must pass before acceptance freeze.')
        behavior=json.loads((DATA/'gate-b.json').read_text())
        if behavior.get('status')!='pass' or behavior.get('implementation_hash')!=state['implementation_hash']:
            raise ValueError('Matching Gate B pass required before acceptance freeze.')

    result = {**state, 'frozen_at': now(), 'purpose': 'unseen_acceptance' if acceptance else 'known_regression',
              'image': environment['image'], 'files': fingerprint(root),
              'development_twins_hash': sha(canonical(twins)) if twins else None,
              'unseen_case_access': 'not selected, opened, or authored before freeze' if acceptance else 'not applicable'}
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    for name in result['files']:
        target = destination / 'frozen-source' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((root / name).read_bytes())
    (destination / 'snapshot.json').write_text(json.dumps(result, indent=2))
    return result


def read_inputs(variant, root):
    from app.probes import validate_files
    root = root.resolve()
    directory = (root / variant['directory']).resolve()
    if not directory.is_relative_to(root):
        raise ValueError('Case directory escapes manifest root.')
    inputs = {}
    for name, digest in variant['input_hashes'].items():
        path = (directory / name).resolve()
        if not path.is_relative_to(directory) or not path.is_file():
            raise ValueError('Input path escapes its case directory or is missing.')
        content = path.read_text()
        if sha(content) != digest:
            raise ValueError('Case input hash changed: ' + name)
        inputs[name] = content
    validate_files(inputs)
    return inputs


def validate(manifest, frozen, root, *, acceptance=True):
    cases = manifest['cases']
    if len(cases) != 12 or len({c['id'] for c in cases}) != 12:
        raise ValueError('Exactly twelve unique cases required.')
    if acceptance and manifest.get('freeze_hash') != sha(canonical(frozen)):
        raise ValueError('Cases refer to a different acceptance freeze.')
    if {c['category'] for c in cases} != set(CATEGORIES):
        raise ValueError('Both and only supported categories are required.')
    for category in CATEGORIES:
        clean='clear_pending_confirmation' if category=='entity_overlap' else 'clear'
        counts=Counter(c['expected']['verdict'] for c in cases if c['category']==category)
        if counts!=Counter({'violation':3,clean:1,'insufficient':2}):
            raise ValueError('Each category requires three violations, one scoped clean/pending control and two insufficient cases.')
    if acceptance and not manifest.get('authorship_constraint'):
        raise ValueError('Record the case authorship independence or its constraint explicitly.')
    identifiers = [case['id'] for case in cases] + [case['id'] + '-twin' for case in cases if 'twin' in case]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError('Case and twin IDs collide.')
    for case in cases:
        if not SAFE_ID.fullmatch(case['id']):
            raise ValueError('Unsafe case ID.')
        if acceptance:
            if not case.get('author') or stamp(case['authored_at']) <= stamp(frozen['frozen_at']):
                raise ValueError('Record an author and authorship timestamp after the freeze.')
            if stamp(case['authored_at']) > datetime.now(timezone.utc):
                raise ValueError('Authorship cannot be future dated.')
            for field in ('family', 'url', 'revision', 'license', 'transformations'):
                if not case['source'].get(field):
                    raise ValueError('Incomplete source provenance: ' + field)
            # Human attestation, not a claim that hashes establish non-exposure.
            if case['source'].get('previously_used') is not False:
                raise ValueError('Explicit unused-source attestation required for unseen cases.')
        variants = [case]
        if case['expected']['verdict'] == 'violation':
            twin = case.get('twin', {})
            if twin.get('expected', {}).get('verdict') != ('clear_pending_confirmation' if case['category']=='entity_overlap' else 'clear'):
                raise ValueError('Every violation requires a defect-removed clear twin.')
            variants.append(twin)
        elif 'twin' in case:
            raise ValueError('Only violations have twins in this protocol.')
        for variant in variants:
            requirements = variant['expected'].get('review_requires')
            if not isinstance(requirements, list) or not requirements or not all(isinstance(x, str) and x.strip() for x in requirements):
                raise ValueError('Every case and twin requires explicit review obligations.')
            read_inputs(variant, root)
        if len(variants) == 2 and case['input_hashes'] == case['twin']['input_hashes']:
            raise ValueError('Defect-removal twin must change the supplied evidence.')
    return cases


def jobs(cases):
    for case in cases:
        for trial in (1, 2):
            yield case, case, trial, case['id']
            if 'twin' in case:
                yield case, case['twin'], trial, case['id'] + '-twin'


def source_inventory():
    from app.primitive_runtime import FILES, DRIVER
    entries = [{'destination': '/opt/asterisk/app/' + n, 'source': 'app/' + n,
                'bytes': (ROOT / 'app' / n).stat().st_size, 'sha256': sha((ROOT / 'app' / n).read_bytes())} for n in FILES]
    entries += [{'destination': '/opt/asterisk/app/__init__.py', 'bytes': 0, 'sha256': sha('')},
                {'destination': '/opt/asterisk/primitive_main.py', 'bytes': len(DRIVER.encode()), 'sha256': sha(DRIVER)}]
    return {'purpose': 'Trusted primitive source upload to Nebius Sandboxes',
            'excludes': ['credentials', 'private case inputs', 'evaluation labels', 'research notebooks'], 'files': entries}


def case_inventory(manifest, frozen, root, *, acceptance=True):
    cases = validate(manifest, frozen, root, acceptance=acceptance)
    records = []
    for case in cases:
        for variant_id, variant in [(case['id'], case)] + ([(case['id'] + '-twin', case['twin'])] if 'twin' in case else []):
            files = read_inputs(variant, root)
            records.append({'id': variant_id, 'source': case['source'], 'files': [
                {'path': str(Path(variant['directory']) / n), 'bytes': len(content.encode()), 'sha256': sha(content)}
                for n, content in files.items()]})
    return {'mode': 'unseen_acceptance' if acceptance else 'known_regression',
            'manifest_hash': sha(canonical(manifest)), 'freeze_hash': sha(canonical(frozen)),
            'destinations': ['Nebius Token Factory inference', 'Nebius Sandboxes'],
            'payload': 'Claims, source inputs and primitive/exploration output; ground truth and review obligations excluded from model input.',
            'cases': records}


@contextmanager
def batch_lock(path=None):
    """One process owns the cumulative ledger; its workers share one Budget instance."""
    path = path or ROOT / '.data/probe-pilot/batch.lock'
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)
