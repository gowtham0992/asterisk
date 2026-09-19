"""Create a private, blinded evidence packet. Does not invent reviewer ratings."""
import hashlib,json,random,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'.data/primitive-pilot'
def main():
    manifest=json.loads((DATA/'cases-sealed.json').read_text());runs=DATA/'runs'
    items=[]
    for c in manifest['cases']:
        for trial in (1,2):
            items.append((f'{c["id"]}-trial{trial}',c))
            if 'twin' in c:items.append((f'{c["id"]}-twin-trial{trial}',{**c,**c['twin']}))
    random.Random(98173).shuffle(items)
    packet=DATA/'private-review-packet';packet.mkdir(exist_ok=False);key={};ratings={};requirements={}
    for index,(name,c) in enumerate(items,1):
        p=runs/name/'result.json'
        if not p.exists():continue
        r=json.loads(p.read_text());alias=f'evidence-{index:02}';key[alias]=name;out=packet/alias;out.mkdir()
        # No expected labels, trial/model identifiers, or automated pass/fail labels.
        evidence={k:r.get(k) for k in ('claim','verdict','primitive_measurements','primitive_replays','input_hashes','primitive_sources')}
        (out/'evidence.json').write_text(json.dumps(evidence,indent=2))
        shutil.copytree(runs/name/'inputs',out/'inputs')
        ratings[alias]={'unsupported_definitive':None,'corrections_before_submission':None,'notes':''}
        requirements[alias]={req:None for req in c['expected']['review_requires']}
    (packet/'ratings.json').write_text(json.dumps(ratings,indent=2))
    (DATA/'review-blinding-key.json').write_text(json.dumps(key,indent=2))
    (DATA/'review-requirements-stage2.json').write_text(json.dumps(requirements,indent=2))
    (packet/'README.txt').write_text('Private independent review. Do not redistribute the research inputs. For each anonymous record, inspect the original inputs, selected arguments, measurements and cited source. Decide whether the evidence establishes the stated scoped verdict. Explain unsupported definitive verdicts. Commit these blind ratings first. Only afterward should the evaluator disclose review-requirements-stage2.json for explicit true/false adjudication of the frozen evidence obligations; these may reveal expected conditions and are withheld from the blind stage. Null means unmeasured. Record corrections only when actually observed with a practitioner; do not infer them from tool errors. The case author must not supply the independent ratings. The separate blinding key must stay with the evaluator until ratings are complete.\n')
    print(f'Prepared {len(ratings)} anonymous records at {packet}. No ratings supplied.')
if __name__=='__main__':main()
