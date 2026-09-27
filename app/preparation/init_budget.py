"""Explicitly create a new installation's estimated preparation budget, offline.

Never run this to replace a spent, uncertain, missing or damaged live ledger.
"""
import argparse
import json
import math
import os
from pathlib import Path


def initialize(path, limit):
    if type(limit) not in (int, float) or not math.isfinite(limit) or not 0 < limit <= 1:
        raise ValueError('Preparation estimated cap must be greater than zero and at most $1')
    path = Path(path)
    if not path.is_absolute():
        raise ValueError('Use an absolute path on persistent local storage')
    state = {'purpose': 'asterisk-preparation-v1', 'limit_usd': limit,
             'settled_usd': 0, 'reservations': {}, 'uncertain': []}
    # O_EXCL also refuses dangling symlinks. No reset or overwrite switch.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as handle:
        json.dump(state, handle, indent=2, allow_nan=False)
        handle.flush()
        os.fsync(handle.fileno())
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--path', required=True)
    parser.add_argument('--limit-usd', required=True, type=float)
    args = parser.parse_args()
    try:
        initialize(args.path, args.limit_usd)
    except (ValueError, OSError) as exc:
        parser.exit(2, f'Budget not created: {exc}\n')
    print('Created new estimated preparation budget. Inference remains disabled until explicitly configured.')


if __name__ == '__main__':
    main()
