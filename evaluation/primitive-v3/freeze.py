"""Freeze v3 before any unseen case access; preserve the entire source snapshot."""
import argparse
import json
from pathlib import Path
from v3harness import DATA, snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--environment', type=Path, default=DATA / 'environment.json')
    parser.add_argument('--twins', type=Path, default=DATA / 'gate-a.json')
    parser.add_argument('--unseen-not-accessed', action='store_true', help='Attest that new cases have not been selected, opened or authored.')
    args = parser.parse_args()
    if not args.unseen_not_accessed:
        parser.error('Freeze requires the explicit unseen-access attestation.')
    result = snapshot(DATA / 'acceptance', json.loads(args.environment.read_text()),
                      acceptance=True, twins=json.loads(args.twins.read_text()))
    (DATA/'snapshot.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k not in ('prompt','tools','files')},indent=2))


if __name__ == '__main__':
    main()
