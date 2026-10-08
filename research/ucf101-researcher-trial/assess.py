"""Compare a private trial receipt to the pre-model independent regex reference.
Usage: python assess.py /private/path/to/trial-directory
"""
import hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from app.ladder import _evaluate
from reference import audit,PATTERN

def assess(folder):
    freeze=json.loads((folder/'freeze.json').read_text());reference_bytes=(folder/'reference.json').read_bytes()
    assert hashlib.sha256(reference_bytes).hexdigest()==freeze['reference_sha256']
    reference=json.loads(reference_bytes);assert audit(folder/'original-splits.zip')==reference
    with zipfile.ZipFile(folder/'evidence.zip') as z:
        record=json.loads(z.read('measurement.json'));index=json.loads(z.read('bundle.json'))
        files={name:z.read(path).decode() for name,path in index['inputs'].items()}
    for name,text in files.items():assert hashlib.sha256(text.encode()).hexdigest()==freeze['files'][name]['sha256']
    spec=record['spec'];unit=next(l for l in spec['levels'] if l['name']==spec['claim']['level']);matched=0
    for source in spec['sources']:
        for line in files[source['file']].splitlines():
            expected=PATTERN.fullmatch(line);assert expected is not None
            key=expected['label']+'_g'+expected['group']
            actual=_evaluate(unit.get('by_source',{}).get(source['file'],unit['expression']),{'value':line},files,{},0)
            assert key==actual;matched+=1
    measured=next(l for l in record['result']['levels'] if l['name']==unit['name'])
    for actual,expected in [('train_rows','train_rows'),('test_rows','test_rows'),('train_units','train_groups'),('test_units','test_groups'),('shared','shared_groups'),('affected_test_rows','affected_test_rows')]:assert measured[actual]==reference[expected]
    assert measured['unmapped_rows']==0
    verification=json.loads((folder/'verification.json').read_text());assert verification['matches'] and verification['engine_hashes_match']
    calls=json.loads((folder/'calls.json').read_text());budget=json.loads((folder/'budget.json').read_text())
    return {'dataset':'UCF101 recognition split 1','reference_matches_every_row':matched,'train_clips':reference['train_rows'],'test_clips':reference['test_rows'],'train_groups':reference['train_groups'],'test_groups':reference['test_groups'],'shared_groups':reference['shared_groups'],'unmapped_rows':0,
      'initial_attempt_valid':record['binding_origin']['attempts'][0]['error'] is None,'provider_calls':len(calls),'automatic_validation_repairs':len(calls)-1,'tokens':sum(c.get('tokens',0) for c in calls),'provider_seconds':round(sum(c.get('seconds',0) for c in calls),3),
      'necessary_file_role_corrections':2,'necessary_group_binding_corrections_after_repair':0,'citation_range_added':[7,14],'optional_group_only_preview_exercise':True,'confirmation_operator':'Codex agent simulation, not a human participant',
      'sandbox_calls':json.loads((folder/'sandbox-count.json').read_text())['calls'],'execution':record['execution'],'receipt_id':record['id'],'origin':record['binding_origin'],'offline_verification_matches':True,'estimated_token_cost_usd':budget['settled_usd'],'human_usefulness_evidence':False}
if __name__=='__main__':print(json.dumps(assess(Path(sys.argv[1])),indent=2))
