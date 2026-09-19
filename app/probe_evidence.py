"""Retain complete probe investigations with a standard-library hash verifier."""
import json,zipfile
from pathlib import Path
from .probes import sha,BOOTSTRAP,validate_files
VERIFY='''"""Verify bytes only. This does not execute generated probes or certify their meaning."""
import hashlib,json,pathlib,sys
root=pathlib.Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_text())
for name,digest in manifest['files'].items():
    p=(root/name).resolve()
    if not p.is_relative_to(root) or not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:
        raise SystemExit('FAILED: '+name)
print('PASS: all manifest bytes match. Semantic correctness and provenance authenticity are not established by hashes.')
'''

def bundle(result,files,destination):
    validate_files(files)
    contents={'result.json':json.dumps(result,indent=2),'claim.txt':result['claim'],
              'bootstrap.py':BOOTSTRAP,'verify.py':VERIFY,
              'README.txt':'Run python verify.py to check retained bytes. Generated probes must run only inside an isolated environment. For v4 receipts, run the matching project scripts/replay_receipt.py with this extracted directory. Historical probes require their original replay tooling. A hash match and replay do not independently establish scientific correctness. Verdict evidence is limited to trusted_primitives and primitive_measurements in result.json. Fresh replay re-invokes those primitives with recorded arguments on original inputs. Generated probes are exploration only. Use the matching released implementation and baked image; a different implementation fails provenance checks.\n'}
    if result.get('revision_comparison'):contents['comparison.json']=json.dumps(result['revision_comparison'],indent=2)
    if result.get('repair_proposal'):contents['repair-proposal.json']=json.dumps({'proposal':result['repair_proposal'],'approval':result.get('repair_approval')},indent=2)
    from .receipt_view import render_receipt,render_worksheet
    contents['receipt.html']=render_receipt(result,files)
    contents['review.html']=render_worksheet(result)
    contents['README.txt']='Open receipt.html in a browser for the offline evidence view. It makes no network requests. The HTML is an unsigned presentation; run verify.py to check bundle bytes.\n'+contents['README.txt']
    contents.update({'inputs/'+n:v for n,v in files.items()})
    contents.update({'trusted_primitives/'+n:v for n,v in result.get('primitive_sources',{}).items()})
    contents.update({'probes/'+n+'.py':v for n,v in result['probes'].items()})
    contents['manifest.json']=json.dumps({'version':1,'files':{n:sha(v) for n,v in contents.items()}},indent=2)
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=False)
    for n,v in contents.items():
        p=destination/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(v)
    with zipfile.ZipFile(destination.with_suffix('.zip'),'w',zipfile.ZIP_DEFLATED) as z:
        for n in contents:z.write(destination/n,n)
    return destination
