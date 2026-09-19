"""Evidence-aware scoring that cannot hide a proven failure behind missing review."""
import statistics


def score(result, expected, review=None, *, attempted=True):
    verdict = result.get('verdict') or {}
    gate = verdict.get('gate') or {}
    records = result.get('primitive_measurements') or {}
    ids = verdict.get('measurement_ids') or []
    replays = result.get('primitive_replays') or []
    gate_ok = (result.get('status') == 'completed' and gate.get('passed') is True
               and gate.get('verdict') == verdict.get('verdict') and bool(ids)
               and set(ids) == set(records))
    replay_ok = (bool(replays) and len(replays) == len(records)
                 and all(item.get('matches') is True for item in replays)
                 and {item.get('measurement_id') for item in replays} == set(records))
    metrics = {name: any(record.get('output', {}).get(name) == value for record in records.values())
               for name, value in expected.get('metrics', {}).items()}
    requirements = expected.get('review_requires', [])
    checks = {requirement: (review or {}).get('requirements', {}).get(requirement) for requirement in requirements}
    reviewed = bool(requirements) and all(value is True for value in checks.values())
    review_status = 'failed' if any(value is False for value in checks.values()) else 'passed' if reviewed else 'unmeasured'
    agreement = verdict.get('verdict') == expected['verdict']
    automated = attempted and gate_ok and replay_ok and agreement and all(metrics.values())
    return {'attempted': attempted, 'verdict_agreement': agreement, 'gate_passed': gate_ok,
            'primitive_replay_match': replay_ok, 'metric_checks': metrics, 'review_requires': checks,
            'automated_correct': bool(automated), 'gated_correct': bool(automated and reviewed),
            'review_status': review_status}


def summarize(rows, twins, review=None, *, cost_rows=None):
    """Supply all 24 base slots, including unstarted or failed attempts, plus six pairs."""
    per_trial = {trial: [row for row in rows if row['trial'] == trial] for trial in (1, 2)}
    counts = {str(trial): sum(row['score']['gated_correct'] for row in items) for trial, items in per_trial.items()}
    automated = {str(trial): sum(row['score']['automated_correct'] for row in items) for trial, items in per_trial.items()}
    attempted = {str(trial): sum(row['attempted'] for row in items) for trial, items in per_trial.items()}
    # Unstarted slots may improve; crashed/failed attempts may not silently be replaced.
    possible = {str(trial): automated[str(trial)] + 12 - attempted[str(trial)] for trial in (1, 2)}
    complete = len(rows) == 24 and all(len(items) == 12 for items in per_trial.values()) and all(row['attempted'] for row in rows)
    review_complete = complete and all(row['score']['review_status'] != 'unmeasured' for row in rows)
    proven_controls = 0
    for row in rows:
        verdict = (row['result'].get('verdict') or {}).get('verdict')
        if row['expected']['verdict'] in ('clear', 'clear_pending_confirmation', 'insufficient') and verdict in ('clear', 'violation'):
            if not row['score']['automated_correct'] or row['score']['review_status'] == 'failed':
                proven_controls += 1
    any_replay_failure = any(row['attempted'] and not row['score']['primitive_replay_match'] for row in rows)
    all_twins_attempted = len(twins) == 6 and all(pair['attempted'] for pair in twins)
    any_twin_failure = any(pair.get('false_clear') or pair.get('proven_failure') or (pair['attempted'] and not pair['passed']) for pair in twins)
    cost_population = rows if cost_rows is None else cost_rows
    cost_values = [row.get('estimated_usd') for row in cost_population]
    known_costs = [value for value in cost_values if value is not None]
    costs_complete = complete and bool(cost_population) and all(row['attempted'] for row in cost_population) and len(known_costs) == len(cost_population)
    unsupported = (review or {}).get('unsupported_definitives')
    corrections = (review or {}).get('corrections')
    median = statistics.median(corrections) if corrections else None
    correctness_status = ('fail' if min(possible.values()) < 8 or (review_complete and min(counts.values()) < 8)
                          else 'unmeasured' if not review_complete else 'pass' if min(counts.values()) >= 10 else 'inconclusive')
    def metric(value, status):
        return {'value': value, 'status': status}
    metrics = {
        'correct_each_trial': metric(counts, correctness_status),
        'automated_correct_upper_bound_each_trial': metric(automated, 'fail' if min(possible.values()) < 8 else 'unmeasured' if not complete else 'pass' if min(automated.values()) >= 10 else 'inconclusive'),
        'false_definitive_controls': metric(proven_controls, 'fail' if proven_controls else 'pass' if review_complete else 'unmeasured'),
        'primitive_replay': metric(not any_replay_failure, 'fail' if any_replay_failure else 'pass' if complete else 'unmeasured'),
        'twin_sensitivity': metric(twins, 'fail' if any_twin_failure else 'pass' if all_twins_attempted else 'unmeasured'),
        'blind_evidence_review': metric(unsupported, 'unmeasured' if unsupported is None else 'pass' if unsupported <= 1 else 'fail' if unsupported >= 3 else 'inconclusive'),
        'cost_per_attempt_usd': metric(max(known_costs) if known_costs else None, 'fail' if known_costs and max(known_costs) > 5 else 'unmeasured' if not costs_complete else 'pass' if max(known_costs) < 2 else 'inconclusive'),
        'median_corrections': metric(median, 'unmeasured' if median is None else 'pass' if median <= 1 else 'fail' if median >= 3 else 'inconclusive')}
    metrics['practitioner_comprehension'] = metric((review or {}).get('practitioner'), 'pass' if (review or {}).get('practitioner',{}).get('completed') is True and (review or {}).get('practitioner',{}).get('independent_human') is True else 'unmeasured')
    statuses = [value['status'] for value in metrics.values()]
    status = 'fail' if 'fail' in statuses else 'pass' if all(value == 'pass' for value in statuses) else 'unmeasured' if 'unmeasured' in statuses else 'inconclusive'
    return {'status': status, 'metrics': metrics, 'attempted_each_trial': attempted,
            'automated_correct_each_trial': automated, 'maximum_possible_each_trial': possible,
            'reviewed_correct_each_trial': counts, 'review_status': 'complete' if review_complete else 'unmeasured'}
