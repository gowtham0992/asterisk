"""Bake only the exact inventory approved for the v2 trusted primitive image."""
import argparse
import json
from pathlib import Path
from v2harness import ROOT, DATA, load_helper, source_inventory, sha, canonical


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory-sha', required=True, help='Hash of the reviewed source inventory; mismatch refuses upload.')
    parser.add_argument('--base-environment', type=Path, default=ROOT / '.data/probe-pilot/environment.json')
    args = parser.parse_args()
    inventory = source_inventory()
    if args.inventory_sha != sha(canonical(inventory)):
        parser.error('Source inventory changed; inspect the current payload before authorizing its hash.')
    from app.primitive_runtime import FILES, DRIVER, implementation_hash
    from contree_sdk import ContreeSync
    from contree_sdk.auth import IAMAuth
    from contree_sdk.config import ContreeConfig
    key, project = load_helper('common').credentials()
    base = json.loads(args.base_environment.read_text())['image']
    client = ContreeSync(ContreeConfig(auth=IAMAuth(token=key, project_id=project), operation_timeout=150, transport_timeout=30))
    files = {'/opt/asterisk/app/' + name: (ROOT / 'app' / name).read_bytes() for name in FILES}
    files.update({'/opt/asterisk/app/__init__.py': b'', '/opt/asterisk/primitive_main.py': DRIVER.encode()})
    result = client.images.use(base).run('python', args=['-c', "import sys;sys.path.insert(0,'/opt/asterisk');from app.primitives import VERSION;print(VERSION)"], files=files, timeout=30, disposable=False).wait()
    if result.exit_code:
        raise SystemExit('Primitive image import validation failed.')
    environment = {'image': str(result.uuid), 'base_image': base, 'implementation_hash': implementation_hash(),
                   'version': result.stdout.strip(), 'source_inventory_hash': args.inventory_sha}
    DATA.mkdir(parents=True, exist_ok=True)
    # Immutable per-image evidence plus a pointer for the latest bake.
    (DATA / ('environment-' + str(result.uuid) + '.json')).write_text(json.dumps(environment, indent=2))
    (DATA / 'environment.json').write_text(json.dumps(environment, indent=2))
    print(json.dumps(environment, indent=2))


if __name__ == '__main__':
    main()
