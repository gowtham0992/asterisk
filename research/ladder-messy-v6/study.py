"""Fresh, frozen comparison; uses unchanged v4 and the unchanged bounds-only candidate."""
import json,hashlib,sys,time,os,importlib.util
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from app import ladder,ladder_proposal as lp
from app.ladder_api import DEFAULT_MODEL,token_factory
from app.ladder_citations import review
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'.data/ladder-messy-v6-20261007'
sp=importlib.util.spec_from_file_location('bounds_variant',ROOT/'research/ladder-line-bounds-v6/variant.py');variant=importlib.util.module_from_spec(sp);sp.loader.exec_module(variant);variant.install(lp)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def spec(claim,expr,doc,end=3):
 return {'schema':'asterisk-ladder/1','claim':{'text':claim,'level':'unit'},'sources':[{'file':'samples.csv','format':'csv','sample':{'column':'sample'},'partition':{'column':'assignment','map':{'fit':'train','check':'test'}}}], 'levels':[{'name':'observation','kind':'observation','expression':{'column':'sample'}},{'name':'unit','kind':'unit','expression':expr}],'citations':[{'file':doc,'start_line':1,'end_line':end}]}
def freeze():
 if (OUT/'packet.json').exists():raise RuntimeError('Already frozen')
 inventory=json.loads((OUT/'source-inventory.json').read_text());assert inventory['72']['counts']['mfeat-fou']==2000 and inventory['72']['counts']['mfeat-kar']==2000;assert inventory['181']['counts']['movement_libras.data']==360
 cases=[]
 claim='Evaluation original character patterns are absent from training.'
 docs={'README.md':'UCI Multiple Features, R. Duin, CC BY 4.0. https://archive.ics.uci.edu/dataset/72/multiple+features\nCorresponding patterns in different feature sets (files) correspond to the same original character.\nIn each file the 2000 patterns are stored in ASCI on 2000 lines.\n',
 'projection.txt':'This local projection retains no feature values. sample is <feature-file>:<original 1-based line number>.\nThe same original line number in different feature files denotes the corresponding original character pattern.\nassignment fit means training and check means evaluation. It is authored for this test, not a published split.\n'}
 for mode in ['cross-view','grouped']:
  rows=[(f'{view}:{i:04}', 'fit' if (view=='mfeat-fou' if mode=='cross-view' else i<=1000) else 'check') for view in ['mfeat-fou','mfeat-kar'] for i in range(1,2001)]
  files={'samples.csv':'sample,assignment\n'+''.join(f'{n},{s}\n' for n,s in rows),**docs};ref=spec(claim,{'column':'sample','field':{'separator':':','from':2}},'projection.txt');ref['citations']+=[{'file':'README.md','start_line':2,'end_line':3}]
  cases.append({'id':'mfeat-'+mode,'claim':claim,'files':files,'reference':ref,'origin':'Public row counts and alignment documentation, authored identifier projection and splits'})
 files={'samples.csv':'sample,assignment\n'+''.join(f'line{i:04},{"fit" if i<=1000 else "check"}\n' for i in range(1,2001)),**docs};files['projection.txt']='Local projection: sample identifies a digit pattern by row number. assignment fit means training; check means evaluation.\nNo writer identities or writer mapping are included.\n';cases.append({'id':'mfeat-writer-unknown','claim':'No evaluation writer appears in training.','files':files,'reference':None,'origin':'Public row counts and documentation, no writer mapping in supplied projection'})
 files={'samples.csv':'sample,assignment\n'+''.join(f'movement-{i:03},{"fit" if i%2 else "check"}\n' for i in range(1,361)),
 'README.md':'UCI Libras Movement, Dias, Peres and Bscaro, CC BY 4.0. https://archive.ics.uci.edu/dataset/181/libras+movement\nThe dataset contains 15 classes of 24 instances each; each class references a hand movement type in LIBRAS.\n90 numeric features represent movement coordinates, with one integer class.\n',
 'projection.txt':'sample identifies one original movement_libras.data row. assignment fit means training; check means evaluation.\nNo movement coordinates, labels, signer identities or signer mapping are supplied.\nA movement type is not a signer identity.\n'}
 cases.append({'id':'libras-signer-unknown','claim':'No evaluation signer appears in training.','files':files,'reference':None,'origin':'Public row count, authored sample IDs and split; no signer mapping'})
 for mode in ['scattered','late','distractor','denied']:
  claim='No evaluation material specimen appears in training.'
  files={'samples.csv':'sample,assignment\nx7,fit\ny2,check\nz9,fit\nw4,check\n','registry.csv':'capture,origin,station\nx7,lot-Q,line-1\ny2,lot-Q,line-2\nz9,lot-R,line-1\nw4,lot-S,line-2\n',
 'README.md':'Original fictional microscopy workflow. sample identifies one capture in samples.csv.\nCurrent file semantics are in registry-notes.txt, not in old notebook column-name guesses.\n',
 'split-notes.txt':'assignment fit is training; check is evaluation.\n'}
  lines=['registry.csv capture matches samples.csv sample exactly.', 'registry.csv origin is the material specimen that generated the capture; captures may repeat the same specimen.', 'registry.csv station names acquisition equipment, not the specimen.']
  if mode=='late':lines=['# Instrument maintenance log']+[f'Entry {i}: calibration log only; no specimen identity definition.' if i%3 else '' for i in range(1,73)]+lines
  if mode=='distractor':lines=['# Column name warning','origin is not the image origin coordinate. The following current definition replaces that old notebook interpretation.']+lines
  if mode=='denied':lines=['registry.csv capture matches samples.csv sample exactly.', 'registry.csv origin is the acquisition station, NOT the material specimen.', 'The material-specimen mapping is absent. No column or substring supplies it.']
  files['registry-notes.txt']='\n'.join(lines)+'\n';ref=None
  if mode!='denied':
   ref=spec(claim,{'lookup':{'file':'registry.csv','format':'csv','key_column':'capture','value_column':'origin','on':{'column':'sample'}}},'README.md',2)
   ref['citations'] += [{'file':'registry-notes.txt','start_line':len(lines)-2,'end_line':len(lines)},{'file':'split-notes.txt','start_line':1,'end_line':1}]
  cases.append({'id':'original-'+mode,'claim':claim,'files':files,'reference':ref,'origin':'Builder-authored fictional case, definitions scattered/late/contrasted; not independent'})
 for c in cases:
  c['documentation']=[n for n in c['files'] if n.endswith(('.md','.txt'))]
  c['share']=[['samples.csv','sample'],['samples.csv','assignment']]
  if 'registry.csv' in c['files']:c['share'] += [['registry.csv','capture'],['registry.csv','origin'],['registry.csv','station']]
  if c['reference']:
   c['expected']=ladder.measure(c['reference'],c['files']);assert c['expected']['finding']['status'] in ['violation','held_out_pending_confirmation']
 assert len(cases)==8 and len({c['id'] for c in cases})==8
 requests=[{'id':c['id'],'version':v,'trial':t,'messages':lp.request(c['claim'],c['files'],c['share'],c['documentation'],v)} for t in [1,2] for c in cases for v in ['v4','v6']]
 packet={'cases':cases,'requests':requests,'model':DEFAULT_MODEL,'maximum_calls':64,'cap_usd':2,'rule':'Promote only if v6 correct>=14/16 and at least 2 above v4, all abstention controls correct, zero wrong pending clear, no paired regression against a correct v4 response, and total rejected-call corrections plus structural review flags <= v4. Otherwise no promotion. No post-hoc retries.','limits':'Builder-authored, correlated cases; no human sessions; review flags are structural cues, not actual human corrections or proof of meaning.'}
 (OUT/'packet.json').write_text(json.dumps(packet,indent=2)+'\n');(OUT/'freeze.json').write_text(json.dumps({'time':time.time(),'packet_sha256':sha(OUT/'packet.json'),'runner_sha256':sha(Path(__file__)),'prompts':{v:hashlib.sha256(lp.PROMPTS[v].encode()).hexdigest() for v in ['v4','v6']}},indent=2)+'\n');print('Frozen 8 cases, 32 proposals; <=64 calls, $2 estimated cap')
def partition(spec,files):return {r['sample']:r['partition'] for r in ladder.population(spec,files)['lineage']}
def correctness(g,c):
 if c['reference'] is None:return g.get('status')=='abstain'
 if g.get('status')!='ladder':return False
 ref=c['reference'];return lp.semantic_match(g['spec'],ref,c['files'])['same_grouping'] and partition(g['spec'],c['files'])==partition(ref,c['files']) and ladder.measure(g['spec'],c['files'])['finding']['status']==c['expected']['finding']['status']
def summarize(rows,packet):
 summary={}
 for v in ['v4','v6']:
  rs=[r for r in rows if r['version']==v];summary[v]={'correct':sum(r['correct'] for r in rs),'unsupported':sum(r['unsupported'] for r in rs),'wrong_pending_clear':sum(r['wrong_pending_clear'] for r in rs),'rejected_calls':sum(r['rejected_calls'] for r in rs),'review_flags':sum(r['review_flags'] for r in rs),'calls':sum(r['usage']['calls'] for r in rs),'tokens':sum(r['usage']['total_tokens'] for r in rs)}
 a,b=summary['v4'],summary['v6'];pairs={(r['id'],r['trial'],r['version']):r for r in rows};regressions=[(r['id'],r['trial']) for r in rows if r['version']=='v6' and not r['correct'] and pairs[(r['id'],r['trial'],'v4')]['correct']];summary['paired_regressions']=regressions
 summary['promote']=b['correct']>=14 and b['correct']>=a['correct']+2 and b['unsupported']==b['wrong_pending_clear']==0 and not regressions and b['rejected_calls']+b['review_flags']<=a['rejected_calls']+a['review_flags'];return summary
def run():
 freeze=json.loads((OUT/'freeze.json').read_text());assert sha(OUT/'packet.json')==freeze['packet_sha256'];assert sha(Path(__file__))==freeze['runner_sha256']
 for v in ['v4','v6']:assert hashlib.sha256(lp.PROMPTS[v].encode()).hexdigest()==freeze['prompts'][v]
 packet=json.loads((OUT/'packet.json').read_text());assert len(packet['cases'])==8 and len(packet['requests'])==32
 s=importlib.util.spec_from_file_location('budget',ROOT/'evaluation/probe-pilot/budget.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);budget=b.Budget(OUT/'budget.json',{DEFAULT_MODEL:(0.5,1.5)},limit=2)
 import app.main
 key=os.environ['NEBIUS_API_KEY']
 def attempt(item):
  path=OUT/f"{item['version']}-{item['id']}-{item['trial']}.json"
  if path.exists():return json.loads(path.read_text())
  c=next(c for c in packet['cases'] if c['id']==item['id']);complete,usage=token_factory(DEFAULT_MODEL,key);trace=[];start=time.monotonic();row={k:item[k] for k in ['id','version','trial']};row.update(correct=False,unsupported=False,wrong_pending_clear=False,review_flags=0)
  def paid(messages,maximum,timeout):
   reservation=budget.reserve(DEFAULT_MODEL,len(json.dumps(messages).encode())+3000,maximum)
   if reservation is None:raise RuntimeError('Budget exhausted; no call')
   before=usage['total_tokens'];call={'messages':messages};trace.append(call)
   try:reply=complete(messages,maximum,timeout)
   except BaseException as e:call['error']=type(e).__name__;budget.uncertain(reservation);raise
   budget.settle(reservation,0,usage['total_tokens']-before);call['reply']=reply;return reply
  try:
   got,attempts=lp.propose(c['claim'],c['files'],paid,c['share'],documentation=c['documentation'],version=item['version']);row.update(proposal=got,attempts=attempts);row['correct']=correctness(got,c);row['unsupported']=c['reference'] is None and got['status']!='abstain'
   if got['status']=='ladder':
    result=ladder.measure(got['spec'],c['files']);row['finding']=result['finding'];row['wrong_pending_clear']=not row['correct'] and result['finding']['status']=='held_out_pending_confirmation';row['review_flags']=sum(bool(r['missing_terms']) for r in review(got['spec'],c['files'],c['documentation'])['requirements'])
  except Exception as e:row['error']=type(e).__name__+': '+str(e)[:250]
  row['rejected_calls']=sum(1 for call in trace if 'reply' in call)-int('proposal' in row);row.update(trace=trace,usage=usage,seconds=round(time.monotonic()-start,2));path.write_text(json.dumps(row,indent=2)+'\n');print(row['version'],row['id'],row['trial'],'correct',row['correct'],flush=True);return row
 with ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(attempt,packet['requests']))
 summary=summarize(rows,packet);(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2),flush=True)
if __name__=='__main__':freeze() if sys.argv[1]=='freeze' else run()
