"""Which unit does this split actually hold out?

A ladder measures one evaluation split against several candidate units at once:
the observation, the recording or slide, the subject, the site. A split can be
disjoint at one level and shared at the next; checking a single column cannot
show that.

Every level reuses existing trusted code. The bounded extraction language derives
the sample-to-unit table from native files, including units that exist only inside
identifiers (a filename's basename or a fixed-length prefix such as a TCGA
patient barcode). The entity-overlap checker in ``app.audit`` counts overlap. The
ladder adds no new overlap arithmetic. It adds comparisons across levels:

* which levels are held out and which are shared;
* whether each level nests inside the next (one coarse unit per fine unit);
* whether a zero could have been anything else: one unit per sample, or
  identifier namespaces that never meet;
* which level the stated claim requires, and what the split establishes there.

Nothing here calls a model, the network or a Sandbox. A proposed ladder is
data; its scientific meaning still needs a person to confirm it.
"""
import copy
import hashlib
import html
import json
import re

from .audit import AuditError, execute
from .preparation.review import executor

SCHEMA = 'asterisk-ladder/1'
KINDS = ('observation', 'unit', 'attribute')
MAX_LEVELS = 8
NAME = re.compile(r'^[a-z][a-z0-9_]{0,39}$')
LEADING_TOKEN = re.compile(r'^[^0-9]*')


class LadderError(ValueError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def _exact(obj, required, optional=()):
    if not isinstance(obj, dict) or not set(required) <= obj.keys() or set(obj) - set(required) - set(optional):
        raise LadderError('Unknown or missing ladder fields')


def validate(spec):
    """Return a normalised copy of a ladder spec or raise LadderError."""
    _exact(spec, ['schema', 'claim', 'sources', 'levels', 'citations'], ['agreements'])
    if spec['schema'] != SCHEMA:
        raise LadderError(f'Ladder schema must be {SCHEMA}')
    claim = spec['claim']
    _exact(claim, ['text', 'level'])
    if not isinstance(claim['text'], str) or not 3 <= len(claim['text']) <= 1000:
        raise LadderError('State the claim in 3–1000 characters')
    sources = spec['sources']
    if not isinstance(sources, list) or not 1 <= len(sources) <= 20:
        raise LadderError('A ladder needs 1–20 observation sources')
    names = set()
    for source in sources:
        _exact(source, ['file', 'format', 'sample', 'partition'], ['deduplicate'])
        if source['file'] in names:
            raise LadderError('Source declared twice')
        names.add(source['file'])
    levels = spec['levels']
    if not isinstance(levels, list) or not 2 <= len(levels) <= MAX_LEVELS:
        raise LadderError(f'A ladder compares 2–{MAX_LEVELS} levels')
    seen = set()
    for level in levels:
        _exact(level, ['name', 'kind', 'expression'], ['by_source', 'meaning', 'missing'])
        if level.get('missing', 'reject') not in ('reject', 'unmapped'):
            raise LadderError('missing must be reject or unmapped')
        if not isinstance(level['name'], str) or not NAME.match(level['name']):
            raise LadderError('Level names are lowercase identifiers such as patient or recording')
        if level['name'] in seen:
            raise LadderError('Level names must be unique')
        seen.add(level['name'])
        if level['kind'] not in KINDS:
            raise LadderError('Level kind must be observation, unit or attribute')
        if not isinstance(level['expression'], dict):
            raise LadderError('Each level needs an extraction expression')
        overrides = level.get('by_source', {})
        if not isinstance(overrides, dict) or set(overrides) - names or any(not isinstance(e, dict) for e in overrides.values()):
            raise LadderError('by_source may only override declared observation sources')
        if 'meaning' in level and (not isinstance(level['meaning'], str) or len(level['meaning']) > 400):
            raise LadderError('A level meaning is at most 400 characters')
    kinds = {level['name']: level['kind'] for level in levels}
    if claim['level'] not in kinds:
        raise LadderError('The claim must name one of the ladder levels')
    if kinds[claim['level']] == 'attribute':
        raise LadderError('A claim cannot require an attribute to be unseen; choose a unit level')
    for pair in spec.get('agreements', []):
        if not (isinstance(pair, list) and len(pair) == 2 and set(pair) <= seen and pair[0] != pair[1]):
            raise LadderError('Agreements compare two different declared levels')
    if not isinstance(spec['citations'], list) or len(spec['citations']) > 16:
        raise LadderError('A ladder carries at most 16 citations')
    return copy.deepcopy(spec)


def level_spec(spec, level):
    """The extraction spec that measures one level: the same sources, one entity expression."""
    overrides = level.get('by_source', {})
    return {
        'status': 'extract',
        'sources': [{**copy.deepcopy(source), 'entity': copy.deepcopy(overrides.get(source['file'], level['expression']))}
                    for source in spec['sources']],
        'citations': copy.deepcopy(spec['citations']),
    }


def _namespace_note(values_train, values_test):
    """Zero overlap between identifier families that never share a leading token proves nothing."""
    if not any(ch.isdigit() for v in list(values_train)[:1000] + list(values_test)[:1000] for ch in v):
        return None  # plain labels such as study codes (SC, ST) are not identifier families
    tokens_train = {LEADING_TOKEN.match(v).group(0) for v in values_train}
    tokens_test = {LEADING_TOKEN.match(v).group(0) for v in values_test}
    if tokens_train and tokens_test and not tokens_train & tokens_test:
        return {'train_tokens': sorted(tokens_train)[:5], 'test_tokens': sorted(tokens_test)[:5]}
    return None


def population(spec, files):
    """Samples, partitions and native lineage from the frozen executor, derived once for every level."""
    base = {'status': 'extract', 'citations': copy.deepcopy(spec['citations']),
            'sources': [{**copy.deepcopy(s), 'entity': copy.deepcopy(s['sample'])} for s in spec['sources']]}
    return executor.extract(base, files)


def _record_index(files, spec):
    index = {}
    for source in spec['sources']:
        for row, ref in executor.records(files[source['file']], source['format'], source['file']):
            index[_ref_key(ref)] = row
    return index


def _ref_key(ref):
    return (ref['file'], ref.get('pointer') or ref.get('line_start'))


class _Missing(Exception):
    pass


def _evaluate(expr, row, files, lookups, depth=0, trail=None):
    """The extraction expression grammar over one record: column, basename, field, characters or prefix, one lookup.

    Identical to the frozen executor except that a blank or absent value raises _Missing,
    which the caller may record as unmapped instead of rejecting the whole level.
    A lookup appends the mapping-table records it used to trail, so witnesses can cite them.
    """
    if depth > 1:
        raise LadderError('Nested lookup unsupported')
    if not isinstance(expr, dict):
        raise LadderError('Expression must be an object')
    if 'lookup' in expr:
        executor.exact(expr, ['lookup'])
        q = expr['lookup']
        executor.exact(q, ['file', 'format', 'key_column', 'value_column', 'on'])
        key = (q['file'], q['format'], q['key_column'], q['value_column'])
        if key not in lookups:
            if q['file'] not in files:
                raise LadderError('Lookup file missing')
            table = {}
            for m, mref in executor.records(files[q['file']], q['format'], q['file']):
                if q['key_column'] not in m or q['value_column'] not in m:
                    raise LadderError('Lookup column missing')
                k, v = m[q['key_column']], m[q['value_column']]
                if not (isinstance(k, str) and k):
                    continue
                if k in table and table[k][0] != v:
                    raise LadderError('Conflicting duplicate lookup identity')
                table.setdefault(k, (v, []))[1].append(mref)
            lookups[key] = table
        value = _evaluate(q['on'], row, files, lookups, depth + 1, trail)
        if value not in lookups[key]:
            raise _Missing()
        value, mrefs = lookups[key][value]
        if trail is not None:
            trail.extend(mrefs)
        if not (isinstance(value, str) and value):
            raise _Missing()
        return executor.text(value)
    executor.exact(expr, ['column'], ['basename', 'field', 'characters', 'prefix'])
    if 'characters' in expr and 'prefix' in expr:
        raise LadderError('Use characters or prefix, not both')
    if not isinstance(expr['column'], str):
        raise LadderError('Column missing')
    if expr['column'] not in row:
        raise LadderError(f"Column {expr['column']} missing")
    value = row[expr['column']]
    if value is None or value == '':
        raise _Missing()
    value = executor.text(value)
    if 'basename' in expr:
        if expr['basename'] is not True:
            raise LadderError('basename must be true')
        value = executor.text(executor.posixpath.basename(value))
    if 'field' in expr:
        value = _field(value, expr['field'])
    if 'characters' in expr:
        start, end = _span(expr['characters'], 'characters', 512)
        if len(value) < end:
            raise LadderError(f'An identifier is shorter than {end} characters')
        value = value[start - 1:end]
    if 'prefix' in expr:
        n = expr['prefix']
        if type(n) != int or not 1 <= n <= 128 or len(value) < n:
            raise LadderError('Invalid or short prefix')
        value = value[:n]
    return value


def _span(spec, name, limit):
    """A 1-based inclusive {from, to} range; to defaults to from."""
    if not isinstance(spec, dict):
        raise LadderError(f'{name} must be an object with from and to')
    executor.exact(spec, ['from'], ['to', 'separator'] if name == 'field' else ['to'])
    start, end = spec['from'], spec.get('to', spec['from'])
    if type(start) != int or type(end) != int or not 1 <= start <= end <= limit:
        raise LadderError(f'{name} needs whole positions from 1, with to at least from')
    return start, end


def _field(value, spec):
    """Fields `from`..`to` of a separated identifier, rejoined with the separator (e.g. city and location)."""
    start, end = _span(spec, 'field', 32)
    separator = spec.get('separator') if isinstance(spec, dict) else None
    if not isinstance(separator, str) or not 1 <= len(separator) <= 3:
        raise LadderError('field needs a separator of 1-3 characters')
    parts = value.split(separator)
    if len(parts) < end:
        raise LadderError(f'An identifier has fewer than {end} fields separated by {separator!r}')
    return separator.join(parts[start - 1:end])


def _ref(ref):
    return {'file': ref['file'], 'at': ref.get('pointer') or f"line {ref['line_start']}"}


def _derive(spec, level, files, base, index, trails=None):
    overrides = level.get('by_source', {})
    allow_missing = level.get('missing', 'reject') == 'unmapped'
    lookups, values, missing = {}, {}, []
    for row in base['lineage']:
        source = row['occurrences'][0]['file']
        expr = overrides.get(source, level['expression'])
        seen = set()
        for occurrence in row['occurrences']:
            trail = []
            try:
                seen.add(_evaluate(expr, index[_ref_key(occurrence)], files, lookups, trail=trail))
            except _Missing:
                seen.add(None)
            except executor.ExtractionError as exc:
                raise LadderError(str(exc)) from None
            if trails is not None and trail:
                trails.setdefault(row['sample'], []).extend(_ref(r) for r in trail if _ref(r) not in trails.get(row['sample'], []))
        if len(seen) > 1:
            raise LadderError(f"Repeated occurrences of sample {row['sample']} disagree on {level['name']}")
        value = seen.pop()
        if value is None:
            if not allow_missing:
                raise LadderError(f"Sample {row['sample']} has no {level['name']} value; declare missing: unmapped to count it as unmapped")
            missing.append(row['sample'])
        else:
            values[row['sample']] = value
    return values, missing


def _csv(fields, rows):
    import csv, io
    out = io.StringIO()
    w = csv.writer(out, lineterminator='\n')
    w.writerow(fields)
    w.writerows(rows)
    return out.getvalue()


def _measure(spec, level, files, base, index):
    trails = {}
    values, missing = _derive(spec, level, files, base, index, trails)
    lineage = {row['sample']: row for row in base['lineage']}
    tables = {'splits.csv': _csv(['sample', 'partition'], [(r['sample'], r['partition']) for r in base['lineage']]),
              'entities.csv': _csv(['sample', 'entity'], sorted(values.items()))}
    if not values:
        raise LadderError(f"No sample has a {level['name']} value")
    result = execute(base['arguments'], tables)
    selected = [r for r in base['lineage'] if r['partition'] in ('train', 'test')]
    mapped = {side: {values[r['sample']] for r in selected if r['partition'] == side and r['sample'] in values}
              for side in ('train', 'test')}
    witnesses = []
    for witness in result['witnesses'][:3]:
        pair = {'unit': witness['entity']}
        for side in ('train', 'test'):
            sample = witness[side]['sample']
            refs = [_ref(o) for o in lineage[sample]['occurrences'][:2]] + trails.get(sample, [])[:2]
            pair[side] = {'sample': sample, 'unit_source': refs}
        witnesses.append(pair)
    selected_missing = sum(1 for s in missing if lineage[s]['partition'] in ('train', 'test'))
    return {
        'status': 'measured',
        'shared': result['shared_entities'],
        'affected_test_rows': result['affected_test_rows'],
        'train_rows': result['train_rows'],
        'test_rows': result['test_rows'],
        'excluded_rows': result['ignored_rows'],
        'train_units': len(mapped['train']),
        'test_units': len(mapped['test']),
        'unmapped_rows': selected_missing,
        'test_units_seen_in_train_percent': round(100 * result['shared_entities'] / len(mapped['test']), 2) if mapped['test'] else None,
        'one_unit_per_sample': level['kind'] == 'unit' and not selected_missing and len(mapped['train'] | mapped['test']) == len(selected),
        'disjoint_namespaces': None if result['shared_entities'] or level['kind'] == 'observation' else _namespace_note(mapped['train'], mapped['test']),
        'witnesses': witnesses,
        '_samples': {r['sample']: values[r['sample']] for r in selected if r['sample'] in values},
    }


def _nesting(finer, coarser):
    parents = {}
    for sample, value in finer['_samples'].items():
        parents.setdefault(value, set()).add(coarser['_samples'].get(sample))
    split = {value: sorted(p for p in ps if p is not None) for value, ps in parents.items() if len(ps) > 1}
    return {'violations': len(split), 'examples': [{'unit': k, 'parents': v[:4]} for k, v in sorted(split.items())[:5]]}


def measure(spec, files, confirmed=()):
    """Measure every level of a validated ladder against the same files.

    confirmed names the levels whose meaning a person has confirmed; only then can the claim read "held out"."""
    spec = validate(spec)
    confirmed = tuple(confirmed)
    unknown = set(confirmed) - {level['name'] for level in spec['levels']}
    if unknown:
        raise LadderError(f'Confirmed levels are not in the ladder: {", ".join(sorted(unknown))}')
    try:
        base = population(spec, files)
    except executor.ExtractionError as exc:
        raise LadderError(f'The observation sources could not be read: {exc}') from None
    index = _record_index(files, spec)
    rows = []
    for level in spec['levels']:
        row = {'name': level['name'], 'kind': level['kind'], 'meaning': level.get('meaning', '')}
        try:
            row.update(_measure(spec, level, files, base, index))
        except (LadderError, AuditError, executor.ExtractionError) as exc:
            row.update({'status': 'unavailable', 'reason': str(exc)})
        rows.append(row)
    consistent = True  # every level is derived over the same executor-derived population
    units = [r for r in rows if r['kind'] != 'attribute']
    for finer, coarser in zip(units, units[1:]):
        if finer['status'] == coarser['status'] == 'measured':
            coarser['nests_previous'] = _nesting(finer, coarser)
    agreements = []
    by_name = {r['name']: r for r in rows}
    for a, b in spec.get('agreements', []):
        ra, rb = by_name[a], by_name[b]
        if ra['status'] == rb['status'] == 'measured':
            differ = sorted(s for s in ra['_samples'] if ra['_samples'][s] != rb['_samples'].get(s))
            agreements.append({'levels': [a, b], 'disagreements': len(differ),
                               'examples': [{'sample': s, a: ra['_samples'][s], b: rb['_samples'].get(s)} for s in differ[:5]]})
        else:
            agreements.append({'levels': [a, b], 'disagreements': None, 'examples': []})
    claim = _claim(spec, by_name, consistent, confirmed)
    for r in rows:
        r.pop('_samples', None)
    return {
        'schema': SCHEMA + '-result',
        'claim': spec['claim'],
        'finding': claim,
        'confirmed_levels': sorted(confirmed),
        'headline': _headline(rows, spec['claim']['level']),
        'levels': rows,
        'population_consistent': consistent,
        'population': {side: sum(1 for r in base['lineage'] if r['partition'] == side) for side in ('train', 'test', 'excluded')},
        'agreements': agreements,
        'spec_hash': digest(spec),
        'input_hashes': {name: hashlib.sha256(content.encode()).hexdigest() for name, content in sorted(files.items())},
        'scope': ('Exact recorded identifiers under the stated derivations. A person must confirm what each level '
                  'means before the claim level can count as held out. No content similarity, preprocessing or '
                  'accuracy effect is measured.'),
    }


def _by_construction(spec, target):
    """Reasons zero overlap at the claim level cannot fail whatever the data say."""
    reasons = []
    level = next(l for l in spec['levels'] if l['name'] == target['name'])
    if level['kind'] == 'observation':
        reasons.append(f'The claim is bound to {target["name"]}, the observation itself; every sample is unique, so '
                       f'zero overlap is guaranteed. Bind the claim to the unit it names, such as patient or recording.')
    for source in spec['sources']:
        column = source['partition'].get('column')
        expr = level.get('by_source', {}).get(source['file'], level['expression'])
        if column and expr.get('column') == column and set(expr) <= {'column', 'basename', 'prefix'}:
            reasons.append(f'In {source["file"]} the partition is read from the column that defines {target["name"]} '
                           f'({column}), so separation is guaranteed. Use the recorded split assignment instead.')
    return reasons


def _claim(spec, levels, consistent, confirmed=()):
    target = levels[spec['claim']['level']]
    name = target['name']
    if not consistent:
        return {'status': 'insufficient', 'level': name,
                'reason': 'Levels were measured over different sample populations; compare like with like first.'}
    if target['status'] != 'measured':
        return {'status': 'insufficient', 'level': name,
                'reason': f'The {name} level could not be derived: {target["reason"]}'}
    if target['shared']:
        return {'status': 'violation', 'level': name,
                'reason': f'{target["shared"]} {name} value(s) occur in training and evaluation, affecting '
                          f'{target["affected_test_rows"]} of {target["test_rows"]} evaluation rows.'}
    if target['unmapped_rows']:
        return {'status': 'insufficient', 'level': name,
                'reason': f'No shared {name} was recorded, but {target["unmapped_rows"]} selected rows have no {name} value; zero overlap cannot establish separation.'}
    warning = ''
    if target['one_unit_per_sample']:
        warning = (f'Every selected sample has its own {name} value, so separation follows automatically. '
                   f'Confirm that this column really names a {name} and is not an image, file or accession identifier.')
    structural = _by_construction(spec, target)
    if structural:
        return {'status': 'not_established', 'level': name, 'reason': ' '.join(structural)}
    if target['disjoint_namespaces']:
        return {'status': 'not_established', 'level': name,
                'reason': (f'Training and evaluation {name} identifiers come from different naming families '
                           f'({", ".join(target["disjoint_namespaces"]["train_tokens"])} vs '
                           f'{", ".join(target["disjoint_namespaces"]["test_tokens"])}); zero overlap cannot show separation.')}
    if name in confirmed:
        return {'status': 'held_out', 'level': name, 'warning': warning, 'confirmable': False,
                'reason': f'No recorded {name} value occurs in both partitions, and a person confirmed that the {name} '
                          f'level names a {name}.'}
    if target['one_unit_per_sample']:
        return {'status': 'not_established', 'level': name, 'warning': warning, 'confirmable': True,
                'reason': f'Every selected sample has its own {name} value, so zero overlap is guaranteed and shows nothing '
                          f'until a person confirms that this column really names a {name}.'}
    return {'status': 'held_out_pending_confirmation', 'level': name, 'warning': warning, 'confirmable': True,
            'reason': f'No recorded {name} value occurs in both partitions. A person must still confirm what {name} means.'}


def _headline(rows, claim_level):
    held, shared, unknown, unavailable = [], [], [], []
    for r in rows:
        if r['kind'] == 'attribute':
            continue
        if r['status'] != 'measured':
            unavailable.append(r['name'])
        elif r['shared'] == 0 and not r['disjoint_namespaces'] and not r['unmapped_rows'] and not r['one_unit_per_sample']:
            held.append(r['name'])
        elif r['shared']:
            shared.append(f"{r['name']} ({r['shared']} shared)")
        else:
            unknown.append(r['name'])
    parts = []
    if held:
        parts.append('Held out: ' + ', '.join(held) + '.')
    if shared:
        parts.append('Shared: ' + ', '.join(shared) + '.')
    if unknown:
        parts.append('Not established: ' + ', '.join(unknown) + '.')
    if unavailable:
        parts.append('Unavailable: ' + ', '.join(unavailable) + '.')
    parts.append(f'Your claim needs {claim_level}.')
    return ' '.join(parts)


STATUS_WORDS = {
    'held_out': 'Held out (meaning confirmed)',
    'violation': 'Not held out',
    'held_out_pending_confirmation': 'Held out, pending confirmation',
    'not_established': 'Not established',
    'insufficient': 'Insufficient evidence',
}


def render(result):
    """A self-contained offline page. Every value is escaped; no scripts or external assets."""
    e = lambda v: html.escape(str(v), quote=True)
    finding = result['finding']
    rows = []
    for r in result['levels']:
        claim = ' is-claim' if r['name'] == result['claim']['level'] else ''
        if r['status'] != 'measured':
            state, detail = 'unknown', e(r['reason'])
        elif r['shared']:
            state = 'shared'
            detail = (f"{e(r['shared'])} of {e(r['test_units'])} evaluation {e(r['name'])} values also in training · "
                      f"{e(r['affected_test_rows'])} of {e(r['test_rows'])} evaluation rows"
                      + (f" · {e(r['unmapped_rows'])} rows without a value" if r['unmapped_rows'] else ''))
        elif r['unmapped_rows']:
            state, detail = 'unknown', f"0 shared, but {e(r['unmapped_rows'])} selected rows have no {e(r['name'])} value"
        elif r['one_unit_per_sample']:
            state, detail = 'held', f"0 shared · one {e(r['name'])} value per sample, so separation is automatic — check the column's meaning"
        elif r['disjoint_namespaces']:
            state, detail = 'unknown', 'Identifier families never meet — zero proves nothing'
        else:
            state = 'held'
            detail = f"0 of {e(r['test_units'])} evaluation {e(r['name'])} values in training"
        nest = r.get('nests_previous')
        nest_note = (f"<small>{e(nest['violations'])} finer units split across several {e(r['name'])} values</small>"
                     if nest and nest['violations'] else '')
        witness = ''
        if r.get('witnesses'):
            w = r['witnesses'][0]
            src = lambda side: '; '.join(f"{e(x['file'])} {e(x['at'])}" for x in w[side]['unit_source'])
            witness = (f"<details><summary>Witness: {e(w['unit'])}</summary><p>Training <code>{e(w['train']['sample'])}</code> "
                       f"({src('train')})<br>Evaluation <code>{e(w['test']['sample'])}</code> ({src('test')})</p></details>")
        rows.append(f"<li class='level {state}{claim}'><span class='kind'>{e(r['kind'])}</span>"
                    f"<strong>{e(r['name'])}</strong><span class='meaning'>{e(r.get('meaning', ''))}</span>"
                    f"<span class='detail'>{detail}</span>{nest_note}{witness}</li>")
    agreements = ''.join(
        f"<li>{e(a['levels'][0])} vs {e(a['levels'][1])}: {e(a['disagreements'])} disagreements</li>"
        for a in result['agreements'])
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'">
<title>Asterisk — which unit does this split hold out?</title>
<style>
body{{margin:0;background:#f4f1e8;color:#16241c;font:16px/1.5 Georgia,serif}}
main{{max-width:880px;margin:0 auto;padding:32px 20px}}
.kicker{{font:12px/1 ui-monospace,monospace;letter-spacing:.08em;text-transform:uppercase;color:#4d5e52}}
h1{{font-size:clamp(28px,5vw,44px);line-height:1.1;margin:.3em 0}}
.finding{{border-left:4px solid #16241c;padding:4px 0 4px 16px;margin:24px 0}}
ol{{list-style:none;padding:0;margin:24px 0;display:grid;gap:10px}}
.level{{display:grid;grid-template-columns:110px 1fr;gap:2px 16px;background:#fbfaf6;border:1px solid #d9d4c5;padding:14px 16px}}
.level strong{{font:600 18px/1.2 system-ui,sans-serif}}
.level .kind{{grid-row:span 3;font:12px ui-monospace,monospace;text-transform:uppercase;color:#4d5e52}}
.level .meaning{{color:#4d5e52;font-size:14px}}
.level .detail{{font:15px system-ui,sans-serif}}
.held{{border-left:6px solid #3f7d4f}} .shared{{border-left:6px solid #b0412e}} .unknown{{border-left:6px solid #b08a2e}}
.is-claim{{outline:2px solid #16241c}}
code{{font:13px ui-monospace,monospace;background:#ece8dc;padding:1px 4px}}
small{{grid-column:2;color:#7a5a1a}} details{{grid-column:2;font-size:14px}}
footer{{font-size:13px;color:#4d5e52;border-top:1px solid #d9d4c5;margin-top:32px;padding-top:12px}}
</style></head><body><main>
<p class="kicker">Asterisk · independence ladder</p>
<h1>{e(result['headline'])}</h1>
<section class="finding"><p class="kicker">{e(STATUS_WORDS[finding['status']])} · claim level: {e(finding['level'])}</p>
<p>{e(result['claim']['text'])}</p><p>{e(finding['reason'])}</p>{f"<p><strong>Check:</strong> {e(finding['warning'])}</p>" if finding.get('warning') else ''}</section>
<ol>{''.join(rows)}</ol>
{f'<h2>Identifier agreement</h2><ul>{agreements}</ul>' if agreements else ''}
<footer><p>{e(result['scope'])}</p><p>Ladder spec {e(result['spec_hash'][:16])}… · inputs: {e(', '.join(f"{k} {v[:12]}…" for k, v in result['input_hashes'].items()))}</p></footer>
</main></body></html>"""
