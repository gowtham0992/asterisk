"""Protocol mechanics use artificial metadata, never new acceptance cases."""
import copy
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).parents[1]
V2 = ROOT / 'evaluation/primitive-v2'
sys.path.insert(0, str(V2))
import v2harness as h
import v2scoring as s
spec = importlib.util.spec_from_file_location('evaluation_v2_runner', V2 / 'run.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


def manifest(tmp_path):
    frozen = {'frozen_at': (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()}
    (tmp_path / 'base').mkdir()
    (tmp_path / 'repair').mkdir()
    (tmp_path / 'base/readme.txt').write_text('protocol fixture; no scientific case')
    (tmp_path / 'repair/readme.txt').write_text('different protocol fixture; no scientific case')
    cases = []
    for category in h.CATEGORIES:
        for index, label in enumerate(('violation', 'violation', 'clear', 'insufficient')):
            case = {'id': category + str(index), 'category': category, 'claim': 'mechanical fixture',
                    'author': 'test fixture', 'authored_at': (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
                    'source': {'family': ('yang', 'drug_response', 'planted', 'planted')[index], 'url': 'test-only',
                               'revision': 'test-only', 'license': 'test-only', 'transformations': 'test-only', 'previously_used': False},
                    'directory': 'base', 'input_hashes': {'readme.txt': h.sha('protocol fixture; no scientific case')},
                    'expected': {'verdict': label, 'review_requires': ['test obligation']}}
            if label == 'violation':
                case['twin'] = {'directory': 'repair', 'input_hashes': {'readme.txt': h.sha('different protocol fixture; no scientific case')},
                                'expected': {'verdict': 'clear', 'review_requires': ['repair obligation']}}
            cases.append(case)
    return {'freeze_hash': h.sha(h.canonical(frozen)), 'cases': cases}, frozen


def result(verdict='violation'):
    return {'status': 'completed', 'claim': 'mechanical fixture', 'probes': {}, 'tokens': {'prompt': 1, 'completion': 1},
            'verdict': {'verdict': verdict, 'gate': {'passed': True, 'verdict': verdict}, 'measurement_ids': ['m']},
            'primitive_measurements': {'m': {'output': {}}}, 'primitive_replays': [{'measurement_id': 'm', 'matches': True}]}


def rows(correct=12, *, human=False):
    data = []
    for trial in (1, 2):
        for index in range(12):
            expected = {'verdict': 'violation', 'review_requires': ['obligation']}
            output = result() if index < correct else {'status': 'failed'}
            review = {'requirements': {'obligation': True}} if human else None
            data.append({'trial': trial, 'attempted': True, 'expected': expected, 'result': output,
                         'score': s.score(output, expected, review), 'estimated_usd': .01})
    return data


def twins():
    return [{'attempted': True, 'passed': True, 'false_clear': False} for _ in range(6)]


def test_fewer_than_eight_is_proven_failure_without_reviewer():
    report = s.summarize(rows(7), twins())
    assert report['automated_correct_each_trial'] == {'1': 7, '2': 7}
    assert report['metrics']['correct_each_trial']['status'] == 'fail'
    assert report['metrics']['blind_evidence_review']['status'] == 'unmeasured'
    assert report['status'] == 'fail'


def test_automated_success_cannot_replace_human_review():
    report = s.summarize(rows(), twins())
    assert report['status'] == 'unmeasured'
    assert report['metrics']['correct_each_trial']['status'] == 'unmeasured'
    assert s.summarize(rows(human=True), twins(), {'unsupported_definitives': 0, 'corrections': [0]})['status'] == 'pass'


def test_unstarted_slots_are_not_failed_or_removed():
    data = rows(7)
    for row in data:
        if row['result']['status'] == 'failed':
            row['attempted'] = False
            row['score'] = s.score({}, row['expected'], attempted=False)
    report = s.summarize(data, [])
    assert report['maximum_possible_each_trial'] == {'1': 12, '2': 12}
    assert report['status'] == 'unmeasured'


def test_acceptance_checks_timestamp_hash_balance_and_unused_source(tmp_path):
    data, frozen = manifest(tmp_path)
    assert len(h.validate(data, frozen, tmp_path)) == 12
    for mutation, match in [
        (lambda d: d['cases'][0].update(authored_at=frozen['frozen_at']), 'after'),
        (lambda d: d['cases'][0]['source'].update(previously_used=True), 'unused'),
        (lambda d: d['cases'][0]['expected'].update(verdict='clear'), 'two violations'),
        (lambda d: d.update(freeze_hash='wrong'), 'different'),
    ]:
        bad = copy.deepcopy(data)
        mutation(bad)
        with pytest.raises(ValueError, match=match):
            h.validate(bad, frozen, tmp_path)
    (tmp_path / 'base/readme.txt').write_text('changed')
    with pytest.raises(ValueError, match='hash changed'):
        h.validate(data, frozen, tmp_path)


def test_known_regression_is_not_required_to_be_postfreeze_or_unused(tmp_path):
    data, frozen = manifest(tmp_path)
    data['freeze_hash'] = 'historical freeze'
    data['cases'][0]['source']['previously_used'] = True
    data['cases'][0]['authored_at'] = frozen['frozen_at']
    inventory = h.case_inventory(data, frozen, tmp_path, acceptance=False)
    assert inventory['mode'] == 'known_regression'
    assert len(inventory['cases']) == 18


def test_input_must_stay_within_variant_directory(tmp_path):
    data, frozen = manifest(tmp_path)
    data['cases'][0]['input_hashes'] = {'../repair/readme.txt': h.sha('different protocol fixture; no scientific case')}
    with pytest.raises(ValueError, match='escapes'):
        h.validate(data, frozen, tmp_path)


def test_new_modules_are_included_in_snapshot_fingerprint(tmp_path):
    for name in ('app/audit.py', 'app/source_analysis.py', 'app/checkpoint.py',
                 'evaluation/primitive-v2/protocol.md', 'evaluation/probe-pilot/common.py', 'evaluation/probe-pilot/budget.py'):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('fixture')
    files = h.fingerprint(tmp_path)
    assert 'app/source_analysis.py' in files and 'app/checkpoint.py' in files
    (tmp_path / 'app/source_analysis.py').write_text('changed')
    assert files != h.fingerprint(tmp_path)


def test_crash_is_preserved_counted_and_never_retried(tmp_path):
    data, frozen = manifest(tmp_path)
    runroot = tmp_path / 'runs'
    runroot.mkdir()
    job = next(h.jobs(data['cases']))
    calls = []
    def failing(*args):
        calls.append(True)
        raise RuntimeError('deliberate fixture crash')
    r.run_attempt(job, tmp_path, runroot, frozen, failing)
    r.run_attempt(job, tmp_path, runroot, frozen, failing)
    assert len(calls) == 1
    row = r.read_row(job, runroot)
    assert row['attempted'] is True
    assert row['score']['automated_correct'] is False
    assert list(runroot.glob('*/failure.json'))
    assert list(runroot.glob('*/inputs/readme.txt'))
    report = r.report(data['cases'], runroot)
    assert report['attempted_runs'] == 1 and report['scheduled_runs'] == 36
    assert len(report['runs']) == 36


def test_interrupted_attempt_stays_incorrect(tmp_path):
    data, frozen = manifest(tmp_path)
    runroot = tmp_path / 'runs'
    runroot.mkdir()
    job = next(h.jobs(data['cases']))
    directory = runroot / (job[3] + '-trial1')
    directory.mkdir()
    (directory / 'events.jsonl').write_text('partial transcript\n')
    r.run_attempt(job, tmp_path, runroot, frozen, lambda *_: pytest.fail('must not retry'))
    assert json.loads((directory / 'failure.json').read_text())['error'] == 'interrupted_attempt'
    assert (directory / 'events.jsonl').read_text() == 'partial transcript\n'


def test_completed_attempt_keeps_verifiable_result(tmp_path):
    data, frozen = manifest(tmp_path)
    runroot = tmp_path / 'runs'
    runroot.mkdir()
    job = next(h.jobs(data['cases']))
    r.run_attempt(job, tmp_path, runroot, frozen, lambda *_: result())
    assert r.read_row(job, runroot)['score']['automated_correct']
    path = next(runroot.glob('*/evidence/result.json'))
    changed = json.loads(path.read_text())
    changed['claim'] = 'tampered'
    path.write_text(json.dumps(changed))
    assert not r.read_row(job, runroot)['score']['automated_correct']


def test_shared_budget_thread_reservations_and_process_lock(tmp_path):
    budget = h.load_helper('budget').Budget(tmp_path / 'budget.json', {'model': (1, 1)}, limit=1)
    with h.batch_lock(tmp_path / 'batch.lock'):
        with pytest.raises(BlockingIOError):
            with h.batch_lock(tmp_path / 'batch.lock'):
                pass
        with ThreadPoolExecutor(max_workers=3) as pool:
            reservations = list(pool.map(lambda _: budget.reserve('model', 200000, 0), range(12)))
    assert sum(item is not None for item in reservations) == 5
    assert sum(value['amount'] for value in budget.state['reservations'].values()) <= 1


def test_human_review_must_be_explicit_and_independent(tmp_path):
    path = tmp_path / 'review.json'
    path.write_text(json.dumps({'unsupported_definitives': 0, 'corrections': [0]}))
    with pytest.raises(ValueError, match='independent human'):
        r.load_review(path)


def test_base_and_twin_names_must_not_collide(tmp_path):
    data, frozen = manifest(tmp_path)
    data['cases'][2]['id'] = data['cases'][0]['id'] + '-twin'
    with pytest.raises(ValueError, match='collide'):
        h.validate(data, frozen, tmp_path)


def test_twin_truth_change_cannot_be_only_provenance_hash_change():
    first = result()
    second = result('clear')
    first['primitive_measurements']['m']['output'] = {'count': 0, 'source_sha256': 'first'}
    second['primitive_measurements']['m']['output'] = {'count': 0, 'source_sha256': 'second'}
    assert r.measurement_signature(first) == r.measurement_signature(second)
    second['primitive_measurements']['m']['output']['count'] = 1
    assert r.measurement_signature(first) != r.measurement_signature(second)


def test_a_failed_twin_attempt_proves_failure_before_remaining_slots_finish():
    report = s.summarize([], [{'attempted': False, 'passed': False, 'proven_failure': True}])
    assert report['status'] == 'fail'
    assert report['metrics']['twin_sensitivity']['status'] == 'fail'


def test_acceptance_snapshot_archives_helpers_and_refuses_overwrite(tmp_path, monkeypatch):
    for name in ('app/checkpoint.py', 'app/source_analysis.py', 'evaluation/primitive-v2/protocol.md',
                 'evaluation/probe-pilot/common.py', 'evaluation/probe-pilot/budget.py'):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('snapshot fixture')
    monkeypatch.setattr(h, 'runtime_state', lambda: {'implementation_hash': 'current', 'prompt': 'frozen prompt', 'tools': []})
    environment = {'implementation_hash': 'current', 'image': 'immutable-image'}
    destination = tmp_path / 'experiment'
    proof = {'implementation_hash': 'current', 'passed': True, 'pairs': [{'passed': True}] * 6}
    frozen = h.snapshot(destination, environment, acceptance=True, twins=proof, root=tmp_path)
    assert frozen['purpose'] == 'unseen_acceptance'
    assert (destination / 'frozen-source/app/checkpoint.py').read_text() == 'snapshot fixture'
    assert json.loads((destination / 'snapshot.json').read_text()) == frozen
    with pytest.raises(FileExistsError):
        h.snapshot(destination, environment, acceptance=True, twins=proof, root=tmp_path)
    proof['pairs'][0] = {'passed': False}
    with pytest.raises(ValueError, match='six development twins'):
        h.snapshot(tmp_path / 'second', environment, acceptance=True, twins=proof, root=tmp_path)


def test_cost_threshold_includes_twin_attempts():
    base = rows(human=True)
    extra = [{'attempted': True, 'estimated_usd': .01} for _ in range(12)]
    extra[-1]['estimated_usd'] = 6.0
    report = s.summarize(base, twins(), {'unsupported_definitives': 0, 'corrections': [0]}, cost_rows=base + extra)
    assert report['metrics']['cost_per_attempt_usd'] == {'value': 6.0, 'status': 'fail'}
    assert report['status'] == 'fail'
    extra[-1]['estimated_usd'] = None
    report = s.summarize(base, twins(), {'unsupported_definitives': 0, 'corrections': [0]}, cost_rows=base + extra)
    assert report['metrics']['cost_per_attempt_usd']['status'] == 'unmeasured'


def test_release_allowlist_contains_v2_tooling_without_private_inputs():
    from scripts.package_release import release_files
    names = {path.relative_to(ROOT).as_posix() for path in release_files(ROOT)}
    assert {'evaluation/primitive-v2/' + path.name for path in V2.glob('*.py')} <= names
    assert 'evaluation/primitive-v2/protocol.md' in names
    assert 'evaluation/primitive-v2/README.md' in names
    assert 'evaluation/primitive-pilot/REPORT.md' in names
    assert not any(name.startswith('.data/') or name == '.env' for name in names)
