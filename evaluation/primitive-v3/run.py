"""Run separate v2 known-case regressions or frozen unseen acceptance attempts."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import traceback
from v3harness import (ROOT, DATA, MODEL, RATES, SAFE_ID, batch_lock, canonical, case_inventory,
                     check, jobs, load_helper, now, read_inputs, sha, snapshot, validate)
from v3scoring import score, summarize


def write_json(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2))
    temporary.replace(path)


def run_attempt(job, root, runroot, frozen, execute):
    """A durable start marker prevents both silent retry and disappearance on crash."""
    case, variant, trial, case_id = job
    name = f'{case_id}-trial{trial}'
    destination = runroot / name
    if destination.exists():
        # An existing directory represents an attempted slot, including partial writes.
        if not (destination / 'completion.json').exists() and not (destination / 'failure.json').exists():
            write_json(destination / 'failure.json', {'error': 'interrupted_attempt', 'case_id': case_id,
                       'trial': trial, 'note': 'Original partial artifacts retained; no automatic retry.'})
        return
    destination.mkdir()
    write_json(destination / 'attempt.json', {'case_id': case_id, 'trial': trial, 'started_at': now(),
               'freeze_hash': sha(canonical(frozen)), 'input_hashes': variant['input_hashes']})
    def event(value):
        with (destination / 'events.jsonl').open('a') as handle:
            handle.write(json.dumps(value) + '\n')
            handle.flush()
    try:
        files = read_inputs(variant, root)
        inputs = destination / 'inputs'
        inputs.mkdir()
        for name, content in files.items():
            path = inputs / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        result = execute(case, files, event)
        result.update(case_id=case_id, trial=trial, freeze_hash=sha(canonical(frozen)),
                      estimated_usd=(result['tokens']['prompt'] * .30 + result['tokens']['completion'] * .90) / 1e6)
        from app.probe_evidence import bundle
        bundle(result, files, destination / 'evidence')
        write_json(destination / 'completion.json', {'completed_at': now(), 'result_sha256': sha(canonical(result))})
    except Exception as exc:
        write_json(destination / 'failure.json', {'case_id': case_id, 'trial': trial,
                   'error': type(exc).__name__, 'finished_at': now(),
                   'note': 'Attempt retained as incorrect; unknown token reservations remain charged.',
                   'traceback': traceback.format_exc()})


def read_row(job, runroot, review=None):
    case, variant, trial, case_id = job
    name = f'{case_id}-trial{trial}'
    directory = runroot / name
    attempted = directory.exists()
    result = {'status': 'failed' if attempted else 'unstarted'}
    if (directory / 'completion.json').exists() and not (directory / 'failure.json').exists():
        try:
            candidate = json.loads((directory / 'evidence/result.json').read_text())
            completion = json.loads((directory / 'completion.json').read_text())
            if sha(canonical(candidate)) != completion['result_sha256']:
                raise ValueError('Retained result changed.')
            result = candidate
        except (OSError, ValueError, KeyError):
            result = {'status': 'failed', 'error': 'invalid_retained_result'}
    human = (review or {}).get('runs', {}).get(name)
    return {'case_id': case_id, 'trial': trial, 'attempted': attempted, 'expected': variant['expected'],
            'result': result, 'score': score(result, variant['expected'], human, attempted=attempted),
            'estimated_usd': result.get('estimated_usd')}


def measurement_signature(result):
    def scrub(value):
        if isinstance(value, dict):
            return {key: scrub(item) for key, item in value.items() if key not in ('source_sha256', 'hashes', 'input_hashes', 'implementation_hash')}
        if isinstance(value, list):
            return [scrub(item) for item in value]
        return value
    outputs = [{'primitive': record.get('primitive'), 'output': scrub(record.get('output', {}))}
               for record in result.get('primitive_measurements', {}).values()]
    return sorted(canonical(value) for value in outputs)


def report(cases, runroot, review=None):
    allrows = {(case_id, trial): read_row(job, runroot, review) for job in jobs(cases) for _, _, trial, case_id in [job]}
    rows = [allrows[case['id'], trial] for case in cases for trial in (1, 2)]
    twins = []
    for case in cases:
        if 'twin' not in case:
            continue
        pairs = [(allrows[case['id'], trial], allrows[case['id'] + '-twin', trial]) for trial in (1, 2)]
        attempted = all(left['attempted'] and right['attempted'] for left, right in pairs)
        verdict = lambda row: (row['result'].get('verdict') or {}).get('verdict')
        different = attempted and all(verdict(left) == 'violation' and verdict(right) == ('clear_pending_confirmation' if case['category']=='entity_overlap' else 'clear') for left, right in pairs)
        replay = attempted and all(left['score']['primitive_replay_match'] and right['score']['primitive_replay_match'] for left, right in pairs)
        false_clear = any(verdict(left) == 'clear' for left, _ in pairs)
        measured_change = attempted and all(measurement_signature(left['result']) != measurement_signature(right['result']) for left, right in pairs)
        failed_attempt = any(row['attempted'] and not row['score']['automated_correct'] for pair in pairs for row in pair)
        twins.append({'case_id': case['id'], 'attempted': attempted, 'different': different,
                      'false_clear': false_clear, 'replay_match': replay, 'measurement_changed': measured_change,
                      'proven_failure': failed_attempt or (attempted and not measured_change),
                      'passed': different and replay and measured_change and not false_clear})
    summary = summarize(rows, twins, review, cost_rows=list(allrows.values()))
    summary['attempted_runs'] = sum(row['attempted'] for row in allrows.values())
    summary['scheduled_runs'] = len(allrows)
    summary['runs'] = [{key: value for key, value in row.items() if key not in ('expected', 'result')} for row in allrows.values()]
    return summary


def load_review(path):
    if path is None:
        return None
    review = json.loads(path.read_text())
    if not review.get('reviewer') or review.get('independent_human') is not True or not review.get('blind_ratings_committed_at'):
        raise ValueError('Review requires named independent human and committed blind-rating timestamp.')
    from v3harness import stamp
    stamp(review['blind_ratings_committed_at'])
    for key in ('unsupported_definitives',):
        value = review.get(key)
        if value is not None and (type(value) is not int or value < 0):
            raise ValueError('Review counts must be nonnegative integers or null.')
    corrections = review.get('corrections')
    if corrections is not None and (not isinstance(corrections, list) or any(type(v) is not int or v < 0 for v in corrections)):
        raise ValueError('Corrections must be genuinely observed nonnegative integer counts.')
    return review


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['regression', 'acceptance'], required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--experiment', help='Unique known-regression experiment name.')
    parser.add_argument('--environment', type=Path, default=DATA / 'environment.json')
    parser.add_argument('--workers', type=int, choices=[1, 2, 3], default=3)
    parser.add_argument('--inventory-sha', help='Exact hash of the locally reviewed case upload inventory.')
    parser.add_argument('--preflight', action='store_true', help='Snapshot/validate/write inventory without network or inference.')
    parser.add_argument('--report-only', action='store_true')
    parser.add_argument('--review', type=Path)
    args = parser.parse_args()
    if args.mode == 'regression':
        if not args.experiment or not SAFE_ID.fullmatch(args.experiment):
            parser.error('Known regression requires a unique safe --experiment name.')
        experiment = DATA / 'regression' / args.experiment
        if not experiment.exists():
            if args.report_only:
                parser.error('No existing regression experiment to report.')
            snapshot(experiment, json.loads(args.environment.read_text()))
    else:
        experiment = DATA / 'acceptance'
    # Frozen source check intentionally precedes opening acceptance manifest/inputs.
    frozen = json.loads((experiment / 'snapshot.json').read_text())
    check(frozen)
    if args.mode == 'acceptance' and frozen['purpose'] != 'unseen_acceptance':
        parser.error('Unseen acceptance requires an acceptance freeze.')
    manifest = json.loads(args.manifest.read_text())
    cases = validate(manifest, frozen, args.manifest.parent, acceptance=args.mode == 'acceptance')
    serialized = json.dumps(manifest, sort_keys=True, indent=2)
    seal = experiment / 'cases-sealed.json'
    if seal.exists() and seal.read_text() != serialized:
        parser.error('Sealed cases changed. Start a separate experiment.')
    if not seal.exists():
        with seal.open('x') as handle:
            handle.write(serialized)
    inventory = case_inventory(manifest, frozen, args.manifest.parent, acceptance=args.mode == 'acceptance')
    write_json(experiment / 'upload-inventory.json', inventory)
    inventory_hash = sha(canonical(inventory))
    if args.preflight:
        print(json.dumps({'experiment': str(experiment), 'inventory': str(experiment / 'upload-inventory.json'),
                          'inventory_sha': inventory_hash, 'runs': 36, 'mode': args.mode}, indent=2))
        return
    review = load_review(args.review)
    runroot = experiment / 'runs'
    runroot.mkdir(exist_ok=True)
    with batch_lock():
        if not args.report_only:
            if args.inventory_sha != inventory_hash:
                parser.error('Inspect the sealed upload inventory and supply its exact --inventory-sha before upload.')
            from app.probes import investigate
            from app.primitive_runtime import PrimitiveSandbox
            key, project = load_helper('common').credentials()
            # Exactly one shared Budget for all threads, under the cross-process lock.
            ledger = ROOT / '.data/probe-pilot/budget.json'
            if not ledger.exists():
                raise ValueError('Original cumulative ledger is missing; refusing to reset prior spend.')
            budget = load_helper('budget').Budget(ledger, RATES, limit=10)
            if budget.state['limit_usd'] > 10:
                raise ValueError('Ledger limit exceeds the authorized cumulative $10 cap.')
            def execute(case, files, on_event):
                return investigate(case['claim'], files, key, MODEL, PrimitiveSandbox(key, project, frozen['image']),
                                   category=case['category'], budget=budget, on_event=on_event)
            with ThreadPoolExecutor(max_workers=args.workers) as pool:
                list(pool.map(lambda job: run_attempt(job, args.manifest.parent, runroot, frozen, execute), jobs(cases)))
        summary = report(cases, runroot, review)
        summary.update(mode=args.mode, unseen=args.mode == 'acceptance', snapshot_hash=sha(canonical(frozen)),freeze_hash=sha(canonical(frozen)),implementation_hash=frozen['implementation_hash'],authorship_constraint=manifest.get('authorship_constraint'))
        write_json(experiment / 'report.json', summary)
        if args.mode=='acceptance':write_json(DATA/'acceptance-report.json',summary)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
