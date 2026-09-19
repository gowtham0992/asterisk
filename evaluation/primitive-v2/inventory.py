"""Prepare local upload inventories and preflight cases without any network call."""
import argparse
import json
from pathlib import Path
from v2harness import DATA, source_inventory, case_inventory, check, sha, canonical


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kind', choices=['source', 'cases'])
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--snapshot', type=Path, default=DATA / 'acceptance/snapshot.json')
    parser.add_argument('--mode', choices=['acceptance', 'regression'], default='acceptance')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.kind == 'source':
        inventory = source_inventory()
    else:
        if not args.manifest:
            parser.error('cases requires --manifest')
        # Verify freeze BEFORE opening any new acceptance manifest.
        frozen = json.loads(args.snapshot.read_text())
        check(frozen)
        if args.mode == 'acceptance' and frozen['purpose'] != 'unseen_acceptance':
            parser.error('Acceptance requires an acceptance freeze.')
        manifest = json.loads(args.manifest.read_text())
        inventory = case_inventory(manifest, frozen, args.manifest.parent, acceptance=args.mode == 'acceptance')
    text = json.dumps(inventory, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(text)
    print('Inventory SHA256:', sha(canonical(inventory)))


if __name__ == '__main__':
    main()
