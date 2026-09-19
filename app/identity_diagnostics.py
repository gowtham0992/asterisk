"""Display-only identity-format warnings; never normalize measurement inputs."""
import unicodedata
from .audit import table


def identity_formats(files,args):
    _,split=table(files[args['split_file']]);_,mapping=table(files[args['mapping_file']])
    labels=set(args['train_values']+args['test_values'])
    selected={r[args['sample_column']] for r in split if r[args['partition_column']] in labels}
    values={r[args['entity_column']] for r in mapping if r[args['mapping_sample_column']] in selected and r[args['entity_column']]}
    groups={}
    for value in sorted(values):
        key=unicodedata.normalize('NFKC',unicodedata.normalize('NFKC',value).casefold()).strip()
        groups.setdefault(key,[]).append(value)
    collisions=[v for v in groups.values() if len(v)>1]
    count=sum(len(v) for v in collisions)
    return {'available':True,'identity_count':count,'collision_groups':len(collisions),
            'examples':[{'exact_values':v[:6],'variants':len(v)} for v in collisions[:5]],
            'examples_truncated':len(collisions)>5 or any(len(v)>6 for v in collisions[:5]),
            'scope':'Mapped identities of selected training/evaluation rows only. Display diagnostic; exact input values and verdict are unchanged.',
            'message':f'{count} distinct identity values differ only by case, spacing or Unicode form. Review their scientific meaning before confirming.' if count else '',
            'normalization':'NFKC, casefold, NFKC, strip (diagnostic only)'}
