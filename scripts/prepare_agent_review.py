"""Prepare historical, outcome-blind automated review inputs; no provider calls."""
import json,hashlib,sys,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from app.receipt_view import render_receipt
out=R/'.data/agent-review-2026-09-18'
if (out/'packet-manifest.json').exists():
    raise SystemExit('Review packet already committed; refusing to overwrite reviewed artifacts.')
out.mkdir(exist_ok=True)
selected=[('E1-ptbxl-random',16),('E2-har-window-random',12),('E3-parkinsons-recording-random',1),('E4-leaf-plots-control',2),('E1-ptbxl-random-twin',11),('E5-ptbxl-coverage-gap',9)]
# Fixed order committed before reviewers begin; no outcome-based selection.
order=[3,0,5,2,4,1]; provenance=[]
for i,j in enumerate(order,1):
 name,b=selected[j];dest=out/'evidence'/f'case-{i:02d}';dest.mkdir(parents=True,exist_ok=True)
 src=R/'.data/primitive-v3/acceptance/runs'/f'{name}-trial1'/'evidence'
 result=json.loads((src/'result.json').read_text());files={p.relative_to(src/'inputs').as_posix():p.read_text() for p in (src/'inputs').rglob('*') if p.is_file()}
 hashes={n:hashlib.sha256(t.encode()).hexdigest() for n,t in files.items()};assert hashes==result['input_hashes']
 shutil.copytree(src/'inputs',dest/'inputs',dirs_exist_ok=True)
 (dest/'claim.txt').write_text(result.get('original_claim') or result['claim'])
 (dest/'receipt.html').write_text(render_receipt(result,files))
 # Retain only reviewer-facing measurement material, excluding case/runner metadata.
 visible={k:result[k] for k in ['claim','original_claim','verdict','input_hashes','primitive_measurements','primitive_replays','binding_confirmation','preflight_confirmation'] if k in result}
 (dest/'measurement.json').write_text(json.dumps(visible,indent=2))
 bp=R/'.data/primitive-v4/general-baseline/results'/f'case-{b:02d}.json';base=json.loads(bp.read_text())
 for n,t in files.items():assert base['input_sha256']['inputs/'+n]==hashes[n]
 base['case_id']=dest.name;base.pop('reproduction',None)
 (dest/'comparison-output.json').write_text(json.dumps(base,indent=2))
 provenance.append({'case':dest.name,'source':name,'trial':1,'baseline':b,'baseline_original_sha256':hashlib.sha256(bp.read_bytes()).hexdigest(),'transformations':['neutral case_id','removed machine-specific reproduction command'],'input_hashes':hashes})
comp=out/'comprehension';comp.mkdir(exist_ok=True)
shutil.copyfile(out/'evidence/case-02/receipt.html',comp/'receipt.html')
(out/'facilitator-provenance.json').write_text(json.dumps(provenance,indent=2))
manifest={p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for d in ['evidence','comprehension'] for p in (out/d).rglob('*') if p.is_file()}
(out/'packet-manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({'path':str(out),'files':len(manifest),'all_input_hashes_match':True}))
