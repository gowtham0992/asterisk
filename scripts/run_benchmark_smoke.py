"""Run the separately approved three-call smoke packet once. No retries or Sandbox.

An approval file must record approved=true and inventory_sha256 for the exact
inventory bytes. This script does not grant approval or create a fresh budget.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.preparation.proposal import ProposalRequest

CASES = ('dermamnist', 'ptbxl', 'wsi')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_new(path, value):
    # Exclusive and private, including raw completions and identifier profiles.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())


def preflight(packet_dir, approval):
    encoded = (packet_dir / 'inventory.json').read_bytes()
    inventory = json.loads(encoded)
    authorization = json.loads(approval.read_bytes())
    if authorization.get('approved') is not True or authorization.get('inventory_sha256') != digest(encoded):
        raise ValueError('Exact inventory approval required')
    entries = inventory['cases']
    if (inventory.get('trials') != 3 or inventory.get('retries') != 0 or
            [entry['case'] for entry in entries] != list(CASES)):
        raise ValueError('Expected the fixed three-call packet')
    requests = []
    for entry in entries:
        raw = (packet_dir / (entry['case'] + '.json')).read_bytes()
        if digest(raw) != entry['packet_sha256']:
            raise ValueError('Packet bytes changed')
        packet = json.loads(raw)
        if packet['case'] != entry['case']:
            raise ValueError('Case identity changed')
        request = ProposalRequest(packet['files'], packet['claim'], ['documentation.txt'], packet['projection'])
        preview = request.preview()
        if preview != packet['preview'] or preview['payload_hash'] != entry['payload_hash']:
            raise ValueError('Application payload changed')
        requests.append((entry['case'], request))
    return digest(encoded), requests


def default_factory():
    if 'ASTERISK_PREPARATION_BUDGET' in os.environ:
        raise ValueError('This batch requires the original cumulative research ledger')
    from app.preparation.provider import configured
    return configured()


def run(packet_dir, approval, output, *, completion_factory=default_factory):
    inventory_hash, requests = preflight(packet_dir, approval)
    if (packet_dir / 'attempt-consumed.json').exists():
        raise FileExistsError('This packet was already consumed')
    # Construction does not call the provider; validate budget before consuming.
    complete = completion_factory()
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    write_new(packet_dir / 'attempt-consumed.json', {
        'inventory_sha256': inventory_hash, 'output': str(output.resolve()),
        'scope': 'One execution only, including interrupted or failed executions.'})
    outcomes = []
    for name, request in requests:
        attempt = output / name
        attempt.mkdir(mode=0o700)
        write_new(attempt / 'request.json', request.preview())
        returned = False
        recording_failed = False

        def capture(messages, maximum, timeout):
            nonlocal returned
            try:
                result = complete(messages, maximum, timeout)
            except Exception as exc:
                write_new(attempt / 'provider-error.json', {
                    'error_type': type(exc).__name__,
                    'response': getattr(exc, 'provider_response', None),
                    'reservation': getattr(exc, 'reservation', None),
                    'estimated_usd': getattr(exc, 'estimated_usd', None)})
                raise
            # Durably retain completion before parser/executor sees it.
            write_new(attempt / 'completion.json', result)
            returned = True
            return result

        try:
            result = request.submit(request.preview()['payload_hash'], True, capture)
            outcome = {key: value for key, value in result.items() if key != 'session'}
            session = result.get('session')
            if session is not None:
                outcome['spec'] = session.spec
                outcome['scientific_confirmation'] = None
                outcome['proposal_issue'] = getattr(session, 'proposal_issue', None)
                try:
                    write_new(attempt / 'model-record.json', session.model_proposal)
                except OSError:
                    recording_failed = True
                    raise
        except Exception as exc:
            outcome = {'status': 'invalid_proposal' if returned and not recording_failed else 'stopped_provider_or_recording_failure',
                       'error_type': type(exc).__name__}
        ledger_path = getattr(complete, 'path', None)
        if ledger_path is not None:
            state = json.loads(Path(ledger_path).read_text())
            write_new(attempt / 'budget-after.json', {key: state.get(key) for key in
                ('limit_usd', 'settled_usd', 'reservations', 'uncertain')})
        write_new(attempt / 'outcome.json', outcome)
        outcomes.append({'case': name, **outcome})
        if not returned or recording_failed:
            break
    summary = {'inventory_sha256': inventory_hash, 'outcomes': outcomes,
               'scope': 'Exposed development proposal smoke only; no human confirmation or Sandbox receipt.'}
    write_new(output / 'summary.json', summary)
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet-dir', type=Path, required=True)
    parser.add_argument('--approval', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = run(args.packet_dir, args.approval, args.output)
    print(json.dumps({'attempts': len(result['outcomes']), 'statuses': [x['status'] for x in result['outcomes']]}))
