"""Bounded source examples for review, never verdict evidence or a completeness claim."""
from .audit import table


def source_examples(files, args):
    _, split = table(files[args['split_file']])
    chosen = []
    counts = {'train': 0, 'test': 0}
    for index, row in enumerate(split, 2):
        label = row[args['partition_column']]
        side = 'train' if label in args['train_values'] else 'test' if label in args['test_values'] else None
        if side is not None and counts[side] < 3:
            counts[side] += 1
            chosen.append({'side': side, 'sample': row[args['sample_column']], 'partition': label, 'split_row': index})
        if all(n == 3 for n in counts.values()):
            break
    wanted = {r['sample'] for r in chosen}
    del split
    _, mapping = table(files[args['mapping_file']])
    matches = {}
    for index, row in enumerate(mapping, 2):
        sample = row[args['mapping_sample_column']]
        if sample in wanted and sample not in matches:
            matches[sample] = {'entity': row[args['entity_column']], 'mapping_row': index}
    for row in chosen:
        row.update(matches.get(row['sample'], {'entity': None, 'mapping_row': None}))
    return {'rows': chosen,
            'scope': 'First three selected rows per partition, in source order. These examples do not establish overlap or complete mapping coverage.',
            'row_numbering': 'CSV record numbers include the header as record 1; multiline records are counted once.'}
