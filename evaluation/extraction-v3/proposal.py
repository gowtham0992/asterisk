"""Precise proposal diagnostics around the unchanged, frozen extraction executor."""
import importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('proposal_v2',Path(__file__).resolve().parents[1]/'extraction-v2/proposal.py')
v2=importlib.util.module_from_spec(s);s.loader.exec_module(v2)
executor=v2.executor
PROMPT=v2.PROMPT+'''
Expression examples (all keys shown): a full observation path is {"column":"path"}; a person encoded by its filename prefix is {"column":"path","basename":true,"prefix":4}. Transforms always need their source column. A sample expression and an entity expression usually differ.
An insufficient response has ONLY status and missing; citations belong ONLY to extract responses. Unsupported layout is different from absent identity: describe the actual limitation. Do not assert linkage is absent when documentation supplies a supported transform. Application code terminates a proposed mapping on missing or conflicting lookup records; it will not ask you to invent evidence.
'''
def request(files,claim):
 messages=v2.request(files,claim);messages[0]['content']=PROMPT;return messages
def shape(obj,required,optional,path):
 if not isinstance(obj,dict):raise ValueError(f'{path}: expected an object')
 missing=set(required)-obj.keys();extra=obj.keys()-set(required)-set(optional)
 if missing or extra:raise ValueError(f'{path}: missing fields {sorted(missing)}; unknown fields {sorted(extra)}')
def expression(e,path,depth=0):
 if not isinstance(e,dict):raise ValueError(f'{path}: expected expression object')
 if 'lookup' in e:
  shape(e,['lookup'],[],path)
  if depth:raise ValueError(f'{path}: nested lookup unsupported')
  shape(e['lookup'],['file','format','key_column','value_column','on'],[],path+'.lookup')
  expression(e['lookup']['on'],path+'.lookup.on',depth+1)
 elif 'row' in e:shape(e,['row'],[],path)
 else:shape(e,['column'],['basename','prefix'],path)
def parse(content):
 # Preserve duplicate-key rejection and exact refusal shape from v2.
 value=v2.parse(content)
 if value.get('status')=='insufficient':return value
 shape(value,['status','sources','citations'],[],'proposal')
 if not isinstance(value['sources'],list):raise ValueError('sources: expected list')
 for i,source in enumerate(value['sources']):
  path=f'sources[{i}]';shape(source,['file','format','sample','entity','partition'],['deduplicate'],path)
  expression(source['sample'],path+'.sample');expression(source['entity'],path+'.entity')
 return value
BLOCKERS={
 'Unmapped sample; coverage incomplete':('incomplete_mapping','The proposed lookup does not cover every observation. Supply the missing identity links or review the proposed binding.'),
 'Conflicting duplicate lookup identity':('conflicting_mapping','The proposed lookup assigns multiple identities to one key. Resolve the conflict or review the proposed binding.'),
 'JSON source must be an array of objects':('unsupported_layout','The proposed JSON source is not a top-level array of objects. This extraction language does not support that layout.'),
}
def execute(spec,files):
 try:return {'status':'extracted','extraction':executor.extract(spec,files)}
 except executor.ExtractionError as exc:
  if str(exc) not in BLOCKERS:raise
  code,message=BLOCKERS[str(exc)]
  return {'status':'blocked','code':code,'message':message,'scope':'This proposed extraction only; no scientific verdict.', 'spec_hash':executor.sha(executor.canonical(spec)),'input_hashes':{n:executor.sha(v) for n,v in files.items()},'confirmation':None}
