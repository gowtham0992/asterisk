"""Offline pinned PTB-XL preparation check; no model or Sandbox requests."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.check_dermamnist_preparation import project_source_files
from app.preparation.intake import open_inputs
from app.preparation.draft import save,restore
from app.primitives import measure
SOURCE_SHA='7600de9c1b27d181d850b3c6038a35d7c3ddb6bb33b702e3a20252a6859d216b'
SOURCE_URL='https://physionet.org/files/ptb-xl/1.0.3/ptbxl_database.csv'


def run(path):
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SOURCE_SHA:raise ValueError('PTB-XL pinned input hash mismatch')
    text=raw.decode('utf-8');rows=list(csv.DictReader(io.StringIO(text)))
    train=[r for r in rows if r['strat_fold'] in {str(i) for i in range(1,9)}]
    test=[r for r in rows if r['strat_fold']=='10']
    overlap={r['patient_id'] for r in train}&{r['patient_id'] for r in test}
    reference={'shared_entities':len(overlap),'affected_test_rows':sum(r['patient_id'] in overlap for r in test),'train_rows':len(train),'test_rows':len(test)}
    projected=project_source_files({'ptbxl.csv':text},{'ptbxl.csv':['ecg_id','patient_id','strat_fold']})
    files=projected['files'];files['interpretation.txt']='Developer-supplied interpretation of PTB-XL v1.0.3: ecg_id identifies a recording, patient_id identifies a patient, strat_fold 1 through 8 is training, fold 10 is evaluation, and fold 9 is excluded. No model inference or independent human confirmation.'
    spec={'status':'extract','sources':[{'file':'ptbxl.csv','format':'csv','sample':{'column':'ecg_id'},'entity':{'column':'patient_id'},'partition':{'column':'strat_fold','map':{**{str(i):'train' for i in range(1,9)},'9':'excluded','10':'test'}}}], 'citations':[{'file':'interpretation.txt','start_line':1,'end_line':1}]}
    session=open_inputs(json.dumps(spec),files)
    session.preview({'ptbxl.csv':{'sample':{'column':'ecg_id'},'repeats':'distinct','evidence':spec['citations']}})
    reopened=restore(save(session,session.review['review_hash']))
    assert reopened.confirmation is None
    extraction=reopened.review['extraction'];measured=measure('entity_overlap',extraction['files'],extraction['arguments'])['output']
    if any(measured[k]!=v for k,v in reference.items()):raise ValueError('Product preparation disagrees with independent reference')
    return {'dataset':'PTB-XL v1.0.3','source_url':SOURCE_URL,'status':'matches','execution':'offline developer check; no inference, Sandbox or scientific confirmation','specification_origin':'recorded developer specification; exposed development dataset','measurement':reference,'projection':projected['projection'],'draft_reopen_matches':True,'lineage_records':len(extraction['lineage']),'excluded_rows':sum(r['strat_fold']=='9' for r in rows),'scope':'Product projection, extraction, persistence and local measurement only; not live acceptance.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    result=run(args.source)
    with args.output.open('x') as out:json.dump(result,out,indent=2)
    print(json.dumps(result['measurement']))


if __name__=='__main__':main()
