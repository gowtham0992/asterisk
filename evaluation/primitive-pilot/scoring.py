"""Acceptance scoring: label agreement alone never counts as evidence validation."""
def score(result,expected,review=None):
    v=result.get('verdict') or {};g=v.get('gate') or {};replays=result.get('primitive_replays') or []
    records=result.get('primitive_measurements') or {}
    ids=v.get('measurement_ids') or []
    gate_ok=g.get('passed') is True and g.get('verdict')==v.get('verdict') and bool(ids) and all(i in records for i in ids)
    replay_ok=bool(replays) and all(x.get('matches') is True for x in replays) and {x.get('measurement_id') for x in replays}==set(records)
    agreement=v.get('verdict')==expected['verdict']
    metric_checks={}
    outputs=[r.get('output',{}) for r in records.values()]
    for name,value in expected.get('metrics',{}).items():
        metric_checks[name]=any(o.get(name)==value for o in outputs)
    requirements=expected.get('review_requires',[])
    review_checks={r:None if review is None else review.get('requirements',{}).get(r) for r in requirements}
    reviewed=all(value is True for value in review_checks.values())
    automated=gate_ok and replay_ok and agreement and all(metric_checks.values())
    return {'verdict_agreement':agreement,'gate_passed':gate_ok,'primitive_replay_match':replay_ok,'metric_checks':metric_checks,'review_requires':review_checks,'automated_correct':automated,'gated_correct':automated and reviewed,'review_status':'unmeasured' if any(x is None for x in review_checks.values()) else 'passed' if reviewed else 'failed'}

def summarize(rows,twins,review=None):
    """Rows include trial, expected, result, score, and estimated_usd. Never hide missing work."""
    import statistics
    counts={str(t):sum(r['score']['gated_correct'] for r in rows if r['trial']==t) for t in (1,2)}
    complete=len(rows)==24 and all(sum(r['trial']==t for r in rows)==12 for t in (1,2))
    false_definitive=sum(r['expected']['verdict'] in ('clear','insufficient') and (r['result'].get('verdict') or {}).get('verdict') in ('clear','violation') and not r['score']['gated_correct'] for r in rows)
    replay=bool(rows) and all(r['score']['primitive_replay_match'] for r in rows)
    twin_complete=len(twins)==6 and all(p.get('complete') for p in twins)
    twin_pass=twin_complete and all(p.get('different') and not p.get('false_clear') and p.get('replay_match') for p in twins)
    costs=[r['estimated_usd'] for r in rows]
    corrections=None if review is None else review.get('corrections')
    unsupported=None if review is None else review.get('unsupported_definitives')
    median=statistics.median(corrections) if corrections else None
    known_review=all(r['score']['review_status']!='unmeasured' for r in rows)
    def row(value,status):return {'value':value,'status':status}
    metrics={
      'correct_each_trial':row(counts,'unmeasured' if not complete or not known_review else 'pass' if min(counts.values())>=10 else 'fail' if min(counts.values())<8 else 'inconclusive'),
      'false_definitive_controls':row(false_definitive,'unmeasured' if not complete or not known_review else 'pass' if false_definitive==0 else 'fail'),
      'primitive_replay':row(replay,'unmeasured' if not complete else 'pass' if replay else 'fail'),
      'twin_sensitivity':row(twins,'unmeasured' if not twin_complete else 'pass' if twin_pass else 'fail'),
      'blind_evidence_review':row(unsupported,'unmeasured' if unsupported is None else 'pass' if unsupported<=1 else 'fail' if unsupported>=3 else 'inconclusive'),
      'cost_per_case_usd':row(max(costs) if costs else None,'unmeasured' if not complete else 'pass' if max(costs)<2 else 'fail' if max(costs)>5 else 'inconclusive'),
      'median_corrections':row(median,'unmeasured' if median is None else 'pass' if median<=1 else 'fail' if median>=3 else 'inconclusive')}
    statuses=[m['status'] for m in metrics.values()]
    return {'status':'fail' if 'fail' in statuses else 'pass' if all(s=='pass' for s in statuses) else 'unmeasured' if 'unmeasured' in statuses else 'inconclusive','metrics':metrics,'automated_correct_each_trial':{str(t):sum(r['score']['automated_correct'] for r in rows if r['trial']==t) for t in (1,2)}}
