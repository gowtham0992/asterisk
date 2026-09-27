"""Recompute an experimental local review from its supplied inputs and choices.

Integrity and reproducibility only. A record can be completely regenerated with
other inputs: this verifies neither external provenance nor scientific meaning.
"""
import argparse
import json
from pathlib import Path
from .review import executor,prepare


def policies_from(review):
    policies={}
    for decision in review['decisions']:
        if decision['file'] in policies:raise ValueError('Repeated source decision')
        policies[decision['file']]={'sample':decision['sample'],'repeats':decision['repeats'],
            'evidence':[{k:c[k] for k in ('file','start_line','end_line')} for c in decision['evidence']],
            **{key:decision[key] for key in ('entity','partition') if key in decision}}
    return policies


def verify(record):
    if not isinstance(record,dict) or record.get('schema_version')!=2:
        raise ValueError('A version 2 review record with original inputs is required')
    body={k:v for k,v in record.items() if k!='record_hash'}
    if executor.sha(executor.canonical(body))!=record.get('record_hash'):
        raise ValueError('Record hash mismatch')
    review=record['review'];confirmation=record.get('confirmation')
    if 'model_proposal' in record:
        from .model_record import verify_model_record
        verify_model_record(record['model_proposal'],review['original_spec'],record['inputs'])
    if not isinstance(confirmation,dict) or confirmation.get('review_hash')!=review.get('review_hash'):
        raise ValueError('Confirmation does not reference this review')
    if not isinstance(confirmation.get('recorded_at'),str) or not confirmation.get('statement'):
        raise ValueError('Confirmation metadata missing')
    policies=policies_from(review)
    recomputed=prepare(review['original_spec'],record['inputs'],policies,review_version=review['schema_version'])
    if executor.canonical(recomputed)!=executor.canonical(review):
        raise ValueError('Recorded review differs from the recomputed result')
    return {'status':'matches','recomputed_population':recomputed['reviewed_population'],
        'original_blocked':recomputed['original_error'] is not None,
        'scope':'Local recomputation only; no identity, scientific meaning or external provenance verified.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('record',type=Path)
    args=parser.parse_args()
    try:
        if args.record.stat().st_size>32_000_000:raise ValueError('Review record exceeds the 32 MB local-tool limit')
        record=json.loads(args.record.read_text(),object_pairs_hook=executor.unique)
        print(json.dumps(verify(record),indent=2))
    except (ValueError,KeyError,TypeError,OSError,RecursionError) as exc:
        print(json.dumps({'status':'failed','error':str(exc) if isinstance(exc,(ValueError,OSError)) else 'Malformed review record'}))
        raise SystemExit(1)


if __name__=='__main__':main()
