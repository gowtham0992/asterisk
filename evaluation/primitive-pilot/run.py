"""Run only sealed, post-freeze cases. No overwrite, hidden retry, or prompt tuning."""
import argparse,fcntl,json,re,sys
from collections import Counter
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'evaluation/probe-pilot'))
from common import credentials
from budget import Budget
from app.probes import investigate,sha,validate_files
from app.primitive_runtime import PrimitiveSandbox
from app.probe_evidence import bundle
from freeze import check
from scoring import score,summarize
DATA=ROOT/'.data/primitive-pilot'
MODEL='nvidia/nemotron-3-super-120b-a12b'
def validate(manifest,frozen,root):
    if manifest.get('freeze_hash')!=sha(json.dumps(frozen,sort_keys=True)):raise ValueError('Case set refers to a different freeze.')
    cases=manifest['cases']
    if len(cases)!=12 or len({c['id'] for c in cases})!=12:raise ValueError('Exactly twelve unique cases required.')
    for category in ('entity_overlap','preprocessing','checkpoint_selection'):
        if Counter(c['expected']['verdict'] for c in cases if c['category']==category)!=Counter(violation=2,clear=1,insufficient=1):raise ValueError('Each category requires two violations, one clean, one insufficient.')
    families={c['source']['family'] for c in cases}
    if not {'yang','drug_response','planted'}<=families:raise ValueError('All three source families required.')
    for category in ('entity_overlap','preprocessing','checkpoint_selection'):
        if not any(c['category']==category and c['source']['family']=='planted' for c in cases):raise ValueError('One planted variant per category required.')
    for c in cases:
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,60}',c['id']):raise ValueError('Unsafe case ID.')
        if datetime.fromisoformat(c['authored_at'])<=datetime.fromisoformat(frozen['frozen_at']):raise ValueError('Cases must be authored after the freeze.')
        if not c['expected'].get('review_requires'):raise ValueError('Freeze explicit evidence review requirements for every case.')
        for field in ('url','revision','license','transformations'):
            if not c['source'].get(field):raise ValueError('Source provenance incomplete: '+field)
        if not c.get('author'):raise ValueError('Record the case author.')
        variants=[c]
        if c['expected']['verdict']=='violation':
            if c.get('twin',{}).get('expected',{}).get('verdict')!='clear':raise ValueError('Every violation needs a defect-removed clear twin.')
            variants.append(c['twin'])
        for v in variants:
            if not v['expected'].get('review_requires'):raise ValueError('Every case and twin needs review requirements.')
            files={}
            for name,digest in v['input_hashes'].items():
                path=(root/v['directory']/name).resolve()
                if not path.is_relative_to(root.resolve()):raise ValueError('Input path escapes case directory.')
                files[name]=path.read_text()
                if sha(files[name])!=digest:raise ValueError('Case input changed.')
            validate_files(files)
    return cases

def main():
    p=argparse.ArgumentParser();p.add_argument('manifest',type=Path);p.add_argument('--confirm-upload',action='store_true');p.add_argument('--report-only',action='store_true');p.add_argument('--review',type=Path);a=p.parse_args()
    frozen=json.loads((DATA/'freeze.json').read_text());check(frozen)
    manifest=json.loads(a.manifest.read_text());cases=validate(manifest,frozen,a.manifest.parent)
    lock=(ROOT/'.data/probe-pilot/batch.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    seal=DATA/'cases-sealed.json';serialized=json.dumps(manifest,sort_keys=True,indent=2)
    if seal.exists() and seal.read_text()!=serialized:raise SystemExit('Sealed cases changed. New experiment required.')
    if not seal.exists():
        with seal.open('x') as f:f.write(serialized)
    review=json.loads(a.review.read_text()) if a.review else None
    runroot=DATA/'runs';runroot.mkdir(exist_ok=True)
    jobs=[]
    for c in cases:
        for trial in (1,2):
            jobs.append((c,c,trial,c['id']))
            if c['expected']['verdict']=='violation':jobs.append((c,c['twin'],trial,c['id']+'-twin'))
    if not a.report_only:
        if not a.confirm_upload:raise SystemExit('Review the sealed source inventory, then use --confirm-upload to authorize its upload.')
        key,project=credentials();budget=Budget(ROOT/'.data/probe-pilot/budget.json',{MODEL:(.30,.90)},limit=10)
        for c,v,trial,id in jobs:
            out=runroot/f'{id}-trial{trial}'
            if (out/'result.json').exists() or (out/'failure.json').exists():continue
            files={n:(a.manifest.parent/v['directory']/n).read_text() for n in v['input_hashes']}
            events=runroot/(out.name+'.events.jsonl')
            if events.exists():
                out.mkdir(exist_ok=True)
                (out/'failure.json').write_text(json.dumps({'error':'interrupted_attempt','note':'Partial transcript retained; no automatic retry.'}))
                continue
            events.touch(exist_ok=False)
            def event(e):
                with events.open('a') as f:f.write(json.dumps(e)+'\n')
            try:
                r=investigate(c['claim'],files,key,MODEL,PrimitiveSandbox(key,project,frozen['image']),category=c['category'],budget=budget,on_event=event)
                r.update(case_id=id,trial=trial,freeze_hash=manifest['freeze_hash'],estimated_usd=(r['tokens']['prompt']*.30+r['tokens']['completion']*.90)/1e6)
                bundle(r,files,out)
                print(json.dumps({'case':id,'trial':trial,'status':r['status'],'verdict':r.get('verdict'),'estimated_usd':r['estimated_usd']}),flush=True)
            except Exception as exc:
                out.mkdir(exist_ok=True)
                (out/'failure.json').write_text(json.dumps({'case_id':id,'trial':trial,'error':type(exc).__name__,'note':'Attempt retained; uncertain token reservations remain charged.'}))
    rows=[];allrows={}
    for c,v,trial,id in jobs:
        path=runroot/f'{id}-trial{trial}'/'result.json'
        if not path.exists():continue
        r=json.loads(path.read_text());human=(review or {}).get('runs',{}).get(f'{id}-trial{trial}')
        row={'case_id':id,'trial':trial,'expected':v['expected'],'result':r,'score':score(r,v['expected'],human),'estimated_usd':r['estimated_usd']};allrows[id,trial]=row
        if id==c['id']:rows.append(row)
    twins=[]
    for c in cases:
        if 'twin' not in c:continue
        pairs=[(allrows.get((c['id'],t)),allrows.get((c['id']+'-twin',t))) for t in (1,2)]
        complete=all(x and y for x,y in pairs)
        verdict=lambda r:(r['result'].get('verdict') or {}).get('verdict')
        twins.append({'case_id':c['id'],'complete':complete,'different':complete and all(verdict(x)=='violation' and verdict(y)=='clear' for x,y in pairs),'false_clear':any(x and verdict(x)=='clear' for x,y in pairs),'replay_match':complete and all(x['score']['primitive_replay_match'] and y['score']['primitive_replay_match'] for x,y in pairs)})
    summary=summarize(rows,twins,review);summary['runs']=[{k:v for k,v in r.items() if k not in ('result','expected')} for r in allrows.values()]
    (DATA/'acceptance-report.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
