"""Offline development check of browser projection and product preparation.

Pinned real sources stay local. Uses a recorded developer-authored specification,
not a model proposal or human-confirmed scientific receipt. Writes aggregates only.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.reproduce_dermamnist import SOURCES,reproduce
from app.preparation.intake import open_inputs
from app.preparation.draft import save,restore
from app.primitives import measure


def project_source_files(raw, selection):
    # Exercise the exact shipped browser projector without an upload or server.
    program="""
import {readFileSync} from 'node:fs';
import {inspectCSV,projectCSV,projectionRecord} from './static/csv-projection.mjs';
import {inspectJSON,projectJSON} from './static/json-projection.mjs';
const input=JSON.parse(readFileSync(0,'utf8')), files={},projection=[];
for(const [name,text] of Object.entries(input.files)){
 const json=name.toLowerCase().endsWith('.json');
 const table=(json?inspectJSON:inspectCSV)(text),columns=input.selection[name].map(n=>table.headers.indexOf(n));
 const result=(json?projectJSON:projectCSV)(table,columns);files[name]=result.content;
 projection.push(await projectionRecord(name,text,result));
}
process.stdout.write(JSON.stringify({files,projection}));
"""
    result=subprocess.run(['node','--input-type=module','-e',program],cwd=ROOT,
        input=json.dumps({'files':raw,'selection':selection}),text=True,capture_output=True,timeout=30)
    if result.returncode:raise RuntimeError('Local projection failed; no provider was contacted')
    return json.loads(result.stdout)


def run(directory):
    reference=reproduce(directory)
    selection={'dermamnist_split_info.csv':['image_id','split'],
               'HAM10000_metadata.csv':['image_id','lesion_id']}
    raw={}
    for name,digest in SOURCES.items():
        data=(directory/name).read_bytes()
        if hashlib.sha256(data).hexdigest()!=digest:raise ValueError('Pinned input hash mismatch')
        raw[name]=data.decode('utf-8')
    projected=project_source_files(raw,selection);files=projected['files']
    files['interpretation.txt']='Developer-supplied development binding: image_id identifies an image; lesion_id groups images of a lesion. split labels train, test and val are used as published. This is not a model inference or independent scientific confirmation.'
    spec={'status':'extract','sources':[{'file':'dermamnist_split_info.csv','format':'csv',
        'sample':{'column':'image_id'},
        'entity':{'lookup':{'file':'HAM10000_metadata.csv','format':'csv','key_column':'image_id','value_column':'lesion_id','on':{'column':'image_id'}}},
        'partition':{'column':'split','map':{'train':'train','test':'test','val':'excluded'}}}],
        'citations':[{'file':'interpretation.txt','start_line':1,'end_line':1}]}
    session=open_inputs(json.dumps(spec),files)
    session.preview({'dermamnist_split_info.csv':{'sample':spec['sources'][0]['sample'],'repeats':'distinct','evidence':spec['citations']}})
    # Reopen the same product draft format; confirmation intentionally absent.
    reopened=restore(save(session,session.review['review_hash']))
    assert reopened.confirmation is None
    extraction=reopened.review['extraction']
    output=measure('entity_overlap',extraction['files'],extraction['arguments'])['output']
    keys=('shared_entities','affected_test_rows','train_rows','test_rows')
    counts={key:output[key] for key in keys}
    if counts!=reference['measurement']:raise ValueError('Product preparation disagrees with independent reference')
    return {'dataset':'DermaMNIST original split','status':'matches',
        'execution':'offline developer check; no inference, Sandbox or scientific confirmation',
        'specification_origin':'recorded developer specification; exposed development dataset',
        'measurement':counts,'projection':projected['projection'],
        'draft_reopen_matches':True,'lineage_records':len(extraction['lineage']),
        'scope':'Checks product projection, extraction, draft persistence and local measurement. Not a live end-to-end receipt or model acceptance.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=run(args.source_dir)
    with args.output.open('x') as handle:json.dump(result,handle,indent=2)
    print(json.dumps(result['measurement']))


if __name__=='__main__':main()
