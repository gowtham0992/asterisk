"""Fixed, exposed development study. Raw inputs and all responses remain private."""
import concurrent.futures,hashlib,importlib.util,json,os,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from app import ladder,ladder_proposal as lp
from app.ladder_api import DEFAULT_MODEL,token_factory
from variant import install
install(lp)
OUT=ROOT/'.data/ladder-source-grammar-v7-20261007'
from datetime import datetime,timezone
DEADLINE=datetime(2026,10,8,4,25,tzinfo=timezone.utc).timestamp()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def reference(claim,sources,expr,doc,end=3):
 return {'schema':'asterisk-ladder/1','claim':{'text':claim,'level':'unit'},'sources':sources,
  'levels':[{'name':'observation','kind':'observation','expression':sources[0]['sample']},{'name':'unit','kind':'unit','expression':expr}],
  'citations':[{'file':doc,'start_line':1,'end_line':end}]}
def freeze():
 OUT.mkdir(exist_ok=True)
 if (OUT/'packet.json').exists():raise RuntimeError('Already frozen')
 u=ROOT/'.data/ucf101-researcher-trial-20261007';files={p.name:p.read_text() for p in (u/'inputs').iterdir()}
 calls=json.loads((u/'calls.json').read_text());claim=json.loads(calls[0]['messages'][1]['content'])['claim'];ref=json.loads(calls[1]['response'])['spec']
 cases=[{'id':'ucf101-exposed','claim':claim,'files':files,'reference':ref,'documentation':['researcher-notes.md'],'share':[['trainlist01.txt','value'],['testlist01.txt','value']],'origin':'Original public identifier-only lists; previously observed trial, not held out'}]
 claim='No evaluation action-qualified source-video group occurs in training.'
 files={'fit.txt':'Drill/v_Drill_g03_c01.avi 1\nSpin/v_Spin_g03_c01.avi 2\nDrill/v_Drill_g04_c01.avi 1\n','check.txt':'Drill/v_Drill_g03_c02.avi\nSpin/v_Spin_g04_c02.avi\n',
 'README.md':'Each filename is v_<action>_<group>_<clip>.avi; a row is one clip.\nA source-video group is the action together with the group token; group numbers are local to an action.\nfit.txt is training; check.txt is evaluation. The numeric suffix after a space in fit.txt is a class label, not a group or clip identity.\n'}
 sources=[{'file':n,'format':'lines','sample':{'column':'value'},'partition':{'value':p}} for n,p in [('fit.txt','train'),('check.txt','test')]]
 cases.append({'id':'qualified-lines','claim':claim,'files':files,'reference':reference(claim,sources,{'column':'value','basename':True,'field':{'separator':'_','from':2,'to':3}},'README.md')})
 claim='No evaluation material specimen appears in training.'
 files={'observations.csv':'record,assignment\nAB0001x,fit\nAB0001y,check\nCD0002x,fit\nCD0003x,check\n','README.md':'record names one observation.\nIn record, characters 3 through 6 (1-based, inclusive) identify the material specimen. Letters before that segment and the final letter do not identify the specimen.\nassignment fit means training and check means evaluation.\n'}
 sources=[{'file':'observations.csv','format':'csv','sample':{'column':'record'},'partition':{'column':'assignment','map':{'fit':'train','check':'test'}}}]
 cases.append({'id':'middle-characters','claim':claim,'files':files,'reference':reference(claim,sources,{'column':'record','characters':{'from':3,'to':6}},'README.md')})
 files={'observations.csv':'record,assignment\nx7,fit\ny2,check\nz9,fit\nw4,check\n','registry.csv':'capture,origin,station\nx7,lot-Q,line-1\ny2,lot-Q,line-2\nz9,lot-R,line-1\nw4,lot-S,line-2\n',
 'README.md':'record identifies one capture; registry.csv capture matches it exactly.\norigin is not an image coordinate: in this current registry it identifies the material specimen that generated the capture. station names equipment, not a specimen.\nassignment fit means training and check means evaluation.\n'}
 cases.append({'id':'lookup-distractor','claim':claim,'files':files,'reference':reference(claim,sources,{'lookup':{'file':'registry.csv','format':'csv','key_column':'capture','value_column':'origin','on':{'column':'record'}}},'README.md')})
 denied={**files,'README.md':'record identifies one capture; registry.csv capture matches it exactly.\norigin identifies equipment, NOT a material specimen. No material-specimen mapping is supplied.\nassignment fit means training and check means evaluation.\n'}
 cases.append({'id':'denied-specimen','claim':claim,'files':denied,'reference':None})
 cases.append({'id':'actor-missing','claim':'No evaluation actor occurs in training.','files':{'fit.txt':'Drill/v_Drill_g08_c01.avi 1\n','check.txt':'Spin/v_Spin_g01_c01.avi\n','README.md':'Each row is a clip with action, source-video group and clip tokens in its filename.\nfit.txt is training; check.txt is evaluation. Source-video groups do not identify actors; no actor mapping is supplied.\n'},'reference':None})
 for c in cases:
  c.setdefault('documentation',['README.md'])
  if 'share' not in c:
   c['share']=[[n,col] for n,t in c['files'].items() if n not in c['documentation'] for col in (t.splitlines()[0].split(',') if n.endswith('.csv') else ['value'])]
  c.setdefault('origin','Original fictional development case authored by implementer')
  if c['reference']:ladder.measure(c['reference'],c['files'])
 requests=[{'id':c['id'],'version':v,'trial':trial,'messages':lp.request(c['claim'],c['files'],c['share'],c['documentation'],v)} for trial in [1,2] for c in cases for v in ['v4','v7']]
 packet={'cases':cases,'requests':requests,'maximum_calls':48,'maximum_proposals':24,'cap_usd':1,'deadline_utc':'2026-10-08T04:25:00Z','model':DEFAULT_MODEL}
 (OUT/'packet.json').write_text(json.dumps(packet,indent=2)+'\n')
 (OUT/'freeze.json').write_text(json.dumps({'created_utc':datetime.now(timezone.utc).isoformat(),'packet_sha256':sha(OUT/'packet.json'),'runner_sha256':sha(Path(__file__)),'candidate_sha256':sha(Path(__file__).with_name('variant.py')),'protocol_sha256':sha(Path(__file__).with_name('PROTOCOL.md')),'application_sha256':sha(ROOT/'app/ladder_proposal.py'),'system_prompts':{v:hashlib.sha256(lp.PROMPTS[v].encode()).hexdigest() for v in ['v4','v7']},'source_hashes':{c['id']:{n:hashlib.sha256(t.encode()).hexdigest() for n,t in c['files'].items()} for c in cases}},indent=2)+'\n')
 print('Frozen 24 proposals; at most 48 calls; $1 estimated cap; no Sandbox or judge calls')
def partitions(spec,files):return {r['sample']:r['partition'] for r in ladder.population(spec,files)['lineage']}
def correct(g,c):
 if c['reference'] is None:return g['status']=='abstain'
 if g['status']!='ladder':return False
 return lp.semantic_match(g['spec'],c['reference'],c['files'])['same_grouping'] and partitions(g['spec'],c['files'])==partitions(c['reference'],c['files'])
def summarize(rows,packet):
 result={}
 for v in ['v4','v7']:
  rs=[r for r in rows if r['version']==v];result[v]={k:sum(r.get(k,False) for r in rs) for k in ['first_valid','first_correct','final_correct','unsupported','wrong_reassurance','rejected_calls']};result[v]['proposals']=len(rs);result[v]['tokens']=sum(r['usage']['total_tokens'] for r in rs);result[v]['calls']=sum(len(r['trace']) for r in rs)
 pairs={(r['id'],r['trial'],r['version']):r for r in rows};regressions=[(r['id'],r['trial']) for r in rows if r['version']=='v7' and not r['final_correct'] and pairs.get((r['id'],r['trial'],'v4'),{}).get('final_correct')]
 a,b=result['v4'],result['v7'];result['paired_regressions']=regressions;result['complete']=len(rows)==24 and not any('error' in r for r in rows)
 result['promote']=result['complete'] and b['final_correct']==12 and b['unsupported']==b['wrong_reassurance']==0 and not regressions and b['first_correct']>=a['first_correct']+2 and b['rejected_calls']<a['rejected_calls'] and all(r['first_correct'] for r in rows if r['version']=='v7' and r['id']=='ucf101-exposed')
 return result
def run():
 frozen=json.loads((OUT/'freeze.json').read_text());assert sha(OUT/'packet.json')==frozen['packet_sha256'];assert sha(Path(__file__))==frozen['runner_sha256'];assert sha(ROOT/'app/ladder_proposal.py')==frozen['application_sha256'];assert sha(Path(__file__).with_name('variant.py'))==frozen['candidate_sha256']
 for v in ['v4','v7']:assert hashlib.sha256(lp.PROMPTS[v].encode()).hexdigest()==frozen['system_prompts'][v]
 packet=json.loads((OUT/'packet.json').read_text());b=importlib.util.spec_from_file_location('study_budget',ROOT/'evaluation/probe-pilot/budget.py');m=importlib.util.module_from_spec(b);b.loader.exec_module(m);budget=m.Budget(OUT/'budget.json',{DEFAULT_MODEL:(.5,1.5)},limit=1)
 os.environ['ASTERISK_DB']=str(OUT/'bootstrap.sqlite');import app.main
 key=os.environ['NEBIUS_API_KEY']
 def attempt(item):
  path=OUT/f"{item['version']}-{item['id']}-{item['trial']}.json"
  if path.exists():return json.loads(path.read_text())
  c=next(c for c in packet['cases'] if c['id']==item['id']);complete,usage=token_factory(DEFAULT_MODEL,key);trace=[];row={k:item[k] for k in ['id','version','trial']};row.update(first_valid=False,first_correct=False,final_correct=False,unsupported=False,wrong_reassurance=False,rejected_calls=0);start=time.monotonic()
  def paid(messages,maximum,timeout):
   if time.time()>=DEADLINE:raise RuntimeError('Study deadline reached; no call')
   rid=budget.reserve(DEFAULT_MODEL,len(json.dumps(messages).encode())+3000,maximum)
   if rid is None:raise RuntimeError('Fixed cap exhausted; no call')
   entry={'messages':messages};trace.append(entry);before=usage['total_tokens']
   try:reply=complete(messages,maximum,min(timeout,max(1,int(DEADLINE-time.time()))));entry['reply']=reply
   except BaseException as e:entry['error']=type(e).__name__;budget.uncertain(rid);raise
   budget.settle(rid,0,usage['total_tokens']-before);return reply
  try:
   got,attempts=lp.propose(c['claim'],c['files'],paid,c['share'],documentation=c['documentation'],version=item['version']);row['proposal']=got;row['attempts']=attempts;row['final_correct']=correct(got,c);row['unsupported']=c['reference'] is None and got['status']!='abstain'
   if got['status']=='ladder':row['wrong_reassurance']=not row['final_correct'] and ladder.measure(got['spec'],c['files'])['finding']['status']=='held_out_pending_confirmation'
  except Exception as e:row['error']=type(e).__name__+': '+str(e)[:500]
  if trace and 'reply' in trace[0]:
   try:first=lp.parse(trace[0]['reply'],c['files'],c['claim'],c['documentation']);row['first_valid']=True;row['first_correct']=correct(first,c)
   except lp.ladder.LadderError:pass
  row['rejected_calls']=sum('reply' in x for x in trace)-int('proposal' in row);row.update(trace=trace,usage=usage,seconds=round(time.monotonic()-start,3));path.write_text(json.dumps(row,indent=2)+'\n');print(item['version'],item['id'],item['trial'],'first',row['first_correct'],'final',row['final_correct'],flush=True);return row
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(attempt,packet['requests']))
 result=summarize(rows,packet);result['estimated_usd']=budget.state['settled_usd'];(OUT/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':freeze() if sys.argv[1]=='freeze' else run()
