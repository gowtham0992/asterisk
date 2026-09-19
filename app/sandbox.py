"""Run trusted checker source remotely; user artifacts remain JSON data."""
import hashlib
import json
from importlib.metadata import version

IMAGE = 'python:3.12-slim'
RUNNER = '''
import json, sys
payload = json.load(sys.stdin)
print(json.dumps(execute(payload['rule'], payload['files'])))
'''

class SandboxError(RuntimeError):
    pass


def run_remote(program, payload, key, project):
    # Optional dependency: local installations do not import the SDK.
    from contree_sdk import ContreeSync
    from contree_sdk.auth import IAMAuth
    from contree_sdk.config import ContreeConfig
    client = ContreeSync(ContreeConfig(auth=IAMAuth(token=key, project_id=project),
                                      operation_timeout=120, transport_timeout=20))
    image = client.images.use(IMAGE)
    result = image.run('python', args=['-c', program], stdin=payload,
                       timeout=30, disposable=True, truncate_output_at=262144).wait()
    return {'exit_code':result.exit_code, 'stdout':result.stdout,
            'truncated':result.result.truncated,
            'seconds':result.result.elapsed_time.total_seconds(),
            'sdk_version':version('contree-sdk')}


def execute_sandbox(rule, files, engine_source, expected, key, project):
    if not key or not project:
        raise SandboxError('Sandbox credentials are missing. Configure the API key and project ID, then restart.')
    program = engine_source + '\n' + RUNNER
    payload = json.dumps({'rule':rule, 'files':files}, ensure_ascii=False)
    try:
        response = run_remote(program, payload, key, project)
        if response['exit_code'] != 0 or response['truncated']:
            raise SandboxError('Sandbox execution failed or its output was incomplete. No result was saved. Retry the check.')
        result = json.loads(response['stdout'])
        if result != expected:
            raise SandboxError('Sandbox output did not match the local verification. No result was saved.')
    except SandboxError:
        raise
    except Exception:
        # SDK exceptions can contain request bodies or authentication details.
        raise SandboxError('Sandbox service did not return a verifiable result. No result was saved. Retry the check.') from None
    sha = lambda text: hashlib.sha256(text.encode()).hexdigest()
    provenance = {'runtime':'nebius-sandbox', 'image':IMAGE, 'sdk_version':response['sdk_version'],
                  'seconds':response['seconds'], 'exit_code':0, 'local_cross_check':True,
                  'program_sha256':sha(program), 'payload_sha256':sha(payload),
                  'stdout_sha256':sha(response['stdout'])}
    return result, provenance, program
