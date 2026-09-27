"""Verified local preparation export. Creates inputs, never a scientific receipt."""
import argparse
import io
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from .verify_record import verify
from .review import executor


def files_for(record):
    verify(record)
    extraction=record['review']['extraction']
    files=dict(extraction['files'])
    files['asterisk.json']=json.dumps({'schema_version':1,'arguments':extraction['arguments']},indent=2)
    files['preparation-review.json']=json.dumps(record,ensure_ascii=False,separators=(',',':'),allow_nan=False)
    files['README.md']='''# Reviewed preparation inputs

These tables were derived by the experimental Asterisk preparation workflow.
They are inputs for a new check, not an overlap verdict or a certified dataset.

1. Choose this prepared-input ZIP in Asterisk's new split receipt form.
   The app server unpacks it in memory without contacting a model.
2. Write your evaluation claim and name the subject that should be unseen.
3. Keep manual column setup. Review the selected columns and labels again.
4. Confirm their meaning only after reading the original documentation.

splits.csv contains derived sample and partition values. entities.csv maps each
derived sample to its reviewed entity value. These names describe output roles;
they do not establish what an entity means scientifically.

preparation-review.json retains original source text, citations, the starting
proposal, reviewed decisions and extraction lineage. Recompute it with the local
prototype verifier. The preparation confirmation records a local action without
verified reviewer identity. It is not transferred to the new split check.

Review all included files before authorizing any external upload in Asterisk.
No provider request or scientific measurement occurs when exporting this folder.
'''
    sizes={name:len(text.encode('utf-8')) for name,text in files.items()}
    if any(size>10_000_000 for size in sizes.values()) or sum(sizes.values())>16_000_000:
        raise ValueError('Prepared inputs exceed the main workspace import bounds; no files exported')
    return files


def archive(record):
    files=files_for(record)
    output=io.BytesIO()
    with ZipFile(output,'w',compression=ZIP_DEFLATED) as bundle:
        for name,text in files.items():bundle.writestr(name,text.encode('utf-8'))
    return output.getvalue()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('record',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    if args.record.stat().st_size>32_000_000:raise ValueError('Review record exceeds 32 MB')
    record=json.loads(args.record.read_text(),object_pairs_hook=executor.unique)
    data=archive(record)
    # Build and verify first; never replace an existing archive.
    with args.output.open('xb') as target:target.write(data)
    print('Verified preparation inputs exported. A new binding confirmation is required.')


if __name__=='__main__':main()
