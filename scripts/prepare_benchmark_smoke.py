"""Prepare three exact real-benchmark proposal payloads OFFLINE. Never dispatch.

Projected identifiers are private local artifacts, not public release assets.
One proposed completion per exposed development dataset, no retries or correction
calls. Sandbox payloads depend on actual proposals and are not authorized here.
"""
import hashlib,json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.check_dermamnist_preparation import SOURCES,project_source_files
from scripts.check_ptbxl_preparation import SOURCE_SHA
from scripts.check_wsi_preparation import HASHES
from app.preparation.proposal import ProposalRequest


def build(raw_root,output):
    output.mkdir(parents=True,exist_ok=False)
    configs=[('dermamnist',{f'derma/{name}':digest for name,digest in SOURCES.items()},
      {'dermamnist_split_info.csv':['image_id','split'],'HAM10000_metadata.csv':['image_id','lesion_id']},
      'Check whether lesions in the test partition also occur in train; exclude val.'),
     ('ptbxl',{'ptbxl.csv':SOURCE_SHA},{'ptbxl.csv':['ecg_id','patient_id','strat_fold']},
      'Check whether patients in fold 10 also occur in folds 1 through 8; exclude fold 9.'),
     ('wsi',{f'wsi/Report_all_type_all_{side}_single.json':digest for side,digest in HASHES.items()},
      {f'Report_all_type_all_{side}_single.json':['image'] for side in HASHES},
      'Check whether patients represented by slides in the test source also occur in the training source.')]
    inventory=[]
    for name,pins,selection,claim in configs:
        raw={}
        for filename,digest in pins.items():
            data=(raw_root/filename).read_bytes()
            if hashlib.sha256(data).hexdigest()!=digest:raise ValueError('Pinned source changed')
            raw[Path(filename).name]=data.decode('utf-8')
        projected=project_source_files(raw,selection);files=projected['files']
        files['documentation.txt']=(ROOT/f'research/real-benchmark-workflow/documentation/{name}.txt').read_text()
        request=ProposalRequest(files,claim,['documentation.txt'],projected['projection'])
        preview=request.preview()
        packet={'case':name,'claim':claim,'files':files,'projection':projected['projection'],'preview':preview}
        encoded=json.dumps(packet,ensure_ascii=False,separators=(',',':')).encode()
        (output/(name+'.json')).write_bytes(encoded)
        inventory.append({'case':name,'packet_sha256':hashlib.sha256(encoded).hexdigest(),'payload_hash':preview['payload_hash'],
          'input_files':[{'file':n,'bytes':len(v.encode()),'sha256':hashlib.sha256(v.encode()).hexdigest()} for n,v in files.items()],
          'projection':projected['projection'],'estimated_reservation_usd':preview['estimated_reservation_usd'],
          'model':'nvidia/nemotron-3-super-120b-a12b','provider':'Nebius Token Factory',
          'transmitted':'Exact preview.messages only; full projected sources retained locally. Sandbox upload is outside this packet.'})
    result={'status':'prepared_not_run','trials':3,'retries':0,'scope':'Exposed development smoke test, not acceptance or independent evaluation. Selected primary-source documentation excerpts.','estimated_total_reservation_usd':sum(x['estimated_reservation_usd'] for x in inventory),'cases':inventory}
    (output/'inventory.json').write_text(json.dumps(result,indent=2))
    return result


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--raw-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=build(a.raw_root,a.output)
    print(json.dumps({'status':result['status'],'trials':result['trials'],'reservation_usd':result['estimated_total_reservation_usd']}))
