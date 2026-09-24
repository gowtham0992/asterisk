"""A human-reviewed binding is the only execution input for a v4 split receipt."""
from datetime import datetime, timezone
from copy import deepcopy
import time
import csv
from pydantic import BaseModel, ConfigDict, Field
from .audit import table, validate_binding
from .primitives import digest, citation
from .probes import Investigation, sha
from .bindings import pending_binding, confirm_binding
from .identity_diagnostics import identity_formats
from .evaluation_intent import supported, describe
from .receipt_context import binding_scope

class EntityBinding(BaseModel):
    model_config = ConfigDict(extra='forbid')
    split_file: str = Field(min_length=1, max_length=300)
    sample_column: str = Field(min_length=1, max_length=2000)
    partition_column: str = Field(min_length=1, max_length=2000)
    train_values: list[str] = Field(min_length=1, max_length=100)
    test_values: list[str] = Field(min_length=1, max_length=100)
    mapping_file: str = Field(min_length=1, max_length=300)
    mapping_sample_column: str = Field(min_length=1, max_length=2000)
    entity_column: str = Field(min_length=1, max_length=2000)


def preview(claim, files, arguments, evaluation_intent=None):
    intent = supported(evaluation_intent)
    args = EntityBinding.model_validate(arguments).model_dump()
    try:
        validate_binding(args, files)
    except ValueError as exc:
        # Structural recovery only: never silently choose a scientific role.
        candidates = []
        try:
            fields, rows = table(files[args['split_file']])
            _, mapping = table(files[args['mapping_file']])
            keys = {r[args['mapping_sample_column']] for r in mapping}
            for column in fields:
                values = [r[column] for r in rows]
                if column != args['partition_column'] and all(values) and len(set(values)) == len(rows) and set(values) & keys:
                    candidates.append(column)
        except (KeyError, ValueError):
            pass
        hint = (' Structural sample-ID candidates: '+', '.join(candidates)+'. These columns are unique, nonblank, and share values with the mapping key. Review their documented meaning; none was selected automatically.') if candidates else ''
        raise ValueError(str(exc)+hint) from exc
    sf, mf = args['split_file'], args['mapping_file']
    _, split = table(files[sf]); _, mapping = table(files[mf])
    counts = {}
    for name, column, rows in [('sample', args['sample_column'], split),
                               ('partition', args['partition_column'], split),
                               ('mapping_sample', args['mapping_sample_column'], mapping),
                               ('entity', args['entity_column'], mapping)]:
        values = [r[column] for r in rows]
        counts[name] = {'column': column, 'rows': len(rows), 'distinct': len(set(values)),
                        'blank': sum(not x for x in values)}
    labels = {v: sum(r[args['partition_column']] == v for r in split)
              for v in set(args['train_values'] + args['test_values'])}
    binding = {'claim': claim, 'arguments': args, 'input_hashes': {n: sha(t) for n,t in files.items()},
               'text': f"{args['entity_column']} in {mf} identifies the generating unit named by this claim. "
                       f"{sf}.{args['sample_column']} joins {mf}.{args['mapping_sample_column']}; "
                       f"compare {args['train_values']} against {args['test_values']} in {args['partition_column']}."}
    if intent is not None:
        binding['evaluation_intent'] = intent
        binding['text'] = f"{args['entity_column']} in {mf} identifies the {intent['unit']} that must be unseen at evaluation. " + binding['text'] + ' ' + describe(intent)
    return {**binding, 'binding_hash': digest(binding), 'columns': counts, 'partition_rows': labels,
            **binding_scope(files, args),
            'identity_diagnostics': identity_formats(files,args),
            'ignored_rows': sum(r[args['partition_column']] not in labels for r in split)}


def profiles(files):
    out = {}
    for name, text in files.items():
        if not name.lower().endswith('.csv'): continue
        try:
            fields, rows = table(text)
            out[name] = {'rows': len(rows), 'columns': {c: {'distinct': len({r[c] for r in rows}),
                'blank': sum(not r[c] for r in rows)} for c in fields}}
        except csv.Error: out[name] = {'error': 'Malformed CSV. Check quotation marks, headers and row lengths.'}
        except ValueError as exc: out[name] = {'error': str(exc)}
    return out


def execute_receipt(claim, files, plan, confirmation, model, runner, on_event=None, evaluation_intent=None):
    started = time.monotonic()
    checked = preview(claim, files, confirmation['arguments'], evaluation_intent)
    if not confirmation.get('confirmed') or checked['binding_hash'] != confirmation['binding_hash']:
        raise ValueError('The confirmed binding no longer matches these inputs.')
    inv = Investigation(files, runner, 'entity_overlap', claim)
    record = inv.dispatch('entity_overlap', checked['arguments'])
    if on_event: on_event({'call': 1, 'tool': 'entity_overlap', 'result': record})
    inv.dispatch('submit_verdict', {'citations': [{'file': c['file'], 'start_line': c['start_line'], 'end_line': c['end_line']} for c in plan['citations']]})
    original = inv.measurements['measurement-1']
    replay = runner.primitive('entity_overlap', checked['arguments'], files)
    matches = not replay.get('execution_error') and all(replay.get(k) == original.get(k) for k in
        ('primitive','version','arguments','input_hashes','implementation_hash','output'))
    if on_event: on_event({'call': 2, 'tool': 'replay_entity_overlap', 'result': {'matches': matches}})
    result = {'evaluation_intent': supported(evaluation_intent), 'evaluation_scope': describe(evaluation_intent), 'claim': claim, 'original_claim': claim, 'model': model, 'engine_version': 'primitive-v4',
        'status': 'completed' if matches else 'incomplete', 'error': None if matches else 'primitive_replay_mismatch',
        'verdict': inv.verdict if matches else None, 'primitive_measurements': inv.measurements,
        'primitive_replays': [{'measurement_id': 'measurement-1', 'matches': matches, 'record': replay}],
        'primitive_sources': getattr(runner,'sources',{}), 'input_hashes': checked['input_hashes'],
        'runtime_sources': dict(getattr(runner,'runtime_sources',{})),
        'identity_diagnostics':checked['identity_diagnostics'],
        'accepted_plan': plan, 'preflight_confirmation': deepcopy(confirmation),
        'seconds': round(time.monotonic()-started,3), 'tool_calls': 2, 'tokens': {'prompt':0,'completion':0},
        'messages': [], 'events': [], 'probes': {}, 'runs': [], 'replays': [],
        'semantic_validation': 'Human-confirmed binding; independent evidence review unmeasured'}
    # Confirmation occurred before execution. Apply it only after matching replay and
    # to the identical inputs/arguments; preserve the primitive's pending outcome.
    pending = pending_binding(result) if matches else None
    if pending:
        result = confirm_binding(result, pending['binding_hash'])
        result['binding_confirmation']['confirmed_at'] = confirmation['confirmed_at']
        result['binding_confirmation']['origin'] = confirmation.get('origin','human_preflight_review')
        result['binding_confirmation']['preflight_binding_hash'] = confirmation['binding_hash']
    return result
