"""Read-only permission check. Requires requirements-sandbox.txt; never prints credentials."""
from pathlib import Path
from contree_client.httpx import ContreeClient

root = Path(__file__).resolve().parent.parent
values = {}
for line in (root / '.env').read_text().splitlines():
    if '=' in line and not line.lstrip().startswith('#'):
        key, value = line.split('=', 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
if not values.get('NEBIUS_API_KEY') or not values.get('NEBIUS_AI_PROJECT'):
    raise SystemExit('Set NEBIUS_API_KEY and NEBIUS_AI_PROJECT in the local .env first.')
with ContreeClient(values['NEBIUS_API_KEY'], project=values['NEBIUS_AI_PROJECT'], timeout=20) as client:
    try:
        client.list_images(limit=1)
        print('Sandbox image-list permission verified. Execution permission has not been tested.')
    except Exception as exc:
        message = str(exc).replace(values['NEBIUS_API_KEY'], '[REDACTED]')
        raise SystemExit(type(exc).__name__ + ': ' + message[:500]) from None
