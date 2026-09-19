"""Development evaluation; sends only the original synthetic cases to Nebius."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.agent import propose, SYSTEM
from app.audit import execute
from app.models import AuditInput


def score(case, proposal, result):
    """Compare semantic field choices and deterministic counts to frozen oracles."""
    expected = case['expected']
    errors = []
    if proposal['status'] != expected['proposal_status']:
        return ['Expected proposal status ' + expected['proposal_status']]
    for key, value in expected.get('rule', {}).items():
        actual = proposal['rule'].get(key)
        # Lists here are partition-label sets; order has no scientific meaning.
        if isinstance(value, list):
            actual, value = sorted(actual or []), sorted(value)
        if actual != value:
            errors.append(f'rule.{key}: expected {value!r}, got {actual!r}')
    for key, value in expected.get('result', {}).items():
        if result is None or result.get(key) != value:
            errors.append(f'result.{key}: expected {value!r}, got {None if result is None else result.get(key)!r}')
    return errors


def run_case(case, key, model, base_url, prompt):
    start = time.monotonic()
    record = {'case': case['id']}
    try:
        audit = AuditInput.model_validate(case['input'])
        proposal, provenance = propose(audit, key, model, base_url, system_prompt=prompt)
        result = execute(proposal['rule'], {f.name:f.content for f in audit.files}) if proposal['status']=='ready' else None
        errors = score(case, proposal, result)
        record.update(proposal=proposal, result=result, provenance=provenance, errors=errors, passed=not errors)
    except Exception as exc:
        # Inputs are synthetic; credentials and raw provider exceptions are not saved.
        record.update(passed=False, errors=[type(exc).__name__], error_type=type(exc).__name__)
    record['wall_seconds'] = round(time.monotonic()-start, 2)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prompt', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Choose a new output path; historical runs are not overwritten.')
    values = {}
    env_file = ROOT/'.env'
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if '=' in line and not line.lstrip().startswith('#'):
                k,v = line.split('=',1)
                if k.strip() in {'NEBIUS_API_KEY','NEBIUS_MODEL','NEBIUS_BASE_URL'}:
                    values[k.strip()] = v.strip().strip('"').strip("'")
    for k in ('NEBIUS_API_KEY','NEBIUS_MODEL','NEBIUS_BASE_URL'):
        if k in os.environ: values[k] = os.environ[k]
    if not values.get('NEBIUS_API_KEY'):
        parser.error('Set NEBIUS_API_KEY locally before running this paid live evaluation.')
    raw = (ROOT/'evaluation/cases.json').read_bytes()
    cases = json.loads(raw)
    prompt = args.prompt.read_text() if args.prompt else SYSTEM
    model = values.get('NEBIUS_MODEL','nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B')
    report = {'started_at':datetime.now(timezone.utc).isoformat(), 'model':model,
              'cases_sha256':hashlib.sha256(raw).hexdigest(), 'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),
              'prompt':prompt, 'method':'One trial per case; two concurrent cases; at most one repair per case. Development fixtures, not held-out evaluation.', 'cases':[]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(run_case,c,values['NEBIUS_API_KEY'],model,values.get('NEBIUS_BASE_URL','https://api.tokenfactory.nebius.com/v1/'),prompt) for c in cases]
        for future in as_completed(futures):
            record = future.result()
            report['cases'].append(record)
            args.output.write_text(json.dumps(report,indent=2)+'\n')
            print(record['case'], 'PASS' if record['passed'] else 'FAIL', record['errors'], flush=True)
    report['passed'] = sum(r['passed'] for r in report['cases'])
    report['total'] = len(cases)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(f"{report['passed']}/{report['total']} passed", flush=True)
    if report['passed'] != report['total']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
