"""Read-only witness inspection from retained, hash-matched CSV inputs."""
import hashlib
from .audit import table


def inspect_witness(record, files, index):
    if record.get('primitive') != 'entity_overlap':
        raise ValueError('This measurement does not contain entity witnesses.')
    hashes = {name: hashlib.sha256(content.encode()).hexdigest() for name, content in files.items()}
    if hashes != record.get('input_hashes'):
        raise ValueError('Saved inputs no longer match this measurement. Inspection is unavailable.')
    args = record['arguments']
    witnesses = record['output'].get('witnesses', [])
    if type(index) is not int or not 0 <= index < len(witnesses):
        raise LookupError('Witness not found.')
    witness = witnesses[index]
    split_file = args['split_file']
    mapping_file = args.get('mapping_file') or split_file
    join = args.get('mapping_sample_column') or args['sample_column']
    split_columns, splits = table(files[split_file])
    mapping_columns, mapping = table(files[mapping_file])

    def source(name, columns, rows, number, highlights):
        if type(number) is not int or not 2 <= number <= len(rows) + 1:
            raise ValueError('Saved witness has an invalid CSV row reference.')
        return {'file': name, 'csv_row': number, 'values': rows[number - 2],
                'columns': columns, 'highlights': highlights}

    sides = {}
    for side, labels in [('train', args['train_values']), ('test', args['test_values'])]:
        ref = witness[side]
        split = source(split_file, split_columns, splits, ref['split_row'],
                       [args['sample_column'], args['partition_column']])
        mapped = source(mapping_file, mapping_columns, mapping, ref['mapping_row'],
                        [join, args['entity_column']])
        if not (split['values'][args['partition_column']] in labels
                and split['values'][args['sample_column']] == ref['sample'] == mapped['values'][join]
                and mapped['values'][args['entity_column']] == witness['entity']
                and not set(args['train_values']) & set(args['test_values'])):
            raise ValueError('Saved witness does not agree with its source rows and selected partitions.')
        sides[side] = {'sample': ref['sample'], 'split': split, 'mapping': mapped}
    return {'entity': witness['entity'], 'entity_column': args['entity_column'],
            'sides': sides, 'input_hashes_verified': True,
            'scope': 'These rows share the recorded identity. Whether that identity represents the unit in your claim depends on the reviewed binding.',
            'row_numbering': 'CSV rows count records, including the header as row 1. A quoted multiline cell is one record.'}
