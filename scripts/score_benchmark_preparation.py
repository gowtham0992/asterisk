"""Offline diagnostic scoring on pinned, exposed development packets. No network."""
import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.preparation.proposal import proposal,executor


def csv_rows(content,name):
    reader=csv.DictReader(io.StringIO(content,newline=''))
    previous=reader.line_num
    # DictReader initializes the header lazily.
    reader.fieldnames
    previous=reader.line_num
    for row in reader:
        yield row,{'file':name,'line_start':previous+1,'line_end':reader.line_num}
        previous=reader.line_num


def reference_rows(case,files):
    """Independent direct reads, matching the previously recorded developer rules."""
    output=[]
    def add(ref,sample,entity,partition):
        output.append({'sample':sample,'entity':entity,'partition':partition,'occurrences':[ref]})
    if case=='dermamnist':
        mapping={}
        for row,_ in csv_rows(files['HAM10000_metadata.csv'],'HAM10000_metadata.csv'):
            key,value=row['image_id'],row['lesion_id']
            if key in mapping and mapping[key]!=value:raise ValueError('Conflicting reference mapping')
            mapping[key]=value
        for row,ref in csv_rows(files['dermamnist_split_info.csv'],'dermamnist_split_info.csv'):
            add(ref,row['image_id'],mapping[row['image_id']],{'train':'train','test':'test','val':'excluded'}[row['split']])
    elif case=='ptbxl':
        for row,ref in csv_rows(files['ptbxl.csv'],'ptbxl.csv'):
            partition={**{str(i):'train' for i in range(1,9)},'9':'excluded','10':'test'}[row['strat_fold']]
            add(ref,row['ecg_id'],row['patient_id'],partition)
    elif case=='wsi':
        for side in ('train','test'):
            name=f'Report_all_type_all_{side}_single.json'
            for i,row in enumerate(json.loads(files[name])):
                slide=row['image'].rsplit('/',1)[-1]
                if not slide.startswith('TCGA-') or len(slide)<12:raise ValueError('Unexpected reference barcode')
                add({'file':name,'pointer':f'/{i}'},slide,slide[:12],side)
    else:raise ValueError('Unknown case')
    return output


def compare_rows(expected,actual):
    def index(rows):
        out={}
        for row in rows:
            for ref in row['occurrences']:
                key=json.dumps(ref,sort_keys=True,separators=(',',':'))
                if key in out:raise ValueError('Duplicate source occurrence')
                out[key]=row
        return out
    wanted,got=index(expected),index(actual)
    common=wanted.keys()&got.keys()
    changes={field:sum(wanted[k][field]!=got[k][field] for k in common)
             for field in ('sample','entity','partition')}
    return {'expected_source_occurrences':len(wanted),'observed_source_occurrences':len(got),
            'missing_occurrences':len(wanted.keys()-got.keys()),
            'extra_occurrences':len(got.keys()-wanted.keys()),'different_fields':changes,
            'exact_reference_rows_match':wanted.keys()==got.keys() and not any(changes.values()),
            'scope':'Literal developer-reference comparison. Equivalent observation-ID encodings may differ; human semantic review remains separate.'}


def score(case,packet,completion):
    base={'case':case,'scientific_confirmation':None}
    try:
        spec=proposal.parse(completion['content'])
        if spec.get('status')=='insufficient':return {**base,'status':'insufficient','missing':spec['missing']}
        extraction=executor.extract(spec,packet['files'])
    except (ValueError,TypeError,KeyError,IndexError,RecursionError) as exc:
        return {**base,'status':'invalid_proposal','error_type':type(exc).__name__}
    rows=extraction['lineage'];train={r['entity'] for r in rows if r['partition']=='train'}
    test=[r for r in rows if r['partition']=='test'];shared=train&{r['entity'] for r in test}
    return {**base,'status':'extracted','population':dict(Counter(r['partition'] for r in rows)),
            'measurement':{'shared_entities':len(shared),'affected_test_rows':sum(r['entity'] in shared for r in test)},
            'reference':compare_rows(reference_rows(case,packet['files']),rows)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet-dir',type=Path,required=True)
    parser.add_argument('--results-dir',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();cases=[]
    for case in ('dermamnist','ptbxl','wsi'):
        raw=(args.packet_dir/(case+'.json')).read_bytes()
        response=args.results_dir/case/'completion.json'
        if not response.exists():cases.append({'case':case,'status':'no_retained_completion'});continue
        encoded=response.read_bytes();result=score(case,json.loads(raw),json.loads(encoded))
        result.update(packet_sha256=hashlib.sha256(raw).hexdigest(),completion_sha256=hashlib.sha256(encoded).hexdigest())
        cases.append(result)
    with args.output.open('x') as stream:json.dump({'scope':'Exposed development only; no independent semantic confirmation','cases':cases},stream,indent=2)
    print(json.dumps({'cases':[{k:r[k] for k in ('case','status')} for r in cases]}))


if __name__=='__main__':main()
