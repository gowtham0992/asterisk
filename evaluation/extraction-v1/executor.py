"""Experimental closed extraction language. Not registered in the production app.

Only input strings and a validated JSON spec enter. No eval, imports, filesystem,
network, generated regex or code. Original record references accompany every row.
"""
import csv,hashlib,io,json,posixpath
MAX_BYTES=16_000_000
MAX_ROWS=100_000
class ExtractionError(ValueError):pass

def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)
def sha(x):return hashlib.sha256(x.encode()).hexdigest()
def exact(obj,required,optional=()):
 if not isinstance(obj,dict) or not set(required)<=obj.keys() or set(obj)-set(required)-set(optional):raise ExtractionError('Unknown or missing spec fields')
def text(v):
 if not isinstance(v,str) or not v or len(v)>4096 or '\x00' in v:raise ExtractionError('Identifier must be a nonempty bounded string; numeric coercion is forbidden')
 return v

def unique(pairs):
 d={}
 for k,v in pairs:
  if k in d:raise ExtractionError('Duplicate JSON key')
  d[k]=v
 return d

def records(content,fmt,name):
 rows=[]
 if fmt=='csv':
  stream=io.StringIO(content,newline='');r=csv.reader(stream,strict=True)
  try:header=next(r)
  except StopIteration:raise ExtractionError('Missing CSV header')
  if not header or len(header)>80 or len(set(header))!=len(header) or any(not h for h in header):raise ExtractionError('Invalid CSV header')
  previous=r.line_num
  for cells in r:
   first=previous+1;previous=r.line_num
   if len(cells)!=len(header):raise ExtractionError('Ragged or blank CSV record')
   rows.append((dict(zip(header,cells)),{'file':name,'line_start':first,'line_end':previous}))
 elif fmt=='json':
  try:data=json.loads(content,object_pairs_hook=unique)
  except (ValueError,RecursionError) as e:raise ExtractionError('Invalid JSON') from e
  if not isinstance(data,list):raise ExtractionError('JSON source must be an array of objects')
  for i,row in enumerate(data):
   if not isinstance(row,dict) or len(row)>80:raise ExtractionError('Invalid JSON record')
   rows.append((row,{'file':name,'pointer':f'/{i}'}))
 elif fmt=='lines':
  for i,line in enumerate(content.splitlines(),1):
   if not line:raise ExtractionError('Blank line is an unaccounted record')
   rows.append(({'value':line},{'file':name,'line_start':i,'line_end':i}))
 else:raise ExtractionError('Unsupported format')
 if not rows or len(rows)>MAX_ROWS:raise ExtractionError('Source record count outside bounds')
 if sum(len(r) for r,_ in rows)>2_000_000:raise ExtractionError('Cell bound exceeded')
 return rows

def extract(spec,files):
 exact(spec,['status','sources','citations'])
 if spec['status']!='extract':raise ExtractionError('An extraction spec is required')
 if not isinstance(files,dict) or not 1<=len(files)<=80 or any(not isinstance(n,str) or not isinstance(v,str) for n,v in files.items()) or sum(len(v.encode()) for v in files.values())>MAX_BYTES:raise ExtractionError('Input file bounds exceeded')
 if not isinstance(spec['sources'],list) or not 1<=len(spec['sources'])<=20:raise ExtractionError('Invalid source list')
 if not isinstance(spec['citations'],list) or not 1<=len(spec['citations'])<=20:raise ExtractionError('Cite supplied identity documentation')
 citations=[]
 for c in spec['citations']:
  exact(c,['file','start_line','end_line']);a,b=c['start_line'],c['end_line']
  if c['file'] not in files or type(a)!=int or type(b)!=int or not 1<=a<=b or b-a>=40:raise ExtractionError('Invalid citation')
  lines=files[c['file']].splitlines()
  if b>len(lines):raise ExtractionError('Citation beyond file')
  quote='\n'.join(lines[a-1:b])
  if len(quote)>8000:raise ExtractionError('Citation too large')
  citations.append({**c,'quote':quote})
 cache={};lookups={};used=set();accounts=[];output={};seen_sources=set()
 def read(name,fmt):
  if name not in files:raise ExtractionError('Source file missing')
  key=(name,fmt)
  if key not in cache:cache[key]=records(files[name],fmt,name)
  used.add(name);return cache[key]
 def expression(expr,row,ref,index,depth=0):
  if depth>1:raise ExtractionError('Nested lookup unsupported')
  if not isinstance(expr,dict):raise ExtractionError('Expression must be an object')
  if 'row' in expr:
   exact(expr,['row'])
   if expr['row'] is not True:raise ExtractionError('Row key must be true')
   return f'{ref["file"]}@{index}',[ref]
  if 'lookup' in expr:
   exact(expr,['lookup']);q=expr['lookup'];exact(q,['file','format','key_column','value_column','on'])
   key=(q['file'],q['format'],q['key_column'],q['value_column'])
   if key not in lookups:
    table={}
    for m,mref in read(q['file'],q['format']):
     if q['key_column'] not in m or q['value_column'] not in m:raise ExtractionError('Lookup column missing')
     k=text(m[q['key_column']]);v=text(m[q['value_column']])
     if k in table and table[k][0]!=v:raise ExtractionError('Conflicting duplicate lookup identity')
     if k not in table:table[k]=(v,[])
     table[k][1].append(mref)
    lookups[key]=table
   value,refs=expression(q['on'],row,ref,index,depth+1)
   if value not in lookups[key]:raise ExtractionError('Unmapped sample; coverage incomplete')
   value,mrefs=lookups[key][value];return value,refs+mrefs
  exact(expr,['column'],['basename','prefix'])
  if not isinstance(expr['column'],str) or expr['column'] not in row:raise ExtractionError('Column missing')
  value=text(row[expr['column']])
  if 'basename' in expr:
   if expr['basename'] is not True:raise ExtractionError('basename must be true')
   value=text(posixpath.basename(value))
  if 'prefix' in expr:
   n=expr['prefix']
   if type(n)!=int or not 1<=n<=128 or len(value)<n:raise ExtractionError('Invalid or short prefix')
   value=value[:n]
  return value,[ref]
 for s in spec['sources']:
  exact(s,['file','format','sample','entity','partition'],['deduplicate'])
  if s['file'] in seen_sources:raise ExtractionError('Source declared twice')
  seen_sources.add(s['file'])
  if type(s.get('deduplicate',False)) is not bool:raise ExtractionError('Invalid deduplication policy')
  p=s['partition'];exact(p,[],['value','column','map'])
  if set(p)=={'value'}:
   if p['value'] not in ('train','test'):raise ExtractionError('Invalid partition value')
  elif set(p)=={'column','map'}:
   if not isinstance(p['map'],dict) or not p['map'] or any(not isinstance(k,str) or v not in ('train','test','excluded') for k,v in p['map'].items()):raise ExtractionError('Invalid partition mapping')
  else:raise ExtractionError('Invalid partition definition')
  data=read(s['file'],s['format']);unique_count=0;excluded=0
  for i,(row,ref) in enumerate(data,1):
   sample,srefs=expression(s['sample'],row,ref,i);entity,erefs=expression(s['entity'],row,ref,i)
   if 'value' in p:partition=p['value']
   else:
    if p['column'] not in row or row[p['column']] not in p['map']:raise ExtractionError('Unlisted partition value; explicit exclusion required')
    partition=p['map'][row[p['column']]]
   excluded+=partition=='excluded'
   refs=[{'role':'sample',**r} for r in srefs]+[{'role':'entity',**r} for r in erefs]+[{'role':'partition',**ref}]
   if sample in output:
    old=output[sample]
    if not s.get('deduplicate',False) or old['entity']!=entity or old['partition']!=partition:raise ExtractionError('Duplicate sample or conflicting cross-partition sample')
    old['occurrences'].append(ref);old['references'].extend(refs)
   else:
    output[sample]={'sample':sample,'entity':entity,'partition':partition,'occurrences':[ref],'references':refs};unique_count+=1
  accounts.append({'file':s['file'],'source_records':len(data),'new_samples':unique_count,'repeated_occurrences':len(data)-unique_count,'excluded_occurrences':excluded})
 if len(output)>MAX_ROWS:raise ExtractionError('Derived sample limit exceeded')
 groups={r['partition'] for r in output.values()}
 if not {'train','test'}<=groups:raise ExtractionError('Both partitions must be nonempty')
 def csvtext(fields,rows):
  stream=io.StringIO();w=csv.writer(stream);w.writerow(fields);w.writerows(rows);return stream.getvalue()
 tables={'splits.csv':csvtext(['sample','partition'],[(r['sample'],r['partition']) for r in output.values()]),'entities.csv':csvtext(['sample','entity'],[(r['sample'],r['entity']) for r in output.values()])}
 args={'split_file':'splits.csv','mapping_file':'entities.csv','sample_column':'sample','mapping_sample_column':'sample','entity_column':'entity','partition_column':'partition','train_values':['train'],'test_values':['test']}
 return {'schema_version':1,'spec':spec,'spec_hash':sha(canonical(spec)),'input_hashes':{n:sha(v) for n,v in files.items()},'used_sources':sorted(used),'source_accounting':accounts,'lookup_accounting':[{'file':k[0],'records':len(cache[(k[0],k[1])]),'unique_keys':len(v)} for k,v in lookups.items()],'lineage':list(output.values()),'citations':citations,'files':tables,'arguments':args,'confirmation':None}
