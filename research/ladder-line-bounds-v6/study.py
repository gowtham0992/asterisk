"""One frozen comparison of citation-bound metadata; never retry to improve a score."""
import json,hashlib,time,os,sys,importlib.util
from pathlib import Path
from app import ladder_proposal as lp,ladder
from app.ladder_api import token_factory,DEFAULT_MODEL
from variant import install
install(lp)
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'.data/line-bounds-v6-20261007'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def reference(claim,expr):
 return {'schema':'asterisk-ladder/1','claim':{'text':claim,'level':'subject'},'sources':[{'file':'split.csv','format':'csv','sample':{'column':'sample'},'partition':{'column':'split','map':{'train':'train','test':'test'}}}], 'levels':[{'name':'sample','kind':'observation','expression':{'column':'sample'}},{'name':'subject','kind':'unit','expression':expr}],'citations':[{'file':'README.md','start_line':1,'end_line':3}]}
def freeze():
 if (OUT/'packet.json').exists():raise RuntimeError('Already frozen')
 names=json.loads((OUT/'orl-index.json').read_text())['filenames'];cases=[]
 doc='AT&T Laboratories Cambridge: https://www.cl.cam.ac.uk/research/dtg/attarchive/facedatabase.html\nThe images are organised in 40 directories (one for each subject), which have names of the form sX, where X indicates the subject number (between 1 and 40).\nIn each of these directories, there are ten different images of that subject, which have names of the form Y.pgm, where Y is the image number for that subject (between 1 and 10).\nLocal projection: sample is the complete original relative image path. split records the researcher-authored train/test assignment. No images are supplied.\n'
 claim='No evaluation subject appears in training.'
 for mode in ['grouped','image-split','missing-definition']:
  rows=[(n,'train' if (int(n.split('/')[0][1:])<=20 if mode=='grouped' else int(n.split('/')[1].split('.')[0])<=8) else 'test') for n in names]
  text=doc if mode!='missing-definition' else 'Each sample is an image path; split records researcher-authored train/test assignment.\nSubject mapping and directory meaning are not supplied.\nNo subject identity can be inferred from path spelling alone.\n'
  files={'split.csv':'sample,split\n'+''.join(f'{n},{s}\n' for n,s in rows),'README.md':text}
  ref=reference(claim,{'column':'sample','field':{'separator':'/','from':1}}) if mode!='missing-definition' else None
  cases.append({'id':'orl-'+mode,'origin':'Real archive filename projection, authored splits; not an official split audit','claim':claim,'files':files,'reference':ref})
 counts=json.loads((OUT/'pendigits-index.json').read_text())['counts']
 # Row identifiers are authored; actual feature/label values are deliberately absent.
 for mode in ['writer-missing','per-row-trap']:
  claim='Evaluation handwriting comes from writers absent from training.'
  files={'split.csv':'sample,split\n'+''.join(f'{n}:{i},{"train" if n.endswith("tra") else "test"}\n' for n,count in counts.items() for i in range(1,count+1)),
         'README.md':'UCI Pendigits: https://archive.ics.uci.edu/dataset/81/pen+based+recognition+of+handwritten+digits\nThe samples written by 30 writers are used for training, cross-validation and writer dependent testing, and the digits written by the other 14 are used for writer independent testing.\nAll input attributes are integers in the range 0..100. The last attribute is the class code 0..9.\nLocal projection: sample is original filename and row number, identifying a handwriting sample, not a writer. split labels train/test by the published .tra/.tes filename. No writer lookup, coordinates or class values are supplied.\n'}
  if mode=='per-row-trap':files['README.md']+='Every row ID is unique. Uniqueness proves only different samples, never different writers.\n'
  cases.append({'id':'pendigits-'+mode,'origin':'Real published row counts; authored row identifiers; no writer mapping','claim':claim,'files':files,'reference':None})
 for mode in ['short-join','long-join','denied-join']:
  claim='No evaluation subject appears in training.'
  files={'split.csv':'sample,split\na,train\nb,test\nc,train\nd,test\n','units.csv':'sample,subject\na,u1\nb,u1\nc,u2\nd,u3\n'}
  lines=['Original fictional spectroscopy fixture. sample identifies one spectrum in split.csv.', 'units.csv joins on sample and returns subject, the physical specimen that generated the spectrum.', 'split.csv split train means training; test means evaluation.']
  if mode=='long-join':lines=['Historical note without identity definitions.']*65+lines
  if mode=='denied-join':lines[1]='units.csv subject is an instrument setting, NOT a physical specimen identity. Specimen mapping is absent.'
  files['README.md']='\n'.join(lines)+'\n';ref=None if mode=='denied-join' else reference(claim,{'lookup':{'file':'units.csv','format':'csv','key_column':'sample','value_column':'subject','on':{'column':'sample'}}})
  if ref:ref['citations']=[{'file':'README.md','start_line':len(lines)-2,'end_line':len(lines)}]
  cases.append({'id':'original-'+mode,'origin':'Builder-authored fictional control, not independent evidence','claim':claim,'files':files,'reference':ref})
 for c in cases:
  c['documentation']=['README.md'];c['share']=[['split.csv','sample'],['split.csv','split']]
  if 'units.csv' in c['files']:c['share'] += [['units.csv','sample'],['units.csv','subject']]
  if c['reference']:c['expected']=ladder.measure(c['reference'],c['files'])
 items=[{'id':c['id'],'version':v,'trial':t,'messages':lp.request(c['claim'],c['files'],c['share'],c['documentation'],v)} for t in [1,2] for c in cases for v in ['v4','v6']]
 packet={'cases':cases,'requests':items,'model':DEFAULT_MODEL,'maximum_calls':64,'cap_usd':2,
 'decision':'Promote only if v6 has zero unsupported or false reassuring proposals; all supported cases correct in both trials; at least two more correct attempts than v4; fewer invalid first replies and fewer citation-bounds errors. Otherwise keep v4. No repeat-until-pass.',
 'limitations':'8 correlated cases, 2 datasets plus fictional controls. Authored by implementer after prompt freeze; not independent acceptance. Tests citation bounds, not universal preparation reliability. No human evidence. No Sandbox.'}
 p=OUT/'packet.json';p.write_text(json.dumps(packet,indent=2)+'\n')
 (OUT/'freeze.json').write_text(json.dumps({'packet_sha256':sha(p),'implementation_sha256':sha(ROOT/'app/ladder_proposal.py'),'prompts':{v:hashlib.sha256(lp.PROMPTS[v].encode()).hexdigest() for v in ['v4','v6']},'time':time.time()},indent=2))
 print('Frozen 32 proposals, <=64 calls, $2 conservative estimated cap')
def run():
 p=OUT/'packet.json';f=json.loads((OUT/'freeze.json').read_text());assert sha(p)==f['packet_sha256'];assert sha(OUT/'candidate-source.py')==f['implementation_sha256']
 for v in ['v4','v6']:assert hashlib.sha256(lp.PROMPTS[v].encode()).hexdigest()==f['prompts'][v]
 packet=json.loads(p.read_text());sp=importlib.util.spec_from_file_location('budget',ROOT/'evaluation/probe-pilot/budget.py');mod=importlib.util.module_from_spec(sp);sp.loader.exec_module(mod)
 budget=mod.Budget(OUT/'budget.json',{DEFAULT_MODEL:(0.5,1.5)},limit=2)
 import app.main
 key=os.environ['NEBIUS_API_KEY'];rows=[]
 for item in packet['requests']:
  path=OUT/f"{item['version']}-{item['id']}-{item['trial']}.json"
  if path.exists():rows.append(json.loads(path.read_text()));continue
  c=next(c for c in packet['cases'] if c['id']==item['id']);complete,usage=token_factory(DEFAULT_MODEL,key)
  def paid(messages,maximum,timeout):
   rid=budget.reserve(DEFAULT_MODEL,len(json.dumps(messages).encode())+3000,maximum)
   if rid is None:raise RuntimeError('Budget exhausted; no call')
   before=usage['total_tokens']
   try:reply=complete(messages,maximum,timeout)
   except Exception:budget.uncertain(rid);raise
   budget.settle(rid,0,usage['total_tokens']-before);return reply
  row={k:item[k] for k in ['id','version','trial']};row.update(correct=False,false_reassurance=False,unsupported=False);start=time.monotonic()
  try:
   got,attempts=lp.propose(c['claim'],c['files'],paid,c['share'],documentation=c['documentation'],version=item['version']);row.update(proposal=got,attempts=attempts)
   if c['reference'] is None:row['correct']=got['status']=='abstain';row['unsupported']=got['status']!='abstain'
   elif got['status']=='ladder':
    actual=ladder.measure(got['spec'],c['files']);expected=c['expected'];pop=ladder.population(got['spec'],c['files']);want=ladder.population(c['reference'],c['files'])
    row['correct']=lp.semantic_match(got['spec'],c['reference'],c['files'])['same_grouping'] and pop==want and actual['finding']['status']==expected['finding']['status']
    row['false_reassurance']=actual['finding']['status']=='held_out_pending_confirmation' and not row['correct']
    row['finding']=actual['finding']
  except Exception as e:row['error']=type(e).__name__+': '+str(e)[:250]
  row.update(usage=usage,seconds=round(time.monotonic()-start,2));path.write_text(json.dumps(row,indent=2)+'\n');rows.append(row);print(row['version'],row['id'],row['trial'],'correct',row['correct'],flush=True)
 summary={}
 for v in ['v4','v6']:
  r=[r for r in rows if r['version']==v];summary[v]={'correct':sum(x['correct'] for x in r),'unsupported':sum(x['unsupported'] for x in r),'false_reassurance':sum(x['false_reassurance'] for x in r),'invalid_first':sum(bool(x.get('attempts') and x['attempts'][0]['error']) or 'error' in x for x in r),'citation_errors':sum('Citation beyond file' in (a['error'] or '') for x in r for a in x.get('attempts',[])),'calls':sum(x['usage']['calls'] for x in r),'tokens':sum(x['usage']['total_tokens'] for x in r)}
 a,b=summary['v4'],summary['v6'];supported={c['id'] for c in packet['cases'] if c['reference']}
 summary['promote']=b['unsupported']==b['false_reassurance']==0 and all(x['correct'] for x in rows if x['version']=='v6' and x['id'] in supported) and b['correct']>=a['correct']+2 and b['invalid_first']<a['invalid_first'] and b['citation_errors']<a['citation_errors']
 (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary),flush=True)
if __name__=='__main__':freeze() if sys.argv[1]=='freeze' else run()
