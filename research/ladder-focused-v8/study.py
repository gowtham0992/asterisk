"""Frozen, original fictional development cases; no human or held-out claims."""
import concurrent.futures
import hashlib
import importlib.util
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from app import ladder, ladder_proposal as lp
from app.ladder_api import DEFAULT_MODEL, BASE
from variant import install
install()
OUT = ROOT / '.data/ladder-focused-v8-20261009'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cases():
    result = []
    def add(name, claim, files, mapping=None, partitions=None):
        docs = ['README.md']
        share = [[n,c] for n,t in files.items() if n not in docs for c in (t.splitlines()[0].split(',') if n.endswith('.csv') else ['value'])]
        result.append(dict(id=name, claim=claim, files=files, documentation=docs, share=share,
                           expected_units=mapping, expected_partitions=partitions))
    add('namespaced-lines','Evaluation source-video groups are unseen in training.',{
        'fit.txt':'Vault/v_Vault_g04_c01.mp4 1\nHurdle/v_Hurdle_g04_c01.mp4 2\nVault/v_Vault_g06_c01.mp4 1\n',
        'report.txt':'Vault/v_Vault_g04_c02.mp4\nHurdle/v_Hurdle_g06_c01.mp4\n',
        'README.md':'One row is a video clip. fit.txt is training; report.txt is evaluation.\nA filename is v_<action>_<group>_<clip>.mp4. The numeric suffix after a space in fit.txt is a class label.\nSource-video groups are the action and group together: group numbers are local to each action. No actor identities are recorded.\n'},
        {'Vault/v_Vault_g04_c01.mp4 1':'Vault_g04','Hurdle/v_Hurdle_g04_c01.mp4 2':'Hurdle_g04','Vault/v_Vault_g06_c01.mp4 1':'Vault_g06','Vault/v_Vault_g04_c02.mp4':'Vault_g04','Hurdle/v_Hurdle_g06_c01.mp4':'Hurdle_g06'},
        {'Vault/v_Vault_g04_c01.mp4 1':'train','Hurdle/v_Hurdle_g04_c01.mp4 2':'train','Vault/v_Vault_g06_c01.mp4 1':'train','Vault/v_Vault_g04_c02.mp4':'test','Hurdle/v_Hurdle_g06_c01.mp4':'test'})
    assignments={'PX031a':'train','QZ031b':'test','PX032a':'train','QZ033b':'test'}
    add('middle-segment','Evaluation material batches are unseen in training.',{
        'runs.csv':'capture,partition\nPX031a,train\nQZ031b,test\nPX032a,train\nQZ033b,test\n',
        'README.md':'capture identifies one capture; partition records train or test.\nCharacters 3 through 5, 1-based inclusive, identify a material batch globally. The initial two letters identify apparatus, not a batch.\n'},
        {s:s[2:5] for s in assignments},assignments)
    assignments={'r1':'train','r2':'test','r3':'train','r4':'test'}
    files={'captures.csv':'capture,partition\nr1,train\nr2,test\nr3,train\nr4,test\n',
           'dictionary.csv':'capture,origin,patient,device\nr1,bA,cam1,rig1\nr2,bA,cam2,rig2\nr3,bB,cam1,rig1\nr4,bC,cam2,rig2\n',
           'README.md':'captures.csv is the observation table: capture identifies a photograph; partition gives train or test.\ndictionary.csv joins on capture. origin identifies the botanical plant from which the photographed leaf was collected. patient is a camera code and device is the imaging rig; neither identifies a plant.\n'}
    add('lookup-distractors','Evaluation plants are unseen in training.',files,dict(r1='bA',r2='bA',r3='bB',r4='bC'),assignments)
    add('source-overrides','Evaluation speakers are unseen in training.',{
        'learning.csv':'clip,talker\na,t7\nb,t8\n','assessment.csv':'record,voice\nc,t7\nd,t9\n',
        'README.md':'learning.csv contains training clips. assessment.csv contains evaluation clips.\nclip in learning.csv and record in assessment.csv are globally unique recording identifiers.\ntalker in learning.csv and voice in assessment.csv both identify the person speaking; multiple clips can belong to one person.\n'},dict(a='t7',b='t8',c='t7',d='t9'),dict(a='train',b='train',c='test',d='test'))
    add('excluded-label','Evaluation specimens are unseen in training.',{
        'captures.csv':'sample,partition,unit\na,learn,k1\nb,report,k1\nc,unused,k9\nd,learn,k2\ne,report,k3\n',
        'README.md':'sample identifies a capture; unit identifies the physical specimen generating the capture.\npartition learn is training, report is evaluation, and unused is excluded from this claim. Do not rebuild the partition from unit.\n'},dict(a='k1',b='k1',c='k9',d='k2',e='k3'),dict(a='train',b='test',c='excluded',d='train',e='test'))
    assignments={'North-07-01.fits':'train','South-07-01.fits':'train','North-07-02.fits':'test','South-08-01.fits':'test'}
    add('qualified-night','Evaluation observing nights are unseen in training.',{
        'exposures.csv':'image,partition\nNorth-07-01.fits,train\nSouth-07-01.fits,train\nNorth-07-02.fits,test\nSouth-08-01.fits,test\n',
        'README.md':'image identifies one exposure; partition records train or test.\nFilenames are <observatory>-<night>-<exposure>.fits. Night numbers restart separately at each observatory. An observing night is observatory plus night; numbers alone do not identify a night globally.\n'},{s:'-'.join(s.split('-')[:2]) for s in assignments},assignments)
    add('observation-claim','Evaluation recording identifiers are unseen in training.',{
        'records.csv':'record,partition,speaker\nrec1,train,p1\nrec2,test,p1\nrec3,train,p2\nrec4,test,p3\n',
        'README.md':'record is a globally unique recording identifier; partition records train or test.\nspeaker is the person speaking. This claim is about recording identifiers, not speaker independence.\n'},dict(rec1='rec1',rec2='rec2',rec3='rec3',rec4='rec4'),dict(rec1='train',rec2='test',rec3='train',rec4='test'))
    add('sample-id-trap','Evaluation animals are unseen in training.',{
        'frames.csv':'sample,subject,origin,partition\nx,frameX,fox1,train\ny,frameY,fox1,test\nz,frameZ,fox2,train\nw,frameW,fox3,test\n',
        'README.md':'sample and subject each identify a single image frame, never an animal.\norigin identifies the individual animal in that frame, using a reviewed tagging registry. partition records train or test.\n'},dict(x='fox1',y='fox1',z='fox2',w='fox3'),dict(x='train',y='test',z='train',w='test'))
    add('absent-actor','Evaluation actors are unseen in training.',{
        'clips.csv':'clip,partition,group\nc1,train,g1\nc2,test,g2\n',
        'README.md':'clip identifies one video clip; partition records train or test. group identifies a source recording, not an actor. No actor mapping is provided.\n'})
    add('denying-binding','Evaluation patients are unseen in training.',{
        'records.csv':'sample,patient,partition\na,scanner1,train\nb,scanner2,test\n',
        'README.md':'sample identifies an image; partition records train or test.\nThe legacy patient column actually identifies the scanner device, NOT the patient. No mapping to patients is supplied.\n'})
    add('unsupported-noncontiguous','Evaluation specimens are unseen in training.',{
        'records.csv':'sample,partition\nA_01_B_v1,train\nA_02_B_v2,test\nC_01_D_v1,train\n',
        'README.md':'sample identifies one image; partition records train or test.\nNames have four underscore-separated fields. A specimen is the concatenation of fields 1 and 3 only. Field 2 is a session and field 4 is a view. No specimen mapping is supplied.\n'})
    add('unknown-partition','Evaluation specimens are unseen in training.',{
        'records.csv':'sample,unit,assignment\na,p1,one\nb,p1,two\nc,p2,one\n',
        'README.md':'sample identifies an observation; unit identifies the physical specimen.\nassignment has values one and two, but the train/evaluation assignment key is missing. Neither file order nor the unit identifies a partition.\n'})
    return result


def groups(mapping):
    grouped={}
    for sample, unit in mapping.items(): grouped.setdefault(unit,set()).add(sample)
    return {frozenset(v) for v in grouped.values()}


def correct(proposal, case):
    if case['expected_units'] is None:
        return proposal['status']=='abstain'
    if proposal['status']!='ladder': return False
    spec=proposal['spec'];base=ladder.population(spec,case['files'])
    level=next(l for l in spec['levels'] if l['name']==spec['claim']['level'])
    index=ladder._record_index(case['files'],spec)
    values,missing=ladder._derive(spec,level,case['files'],base,index)
    # Compare the original observation rows, independent of a valid renamed sample key.
    original_values,partition={},{}
    for row in base['lineage']:
        if row['sample'] not in values: return False
        for occurrence in row['occurrences']:
            original=next(iter(index[ladder._ref_key(occurrence)].values()))
            original_values[original]=values[row['sample']]
            partition[original]=row['partition']
    return not missing and set(original_values)==set(case['expected_units']) and groups(original_values)==groups(case['expected_units']) and partition==case['expected_partitions']


def freeze():
    OUT.mkdir(exist_ok=True)
    if (OUT/'packet.json').exists(): raise RuntimeError('Already frozen')
    packet={'cases':cases(),'arms':['v4','v8'],'trials':[1,2],'maximum_calls':96,'cap_usd':3,'model':DEFAULT_MODEL}
    packet['requests']=[{'id':c['id'],'version':v,'trial':t,'messages':lp.request(c['claim'],c['files'],c['share'],c['documentation'],v)} for t in packet['trials'] for c in packet['cases'] for v in packet['arms']]
    (OUT/'packet.json').write_text(json.dumps(packet,indent=2)+'\n')
    paths=[Path(__file__),Path(__file__).with_name('variant.py'),Path(__file__).with_name('PROTOCOL.md'),ROOT/'app/ladder_proposal.py',ROOT/'app/ladder.py']
    frozen={'created_utc':datetime.now(timezone.utc).isoformat(),'packet_sha256':sha(OUT/'packet.json'),'hashes':{str(p.relative_to(ROOT)):sha(p) for p in paths},'maximum_calls':96,'cap_usd':3}
    (OUT/'freeze.json').write_text(json.dumps(frozen,indent=2)+'\n')
    print('Frozen:',len(packet['cases']),'cases;',len(packet['requests']),'proposals; maximum 96 calls; $3 cap')


def summarize(rows):
    arms={v:{'first_correct':sum(r['first_correct'] for r in rows if r['version']==v),'final_correct':sum(r['final_correct'] for r in rows if r['version']==v),'calls':sum(len(r['trace']) for r in rows if r['version']==v),'tokens':sum(r['tokens'] for r in rows if r['version']==v)} for v in ['v4','v8']}
    pairs={(r['id'],r['trial'],r['version']):r for r in rows}
    regressions=[(r['id'],r['trial']) for r in rows if r['version']=='v8' and not r['final_correct'] and pairs.get((r['id'],r['trial'],'v4'),{}).get('final_correct')]
    complete=len(rows)==48 and all(r['trace'] and all('reply' in c for c in r['trace']) for r in rows)
    return {'arms':arms,'complete':complete,'paired_regressions':regressions,'promote':complete and arms['v8']['final_correct']==24 and not regressions and arms['v8']['first_correct']>=arms['v4']['first_correct']+2}


def run():
    frozen=json.loads((OUT/'freeze.json').read_text());assert sha(OUT/'packet.json')==frozen['packet_sha256']
    for name,digest in frozen['hashes'].items(): assert sha(ROOT/name)==digest
    packet=json.loads((OUT/'packet.json').read_text())
    module=importlib.util.spec_from_file_location('study_budget',ROOT/'evaluation/probe-pilot/budget.py');budget_module=importlib.util.module_from_spec(module);module.loader.exec_module(budget_module)
    budget=budget_module.Budget(OUT/'budget.json',{DEFAULT_MODEL:(10,10)},limit=3)
    # Load only named credentials, without importing or modifying the product DB.
    for line in (ROOT/'.env').read_text().splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            name,value=line.split('=',1)
            if name.strip() in ['NEBIUS_API_KEY','NEBIUS_BASE_URL']:os.environ.setdefault(name.strip(),value.strip().strip('\"').strip("'"))
    from openai import OpenAI
    def attempt(item):
        target=OUT/f"{item['version']}-{item['id']}-{item['trial']}.json"
        if target.exists(): raise RuntimeError('No reruns permitted')
        case=next(c for c in packet['cases'] if c['id']==item['id']);row={k:item[k] for k in ['id','version','trial']};row.update(first_correct=False,final_correct=False,trace=[],tokens=0);start=time.monotonic()
        def complete(messages,maximum,timeout):
            reservation=budget.reserve(DEFAULT_MODEL,len(json.dumps(messages).encode())+3000,maximum)
            if reservation is None: raise RuntimeError('Fixed budget exhausted; no call')
            call={'messages':messages};row['trace'].append(call)
            try:
                with OpenAI(base_url=os.getenv('NEBIUS_BASE_URL',BASE),api_key=os.environ['NEBIUS_API_KEY'],timeout=timeout,max_retries=0) as client:
                    response=client.chat.completions.create(model=DEFAULT_MODEL,messages=messages,temperature=0,max_tokens=maximum,response_format={'type':'json_object'})
                call.update(reply=response.choices[0].message.content or '',finish_reason=response.choices[0].finish_reason,usage=response.usage.model_dump() if response.usage else None)
                tokens=response.usage.total_tokens if response.usage else None
                if tokens is None:budget.uncertain(reservation)
                else:budget.settle(reservation,0,tokens);row['tokens']+=tokens
                return call['reply']
            except BaseException as exc:
                call['provider_error']=type(exc).__name__;budget.uncertain(reservation);raise
        try:
            proposal,attempts=lp.propose(case['claim'],case['files'],complete,case['share'],documentation=case['documentation'],version=item['version'])
            row.update(proposal=proposal,attempts=attempts,final_correct=correct(proposal,case))
        except Exception as exc:row['error']=type(exc).__name__+': '+str(exc)[:500]
        if row['trace'] and 'reply' in row['trace'][0]:
            try:row['first_correct']=correct(lp.parse(row['trace'][0]['reply'],case['files'],case['claim'],case['documentation']),case)
            except (ValueError,lp.executor.ExtractionError):pass
        row['seconds']=round(time.monotonic()-start,3);target.write_text(json.dumps(row,indent=2)+'\n');print(item['version'],item['id'],item['trial'],'first',row['first_correct'],'final',row['final_correct'],flush=True)
        return row
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(attempt,packet['requests']))
    summary=summarize(rows);summary['estimated_usd']=budget.state['settled_usd'];summary['uncertain_reservations']=budget.state['uncertain'];summary['promote']=summary['promote'] and not summary['uncertain_reservations']
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))


if __name__=='__main__':
    freeze() if sys.argv[1]=='freeze' else run()
