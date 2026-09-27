"""Recompute a ladder in a fresh Nebius Sandbox and require it to match the local measurement exactly.

The Sandbox receives the engine's own source (the frozen extraction executor, the overlap audit and the ladder
module) plus the spec and files as a gzip-compressed JSON file. It never receives credentials, model output or anything else.
A replay is evidence that the same code on the same inputs gives the same answer on independent infrastructure;
it is not tamper-proofing.
"""
import gzip
import hashlib
import json
from importlib.metadata import version
from pathlib import Path

from . import ladder
from .sandbox import IMAGE, SandboxError

ROOT = Path(__file__).resolve().parent.parent
IMPORTS = ('from .audit import AuditError, execute\n', 'from .preparation.review import executor\n')
RUNNER = '''
import json, sys, types

def load(name, source, inject=None):
    module = types.ModuleType(name)
    module.__dict__.update(inject or {})
    exec(compile(source, name + '.py', 'exec'), module.__dict__)
    sys.modules[name] = module
    return module

executor = load('executor', SOURCES['executor'])
audit = load('audit', SOURCES['audit'])
ladder = load('ladder', SOURCES['ladder'], {'executor': executor, 'AuditError': audit.AuditError, 'execute': audit.execute})
if len(sys.argv) > 1:
    import gzip
    with open(sys.argv[1], 'rb') as handle:
        payload = json.loads(gzip.decompress(handle.read()))
else:
    payload = json.load(sys.stdin)
print(json.dumps(ladder.measure(payload['spec'], payload['files'], payload.get('confirmed', [])), sort_keys=True))
'''


def sources():
    """The exact engine source the local process uses, with its two package-relative imports removed."""
    text = (ROOT / 'app' / 'ladder.py').read_text()
    for line in IMPORTS:
        if line not in text:
            raise SandboxError('The ladder engine changed shape; refusing to build a replay program.')
        text = text.replace(line, '')
    return {'executor': (ROOT / 'evaluation' / 'extraction-v1' / 'executor.py').read_text(),
            'audit': (ROOT / 'app' / 'audit.py').read_text(), 'ladder': text}


INPUT = '/tmp/asterisk-ladder-input.json.gz'


def run_remote(code, payload, key, project):
    """One disposable Sandbox run. Inputs go up as a gzip file: stdin is capped near 1 MB, benchmark metadata is not."""
    from contree_sdk import ContreeSync  # optional dependency; local installs never import it
    from contree_sdk.auth import IAMAuth
    from contree_sdk.config import ContreeConfig
    client = ContreeSync(ContreeConfig(auth=IAMAuth(token=key, project_id=project), operation_timeout=180, transport_timeout=60))
    result = client.images.use(IMAGE).run('python', args=['-c', code, INPUT], files={INPUT: gzip.compress(payload.encode(), 9)},
                                          timeout=120, disposable=True, truncate_output_at=4_000_000).wait()
    return {'exit_code': result.exit_code, 'stdout': result.stdout, 'truncated': result.result.truncated,
            'seconds': result.result.elapsed_time.total_seconds(), 'sdk_version': version('contree-sdk')}


def program():
    return 'SOURCES = ' + json.dumps(sources(), sort_keys=True) + '\n' + RUNNER


def canonical(result):
    return json.dumps(result, sort_keys=True)


def replay(spec, files, confirmed, key, project, run=run_remote):
    """Measure locally, recompute in a Sandbox, and return (result, provenance) only if they match exactly."""
    local = ladder.measure(spec, files, confirmed)
    if not key or not project:
        raise SandboxError('Sandbox credentials are missing. Configure the API key and project ID, then restart.')
    code = program()
    payload = json.dumps({'spec': spec, 'files': files, 'confirmed': list(confirmed)}, ensure_ascii=False)
    try:
        response = run(code, payload, key, project)
    except Exception:
        # SDK exceptions can contain request bodies or authentication details.
        raise SandboxError('The Sandbox did not return a result. Nothing was recorded; retry the replay.') from None
    if response['exit_code'] != 0 or response['truncated']:
        raise SandboxError('The Sandbox run failed or its output was cut off. Nothing was recorded; retry the replay.')
    if response['stdout'].strip() != canonical(local):
        raise SandboxError('The Sandbox result differs from the local measurement. Nothing was recorded.')
    sha = lambda text: hashlib.sha256(text.encode()).hexdigest()
    provenance = {'runtime': 'nebius-sandbox', 'image': IMAGE, 'sdk_version': response.get('sdk_version'),
                  'seconds': response.get('seconds'), 'exit_code': 0, 'matches_local': True,
                  'program_sha256': sha(code), 'payload_sha256': sha(payload), 'result_sha256': sha(canonical(local))}
    return local, provenance
