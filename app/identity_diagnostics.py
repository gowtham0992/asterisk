"""Display-only identity-format warnings; never normalize measurement inputs."""
import unicodedata
from .audit import table


def identity_formats(files,args):
    _,split=table(files[args['split_file']]);_,mapping=table(files[args['mapping_file']])
    labels=set(args['train_values']+args['test_values'])
    selected={r[args['sample_column']] for r in split if r[args['partition_column']] in labels}
    values={r[args['entity_column']] for r in mapping if r[args['mapping_sample_column']] in selected and r[args['entity_column']]}
    groups={};mixed=[];invisible=[]
    for value in sorted(values):
        visible=''.join(c for c in value if unicodedata.category(c)!='Cf')
        if visible!=value:invisible.append(value)
        scripts={unicodedata.name(c,'').split(' ')[0] for c in value if unicodedata.name(c,'').startswith(('LATIN ','CYRILLIC ','GREEK '))}
        if len(scripts)>1:mixed.append(value)
        key=unicodedata.normalize('NFKC',unicodedata.normalize('NFKC',visible).casefold()).strip()
        groups.setdefault(key,[]).append(value)
    collisions=[v for v in groups.values() if len(v)>1]
    count=len({x for group in collisions for x in group}|set(mixed)|set(invisible))
    examples=[{'exact_values':v[:6],'variants':len(v)} for v in collisions]
    examples += [{'exact_values':[v],'reason':'Invisible format character'} for v in invisible]
    examples += [{'exact_values':[v],'reason':'Mixed Latin, Greek or Cyrillic scripts; inspect intent'} for v in mixed]
    return {'available':True,'identity_count':count,'collision_groups':len(collisions),
            'examples':examples[:5],
            'examples_truncated':len(examples)>5 or any(len(v)>6 for v in collisions[:5]),
            'scope':'Mapped identities of selected training/evaluation rows only. Display diagnostic; exact input values and verdict are unchanged.',
            'message':f'{count} distinct identity values have case/spacing/Unicode variants, invisible format characters, or mixed Latin/Greek/Cyrillic scripts. These can be intentional. Review exact values and their scientific meaning; this is not comprehensive confusable detection.' if count else '',
            'normalization':'Remove Cf characters, NFKC, casefold, NFKC, strip (diagnostic only)'}
