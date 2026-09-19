"""Freeze before case authoring; never overwrite an earlier experiment identity."""
import json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from app.probes import SYSTEM,TOOLS,ENGINE_VERSION,sha
from app.primitive_runtime import implementation_hash
from app.primitives import VERSION
TRACKED=['app/probes.py','app/primitives.py','app/fit_trace.py','app/audit.py','app/primitive_runtime.py','evaluation/primitive-pilot/protocol.md','evaluation/primitive-pilot/scoring.py','evaluation/primitive-pilot/run.py','evaluation/primitive-pilot/freeze.py']
def fingerprint(root=ROOT):
    return {name:sha((root/name).read_text()) for name in TRACKED}
def check(frozen,root=ROOT):
    if frozen['files']!=fingerprint(root):raise ValueError('Frozen implementation changed. Start a new experiment with newly unseen cases.')
    if frozen['implementation_hash']!=implementation_hash():raise ValueError('Primitive implementation changed.')
    if frozen['prompt_hash']!=sha(SYSTEM) or frozen['tools_hash']!=sha(json.dumps(TOOLS,sort_keys=True)):raise ValueError('Frozen prompt/tools changed.')
def main():
    data=ROOT/'.data/primitive-pilot';env=json.loads((data/'environment.json').read_text());twins=json.loads((data/'twins.json').read_text())
    digest=implementation_hash()
    if env['implementation_hash']!=digest or twins['implementation_hash']!=digest or not twins['passed'] or len(twins['pairs'])!=6 or not all(p['passed'] for p in twins['pairs']):raise SystemExit('Bake and pass all six development twins on the current implementation before freezing.')
    result={'frozen_at':datetime.now(timezone.utc).isoformat(),'engine_version':ENGINE_VERSION,'primitive_version':VERSION,'implementation_hash':digest,'image':env['image'],'files':fingerprint(),'prompt_hash':sha(SYSTEM),'tools_hash':sha(json.dumps(TOOLS,sort_keys=True)),'development_twins_hash':sha((data/'twins.json').read_text()),'model':'nvidia/nemotron-3-super-120b-a12b','trials':[1,2]}
    with (data/'freeze.json').open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
