"""One disposable Nebius Python run on inline synthetic data; no file uploads."""
import hashlib
import json
import os
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from contree_sdk import ContreeSync
from contree_sdk.auth import IAMAuth
from contree_sdk.config import ContreeConfig

ROOT = Path(__file__).resolve().parent.parent
values = {}
for line in (ROOT / '.env').read_text().splitlines():
    if '=' in line and not line.lstrip().startswith('#'):
        key, value = line.split('=', 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
for key in ('NEBIUS_API_KEY', 'NEBIUS_PROJECT_ID', 'NEBIUS_AI_PROJECT'):
    if key in os.environ:
        values[key] = os.environ[key]
key = values.get('NEBIUS_API_KEY')
project = values.get('NEBIUS_PROJECT_ID') or values.get('NEBIUS_AI_PROJECT')
if not key or not project:
    raise SystemExit('Set the API key and project ID in the local environment.')
code = '''import json, sys
train = {"synthetic-unit-a", "synthetic-unit-b"}
test = ["synthetic-unit-b", "synthetic-unit-c", "synthetic-unit-b"]
print(json.dumps({"python": sys.version.split()[0], "shared_entities": len(train & set(test)), "affected_test_rows": sum(unit in train for unit in test)}))
'''
report = {'started_at': datetime.now(timezone.utc).isoformat(), 'sdk_version': version('contree-sdk'),
          'image': 'python:3.12-slim', 'code_sha256': hashlib.sha256(code.encode()).hexdigest(),
          'code': code, 'data': 'Inline invented IDs only; no uploaded files or credentials in sandbox environment.',
          'scope': 'Standalone execution smoke test, not product integration or model-generated code.'}
try:
    client = ContreeSync(ContreeConfig(auth=IAMAuth(token=key, project_id=project), operation_timeout=120, transport_timeout=20))
    image = client.images.use(report['image'])
    result = image.run('python', args=['-c', code], timeout=10, disposable=True, truncate_output_at=4096).wait()
    output = json.loads(result.stdout)
    report.update(exit_code=result.exit_code, output=output, elapsed_seconds=result.result.elapsed_time.total_seconds())
    report['passed'] = result.exit_code == 0 and output.get('shared_entities') == 1 and output.get('affected_test_rows') == 2
except Exception as exc:
    # Provider exceptions may include request details; never persist their raw text.
    report.update(passed=False, error_type=type(exc).__name__)
report['finished_at'] = datetime.now(timezone.utc).isoformat()
out = ROOT / '.data/sandbox-checks'
out.mkdir(parents=True, exist_ok=True)
path = out / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.json')
path.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
print('Evidence:', path)
if not report['passed']:
    raise SystemExit(1)
