"""Re-derive a decision; no claim of authenticity for unsigned human confirmations."""
from .primitives import gate, digest
from .probes import sha
from .receipt import preview


def verify_verdict(result, replayed, files):
    expected_hashes={n:sha(t) for n,t in files.items()}
    records=list(replayed.values())
    if not records or result.get('input_hashes')!=expected_hashes or any(r.get('execution_error') or r.get('primitive')!='entity_overlap' or r.get('input_hashes')!=expected_hashes for r in records):
        return {'matches':False,'reason':'Missing or inconsistent replay evidence'}
    decision=gate('entity_overlap',records,[])
    expected=decision['verdict']
    if expected=='clear_pending_confirmation' and result.get('binding_confirmation'):
        confirmation=result['binding_confirmation']
        claim=result.get('original_claim') or result.get('claim')
        binding={**decision['binding'],'claim':claim}
        valid=(confirmation.get('confirmed') is True and confirmation.get('binding_hash')==digest(binding)
               and all(confirmation.get(k)==v for k,v in binding.items()))
        preflight=result.get('preflight_confirmation')
        if preflight:
            checked=preview(claim,files,decision['binding']['arguments'],result.get('evaluation_intent'))
            valid=valid and preflight.get('confirmed') is True and preflight.get('binding_hash')==checked['binding_hash'] and preflight.get('arguments')==checked['arguments']
        if not valid:return {'matches':False,'reason':'Confirmation does not bind the replayed inputs, arguments and claim'}
        expected='clear'
    actual=(result.get('verdict') or {}).get('verdict')
    return {'matches':actual==expected,'expected':expected,'recorded':actual,
            'meaning':'Decision consistency only. A recorded confirmation does not authenticate its author or establish scientific meaning.'}


def assess_receipt(result, files):
    """Recompute with installed trusted code, never source supplied by a receipt."""
    from .primitives import measure, VERSION
    fields=('primitive','version','arguments','input_hashes','output')
    try:
        records=result.get('primitive_measurements') or {}
        if result.get('engine_version')!='primitive-v4':
            return {'matches':False,'reason':'Historical engine: use its original verifier','historical':True}
        if len(records)!=1:raise ValueError('Exactly one entity measurement is required')
        computed={}
        for mid,record in records.items():
            if record.get('primitive')!='entity_overlap' or record.get('version')!=VERSION or record.get('execution_error'):
                raise ValueError('Unsupported or failed measurement')
            fresh=measure('entity_overlap',files,record['arguments'])
            if any(record.get(k)!=fresh.get(k) for k in fields):raise ValueError('Retained measurement disagrees with original inputs')
            computed[mid]=fresh
        verdict=verify_verdict(result,computed,files)
        if not verdict['matches']:raise ValueError(verdict.get('reason','Recorded verdict disagrees with recomputed evidence'))
        # Check any claimed replay against its retained record, not the boolean alone.
        for replay in result.get('primitive_replays') or []:
            if replay.get('matches') is not True:continue
            original=records.get(replay.get('measurement_id'));retained=replay.get('record') or {}
            if original is None or retained.get('execution_error') or any(original.get(k)!=retained.get(k) for k in fields):
                raise ValueError('Claimed replay does not match its retained measurement')
        return {'matches':True,'verdict':verdict['expected'],'meaning':'Local recomputation matches. Authorship and identity meaning remain unverified.'}
    except (ValueError,KeyError,TypeError,AttributeError) as exc:
        return {'matches':False,'reason':str(exc)}
