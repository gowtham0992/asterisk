"""Pinned WSI-Bench report preparation through local JSON field projection.

Offline recorded-spec development check only. Raw narrative fields stay local.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.check_dermamnist_preparation import project_source_files
from app.preparation.intake import open_inputs,validate_files
from app.preparation.projection import validate_projection
from app.preparation.draft import save,restore
from app.primitives import measure
HASHES={'train':'7c49ff5701155f4fbac33c15e628c2be5c38bd35689511220b7d4764a982d393','test':'1a571bd5503e0c3c5072fbb8f270a13569e6add81e8828a7715c2a339dbb28b9'}


def run(directory):
    raw={};images={};sources=[]
    for side,digest in HASHES.items():
        name=f'Report_all_type_all_{side}_single.json';data=(directory/name).read_bytes()
        if hashlib.sha256(data).hexdigest()!=digest:raise ValueError('WSI pinned input hash mismatch')
        raw[name]=data.decode('utf-8');rows=json.loads(raw[name]);images[side]=[row['image'].rsplit('/',1)[-1] for row in rows]
        if len(set(images[side]))!=len(rows) or any(not name.startswith('TCGA-') or len(name)<12 for name in images[side]):raise ValueError('Unexpected or duplicate WSI observation identifier')
        sources.append({'file':name,'format':'json','sample':{'column':'image','basename':True},'entity':{'column':'image','basename':True,'prefix':12},'partition':{'value':side}})
    patients={side:{s[:12] for s in values} for side,values in images.items()};shared=patients['train']&patients['test']
    reference={'shared_entities':len(shared),'affected_test_rows':sum(s[:12] in shared for s in images['test']),'train_rows':len(images['train']),'test_rows':len(images['test'])}
    projected=project_source_files(raw,{name:['image'] for name in raw});files=projected['files'];validate_files(files);validate_projection(projected['projection'],files)
    files['interpretation.txt']='Developer-supplied interpretation: each image basename identifies a slide. The first 12 characters of its TCGA barcode identify a patient. Training/test membership is the source filename. Recorded development specification, not model inference or independent human confirmation.'
    spec={'status':'extract','sources':sources,'citations':[{'file':'interpretation.txt','start_line':1,'end_line':1}]}
    session=open_inputs(json.dumps(spec),files);session.preview({s['file']:{'sample':s['sample'],'repeats':'distinct','evidence':spec['citations']} for s in sources})
    reopened=restore(save(session,session.review['review_hash']));assert reopened.confirmation is None
    extraction=reopened.review['extraction'];output=measure('entity_overlap',extraction['files'],extraction['arguments'])['output']
    if any(output[k]!=v for k,v in reference.items()):raise ValueError('Prepared measurement differs from separate reference')
    return {'dataset':'WSI-Bench report task','status':'matches','execution':'offline developer check; no inference, Sandbox or scientific confirmation','specification_origin':'recorded developer specification; exposed development dataset','measurement':reference,'shared_slides':len(set(images['train'])&set(images['test'])),'test_patients':len(patients['test']),'projection':projected['projection'],'projected_sizes':{name:len(text.encode()) for name,text in projected['files'].items() if name in raw},'draft_reopen_matches':True,'scope':'Product JSON projection, extraction, draft persistence and local measurement. Not a live receipt or fresh model acceptance.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source-dir',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();result=run(args.source_dir)
    with args.output.open('x') as out:json.dump(result,out,indent=2)
    print(json.dumps({'measurement':result['measurement'],'projected_sizes':result['projected_sizes']}))


if __name__=='__main__':main()
