"""Compare recorded split inputs without claiming causal or scientific improvement."""
import hashlib
from .audit import table, validate_binding


def snapshot(a):
    result=a.get('result') or {}
    records=[r for r in result.get('primitive_measurements',{}).values() if r.get('primitive')=='entity_overlap']
    if len(records)!=1:raise ValueError('Complete one entity measurement on each revision first.')
    record=records[0];files={f['name']:f['content'] for f in a['input']['files']}
    hashes={n:hashlib.sha256(t.encode()).hexdigest() for n,t in files.items()}
    if record.get('input_hashes')!=hashes:raise ValueError('Saved inputs do not match their measurement.')
    args=record['arguments'];validate_binding(args,files)
    sf=args['split_file'];mf=args.get('mapping_file') or sf;join=args.get('mapping_sample_column') or args['sample_column']
    _,rows=table(files[sf]);_,mapping=table(files[mf])
    ids={r[join]:r[args['entity_column']] for r in mapping if r[join] and r[args['entity_column']]}
    samples={r[args['sample_column']]:r[args['partition_column']] for r in rows}
    groups={side:{s for s,p in samples.items() if p in args[key]} for side,key in [('train','train_values'),('test','test_values')]}
    shared={ids[s] for s in groups['train'] if s in ids}&{ids[s] for s in groups['test'] if s in ids}
    affected={s for s in groups['test'] if ids.get(s) in shared}
    selected=groups['train']|groups['test'];missing=selected-ids.keys()
    output=record.get('output') or {}
    if not output.get('available') or output.get('shared_entities')!=len(shared) or output.get('affected_test_rows')!=len(affected):
        raise ValueError('Recorded counts do not agree with the retained source tables.')
    return {'args':args,'samples':samples,'ids':ids,'shared':shared,'affected':affected,'groups':groups,
            'missing':missing,'hashes':hashes,'claim':a['input']['claim'],
            'confirmation':result.get('preflight_confirmation') or result.get('binding_confirmation'),
            'replay_recorded':any(r.get('matches') is True for r in result.get('primitive_replays',[]))}


def compare_receipts(before,after):
    try:a,b=snapshot(before),snapshot(after)
    except (ValueError,KeyError,TypeError) as exc:return {'available':False,'reason':str(exc)}
    common=a['samples'].keys()&b['samples'].keys()
    added=sorted(b['samples'].keys()-a['samples'].keys());removed=sorted(a['samples'].keys()-b['samples'].keys())
    moved=[{'sample':s,'before':a['samples'][s],'after':b['samples'][s]} for s in sorted(common) if a['samples'][s]!=b['samples'][s]]
    remapped=[{'sample':s,'before':a['ids'].get(s),'after':b['ids'].get(s)} for s in sorted(a['samples'].keys()|b['samples'].keys()) if a['ids'].get(s)!=b['ids'].get(s)]
    same_binding=a['args']==b['args'];same_claim=a['claim']==b['claim'];same_ids=not remapped
    same_universe=not added and not removed
    shared_comparable=same_binding and same_claim and same_ids
    def summary(s):
        return {'shared_identities':len(s['shared']),'affected_evaluation_rows':len(s['affected']),
                'evaluation_rows':len(s['groups']['test']),'training_rows':len(s['groups']['train']),
                'ignored_rows':len(s['samples'])-len(s['groups']['train']|s['groups']['test']),'unmapped_selected_rows':len(s['missing']),'confirmation_recorded':bool(s['confirmation']),
                'replay_recorded':s['replay_recorded']}
    return {'available':True,'before':summary(a),'after':summary(b),
            'same_claim':same_claim,'same_binding':same_binding,'same_identity_assignments':same_ids,'same_sample_universe':same_universe,
            'partition_only_change':shared_comparable and same_universe,
            'shared_identity_comparison_available':shared_comparable,
            'resolved_identities':sorted(a['shared']-b['shared']) if shared_comparable else None,
            'introduced_identities':sorted(b['shared']-a['shared']) if shared_comparable else None,
            'persisting_identities':sorted(a['shared']&b['shared']) if shared_comparable else None,
            'evaluation_rows_added':sorted(b['groups']['test']-a['groups']['test']),
            'evaluation_rows_removed':sorted(a['groups']['test']-b['groups']['test']),
            'samples_added':added,'samples_removed':removed,'partition_moves':moved,'identity_changes':remapped,
            'changed_files':sorted(n for n in a['hashes'].keys()|b['hashes'].keys() if a['hashes'].get(n)!=b['hashes'].get(n)),
            'scope':'Changes in exact recorded identities and partition membership. No accuracy effect, causal improvement or scientific validity is established.'}
