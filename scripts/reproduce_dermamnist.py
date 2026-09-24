"""Reproduce recorded lesion overlap from pinned upstream CSVs; no network/uploads.

Run from a separately obtained Asterisk source checkout. Raw metadata stays local.
Only aggregate results and source hashes are written. No model or dataset code runs.
"""
import argparse,csv,hashlib,io,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.primitives import measure
COMMIT='ac655ac5a5b93264c57d69d6d520778d915bfc89'
BASE=f'https://raw.githubusercontent.com/kakumarabhishek/Corrected-Skin-Image-Datasets/{COMMIT}/DermaMNIST/DermaMNIST_Analysis/'
SOURCES={
 'dermamnist_split_info.csv':'0c9b1719bf04fa9ad3cdee2a852067a8b848795624e88ea794df40fd13c099f0',
 'HAM10000_metadata.csv':'de17ec44cb25ea9c3f6378ba18d69224c740afd62e86ec2edc6a894d6aa663d3',
}
def table(fields,rows):
 out=io.StringIO(newline='');w=csv.writer(out);w.writerow(fields);w.writerows(rows);return out.getvalue()
def reproduce(directory):
 data={}
 for name,digest in SOURCES.items():
  raw=(directory/name).read_bytes()
  if hashlib.sha256(raw).hexdigest()!=digest:raise ValueError(f'{name}: source hash mismatch; use the pinned upstream file')
  data[name]=list(csv.DictReader(io.StringIO(raw.decode('utf-8'))))
 splits=data['dermamnist_split_info.csv'];mapping=data['HAM10000_metadata.csv']
 ids={}
 for r in mapping:
  key,entity=r['image_id'],r['lesion_id']
  if not key or not entity:raise ValueError('Blank identifier')
  if key in ids and ids[key]!=entity:raise ValueError('Conflicting identity mapping')
  ids[key]=entity
 seen=set();parts={'train':[],'test':[],'val':[]}
 for r in splits:
  key,part=r['image_id'],r['split']
  if key in seen or not key:raise ValueError('Duplicate or blank sample')
  seen.add(key)
  if key not in ids or part not in parts:raise ValueError('Unmapped sample or unexpected partition')
  parts[part].append(ids[key])
 shared=set(parts['train'])&set(parts['test'])
 reference={'shared_entities':len(shared),'affected_test_rows':sum(x in shared for x in parts['test']),'train_rows':len(parts['train']),'test_rows':len(parts['test'])}
 files={'splits.csv':table(['sample','partition'],[(r['image_id'],r['split']) for r in splits]),'entities.csv':table(['sample','entity'],[(r['image_id'],r['lesion_id']) for r in mapping])}
 arguments={'split_file':'splits.csv','mapping_file':'entities.csv','sample_column':'sample','mapping_sample_column':'sample','entity_column':'entity','partition_column':'partition','train_values':['train'],'test_values':['test']}
 measured=measure('entity_overlap',files,arguments)['output']
 if not measured['available'] or any(measured[k]!=v for k,v in reference.items()):raise ValueError('Checker disagrees with separate set-based reference')
 return {'schema_version':1,'dataset':'Original DermaMNIST split mapped to HAM10000 lesion IDs','source_commit':COMMIT,'sources':[{'file':n,'url':BASE+n,'sha256':h} for n,h in SOURCES.items()],'measurement':reference,'excluded_validation_rows':len(parts['val']),'reference_agrees':True,'execution':'local; no inference or provider upload','identity_scope':'Lesions, not patients. Scientific meaning supplied by upstream documentation.','published_shared_lesions':641,'matches_published_lesion_count':len(shared)==641,'checker_sha256':hashlib.sha256((ROOT/'app/primitives.py').read_bytes()).hexdigest(),'scope':'Recorded identity overlap only; no model accuracy measurement, new discovery, or human usefulness claim.'}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-dir',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 result=reproduce(a.source_dir)
 if a.output.exists():raise ValueError('Output already exists; choose a new file to preserve earlier results')
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['measurement'],indent=2))
if __name__=='__main__':main()
