"""Deterministic entity-independence audit. Standard library only; portable in exports."""
import csv
import hashlib
import io
from collections import defaultdict


class AuditError(ValueError):
    pass


def table(content):
    reader = csv.DictReader(io.StringIO(content.lstrip('\ufeff')), strict=True)
    fields = reader.fieldnames
    if not fields or len(set(fields)) != len(fields) or any(not f for f in fields):
        raise AuditError('CSV headers must be nonempty and unique.')
    rows = []
    try:
        for i, row in enumerate(reader, 2):
            if i > 100001 or (i-1)*len(fields) > 2_000_000:
                raise AuditError('Each CSV may contain at most 100,000 data rows and 2,000,000 cells.')
            if None in row or any(v is None for v in row.values()):
                raise AuditError(f'CSV row {i} does not match its headers.')
            if any(len(v) > 2000 for v in row.values()):
                raise AuditError('CSV cells may contain at most 2,000 characters.')
            rows.append(row)
    except csv.Error as exc:
        raise AuditError('Malformed CSV.') from exc
    if not rows:
        raise AuditError('A CSV needs at least one data row.')
    if len(fields) > 80:
        raise AuditError('A CSV may contain at most 80 columns.')
    return fields, rows


def validate_binding(plan, files):
    """Validate declared roles and cardinalities without inferring scientific meaning."""
    sf = plan.get('split_file'); mf = plan.get('mapping_file') or sf
    if sf not in files or mf not in files:
        raise AuditError('The selected split or mapping file is missing.')
    sh, rows = table(files[sf]); mh, mapping = table(files[mf])
    sample, partition = plan.get('sample_column'), plan.get('partition_column')
    join = plan.get('mapping_sample_column') or sample
    entity = plan.get('entity_column')
    if sample not in sh or partition not in sh or join not in mh or entity not in mh:
        raise AuditError('A selected binding column is absent from its table.')
    values = [r[sample] for r in rows]
    distinct = len(set(values)); blanks = sum(not v for v in values)
    detail = f'{sf}.{sample} has {distinct} distinct values across {len(rows)} rows ({blanks} blank).'
    if sample == partition:
        raise AuditError(f'Invalid sample binding: {detail} Sample and partition columns must differ. Choose the row identifier; no data defect has been established.')
    if distinct != len(rows) or blanks:
        raise AuditError(f'Invalid sample binding: {detail} Duplicate or blank sample IDs: IDs must be unique and nonblank. Review the selected column or supply an unambiguous split table.')
    train, test = plan.get('train_values'), plan.get('test_values')
    if not isinstance(train,list) or not isinstance(test,list) or not train or not test or any(not isinstance(v,str) or not v for v in train+test):
        raise AuditError('Select nonempty training and evaluation labels.')
    if set(train) & set(test): raise AuditError('Training and evaluation labels must be disjoint.')
    labels = {r[partition] for r in rows}
    if not set(train+test) <= labels: raise AuditError('A selected partition label is absent from the split table.')
    index = {}
    for r in mapping:
        if not r[join] or not r[entity]: continue
        if r[join] in index and index[r[join]] != r[entity]:
            raise AuditError(f'{mf}.{join} maps one sample to conflicting {entity} values.')
        index[r[join]] = r[entity]
    return {'sample_column': sample, 'distinct': distinct, 'rows': len(rows)}


def execute(plan, files):
    """Accept an explicit contract; never execute supplied or model-generated code."""
    validate_binding(plan, files)
    required = ['split_file', 'sample_column', 'partition_column', 'entity_column']
    if any(not plan.get(k) for k in required):
        raise AuditError('The audit rule is missing a required field.')
    sf = plan['split_file']
    mf = plan.get('mapping_file') or sf
    if sf not in files or mf not in files:
        raise AuditError('A referenced data file is missing.')
    sh, splits = table(files[sf])
    mh, mapping = table(files[mf])
    sample = plan['sample_column']
    partition = plan['partition_column']
    mapping_sample = plan.get('mapping_sample_column') or sample
    entity = plan['entity_column']
    if sample not in sh or partition not in sh or mapping_sample not in mh or entity not in mh:
        raise AuditError('A rule references a column that does not exist.')
    train_values, test_values = set(plan['train_values']), set(plan['test_values'])
    if not train_values or not test_values or train_values & test_values:
        raise AuditError('Training and evaluation labels must be nonempty and disjoint.')
    index = {}
    for line, row in enumerate(mapping, 2):
        sid, eid = row[mapping_sample], row[entity]
        if not sid or not eid:
            continue
        if sid in index and index[sid][0] != eid:
            raise AuditError(f'A sample maps to conflicting entities in {mf}.')
        index[sid] = (eid, line)
    train, test = defaultdict(list), defaultdict(list)
    sample_train, sample_test = set(), set()
    missing, seen = [], set()
    counts = {'train': 0, 'test': 0, 'ignored': 0}
    for line, row in enumerate(splits, 2):
        label, sid = row[partition], row[sample]
        if label not in train_values | test_values:
            counts['ignored'] += 1
            continue
        if not sid:
            raise AuditError(f'A sample ID is missing in {sf} at row {line}.')
        if sid in seen:
            raise AuditError('Duplicate sample IDs in the split manifest make membership ambiguous.')
        seen.add(sid)
        group = 'train' if label in train_values else 'test'
        counts[group] += 1
        (sample_train if group == 'train' else sample_test).add(sid)
        if sid not in index:
            missing.append({'sample': sid, 'split_row': line})
            continue
        eid, source_line = index[sid]
        (train if group == 'train' else test)[eid].append({'sample': sid, 'split_row': line, 'mapping_row': source_line})
    if not counts['train'] or not counts['test']:
        raise AuditError('The selected labels must identify at least one training and one evaluation row.')
    overlap = sorted(train.keys() & test.keys())
    affected = sum(len(test[e]) for e in overlap)
    witnesses = [{'entity': e, 'train': train[e][0], 'test': test[e][0]} for e in overlap[:30]]
    status = 'overlap' if overlap else ('incomplete' if missing else 'clear')
    return {
        'status': status, 'train_rows': counts['train'], 'test_rows': counts['test'],
        'ignored_rows': counts['ignored'], 'train_entities': len(train), 'test_entities': len(test),
        'shared_entities': len(overlap), 'shared_sample_ids': len(sample_train & sample_test),
        'affected_test_rows': affected, 'affected_percent': round(affected / counts['test'] * 100, 2),
        'mapping_coverage_percent': round((len(seen) - len(missing)) / len(seen) * 100, 2),
        'missing_count': len(missing), 'missing_examples': missing[:10], 'witnesses': witnesses,
        'scope': 'Exact, case-sensitive entity IDs; selected training and evaluation labels only. No inference about patient independence, duplicate images, or model accuracy.',
        'hashes': {name: hashlib.sha256(value.encode()).hexdigest() for name, value in files.items()},
        'executor': 'Asterisk deterministic entity audit v1',
    }
