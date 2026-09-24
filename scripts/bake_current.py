"""Bake current trusted sources, measure/replay 100k synthetic rows, then activate. --execute required."""
import hashlib,json,sys,time,resource
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'evaluation/probe-pilot'))
from common import credentials
from app.primitive_runtime import FILES,DRIVER,implementation_hash,PrimitiveSandbox
from app.primitives import measure,digest

def main():
    data=ROOT/'.data/product-repair';data.mkdir(exist_ok=True)
    files={'/opt/asterisk/app/'+n:(ROOT/'app'/n).read_bytes() for n in FILES};files.update({'/opt/asterisk/app/__init__.py':b'','/opt/asterisk/primitive_main.py':DRIVER.encode()})
    inventory={n:{'bytes':len(v),'sha256':hashlib.sha256(v).hexdigest()} for n,v in files.items()}
    (data/'upload-inventory.json').write_text(json.dumps({'trusted_source':inventory,'smoke_inputs':'Synthetic IDs only: 100,000 rows in each of two CSV files. No research or user data.'},indent=2))
    if '--execute' not in sys.argv:print('Inventory prepared. Pass --execute to bake, smoke/replay and activate.');return
    from contree_sdk import ContreeSync
    from contree_sdk.auth import IAMAuth
    from contree_sdk.config import ContreeConfig
    key,project=credentials();base=json.loads((ROOT/'.data/probe-pilot/environment.json').read_text())['image']
    client=ContreeSync(ContreeConfig(auth=IAMAuth(token=key,project_id=project),operation_timeout=150,transport_timeout=30))
    r=client.images.use(base).run('python',args=['-c',"import sys;sys.path.insert(0,'/opt/asterisk');from app.primitives import VERSION;print(VERSION)"],files=files,timeout=30,disposable=False).wait()
    if r.exit_code:raise SystemExit('Bake import failed; active image unchanged.')
    env={'image':str(r.uuid),'base_image':base,'implementation_hash':implementation_hash(),'version':r.stdout.strip(),'inventory_hash':digest(inventory),'driver_sha256':hashlib.sha256(DRIVER.encode()).hexdigest()}
    (data/'candidate-environment.json').write_text(json.dumps(env,indent=2));print('Baked candidate '+env['image'],flush=True)
    args={'split_file':'split.csv','mapping_file':'map.csv','sample_column':'sample','mapping_sample_column':'sample','partition_column':'partition','entity_column':'entity','train_values':['train'],'test_values':['test']}
    inputs={'split.csv':'sample,partition\n'+''.join(f'{i},{"train" if i<80000 else "test"}\n' for i in range(100000)), 'map.csv':'sample,entity\n'+''.join(f'{i},{i%80000}\n' for i in range(100000))}
    start=time.perf_counter();local=measure('entity_overlap',inputs,args);elapsed=time.perf_counter()-start
    sandbox=PrimitiveSandbox(key,project,env['image']);first=sandbox.primitive('entity_overlap',args,inputs);second=sandbox.primitive('entity_overlap',args,inputs)
    valid=not first.get('execution_error') and not second.get('execution_error') and first['output']==second['output']==local['output']
    report={'rows_per_csv':100000,'cells':400000,'input_bytes':sum(len(t.encode()) for t in inputs.values()),'local_seconds':elapsed,'host_peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'implementation_hash':implementation_hash(),'measurement':first,'replay':second,'outputs_equal':valid}
    (data/'100k-benchmark.json').write_text(json.dumps(report,indent=2))
    if not valid:raise SystemExit('Smoke/replay failed; active image unchanged.')
    newline_reports=[]
    for ending in ('\n','\r\n'):
        small={'split.csv':('sample,partition\na,train\nb,test\n').replace('\n',ending),
               'map.csv':('sample,entity\na,p1\nb,p1\n').replace('\n',ending)}
        expected=measure('entity_overlap',small,args)
        runs=[sandbox.primitive('entity_overlap',args,small) for _ in range(2)]
        match=all(not r.get('execution_error') and all(r.get(k)==expected.get(k) for k in ('input_hashes','output','arguments','primitive','version')) for r in runs)
        newline_reports.append({'line_ending':repr(ending),'matches':match,'measurement':runs[0],'replay':runs[1]})
    (data/'newline-replay.json').write_text(json.dumps(newline_reports,indent=2))
    if not all(r['matches'] for r in newline_reports):raise SystemExit('Newline replay failed; active image unchanged.')
    active=ROOT/'.data/primitive-v4';immutable=active/('environment-'+env['image']+'.json')
    with immutable.open('x') as f:json.dump(env,f,indent=2)
    (active/'environment.json').write_text(json.dumps(env,indent=2));print(json.dumps({'activated':env,'local_seconds':elapsed,'remote_seconds':[first['execution']['seconds'],second['execution']['seconds']],'outputs_equal':valid},indent=2))
if __name__=='__main__':main()
