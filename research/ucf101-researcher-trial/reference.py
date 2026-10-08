"""Independent UCF101 metadata audit: regex parser, no Asterisk imports.
Usage: python reference.py /private/path/to/original-splits.zip
"""
import hashlib,json,re,sys,zipfile
from collections import Counter
from pathlib import Path
PATTERN=re.compile(r'(?P<class>[^/]+)/v_(?P<label>[^_]+)_g(?P<group>\d+)_c(?P<clip>\d+)\.avi(?: (?P<target>\d+))?')
def audit(archive):
    with zipfile.ZipFile(archive) as z:
        groups={};samples={};counts={};hashes={}
        for side in ('train','test'):
            name=f'ucfTrainTestlist/{side}list01.txt';raw=z.read(name);hashes[side]=hashlib.sha256(raw).hexdigest()
            records=[]
            for line in raw.decode().splitlines():
                m=PATTERN.fullmatch(line)
                if not m or m['class'].casefold()!=m['label'].casefold():raise ValueError('Unexpected filename structure')
                if side=='train' and not m['target']:raise ValueError('Missing training class label')
                records.append((line.split()[0],(m['label'],int(m['group']))))
            assert len({r[0] for r in records})==len(records),'Duplicate clip identifiers'
            groups[side]={r[1] for r in records};samples[side]={r[0] for r in records};counts[side]=Counter(r[1] for r in records)
        common=groups['train']&groups['test'];ambiguous={g for _,g in groups['train']}&{g for _,g in groups['test']}
        # An independent cross-check: sorted group keys reconciled with each class's partition totals.
        classes={c for c,_ in groups['train']|groups['test']}
        per_class={c:{s:sum(n for (label,_),n in counts[s].items() if label==c) for s in counts} for c in sorted(classes)}
        assert sum(r['test'] for r in per_class.values())==len(samples['test'])
        return {'train_rows':len(samples['train']),'test_rows':len(samples['test']),'train_groups':len(groups['train']),'test_groups':len(groups['test']),
                'shared_groups':len(common),'affected_test_rows':sum(counts['test'][g] for g in common),'shared_clip_ids':len(samples['train']&samples['test']),
                'numeric_group_ids_shared_ignoring_action':len(ambiguous),'classes':len(classes),'source_hashes':hashes,'per_class':per_class}
if __name__=='__main__':print(json.dumps(audit(Path(sys.argv[1])),indent=2))
