"""Retain complete probe investigations with a standard-library hash verifier."""
import json,zipfile
from pathlib import Path
from .probes import sha,BOOTSTRAP,validate_files
VERIFY=Path(__file__).with_name('bundle_verifier.py').read_text()


def bundle(result,files,destination):
    validate_files(files)
    contents={'result.json':json.dumps(result,indent=2),'claim.txt':result['claim'],
              'bootstrap.py':BOOTSTRAP,'verify.py':VERIFY,
              'README.txt':'The included verify.py checks bytes against the included unsigned manifest only. Run bundle-supplied code only after reviewing and trusting it. Generated probes must run only inside an isolated environment. For v4 receipts, run the matching project scripts/replay_receipt.py with this extracted directory. Historical probes require their original replay tooling. A hash match and replay do not independently establish scientific correctness. Verdict evidence is limited to trusted_primitives and primitive_measurements in result.json. Fresh replay re-invokes those primitives with recorded arguments on original inputs. Generated probes are exploration only. Use the matching released implementation and baked image; a different implementation fails provenance checks.\n'}
    if result.get('revision_comparison'):contents['comparison.json']=json.dumps(result['revision_comparison'],indent=2)
    if result.get('engine_version')=='primitive-v4':
        contents.pop('bootstrap.py')
        runtime=result.get('runtime_sources') or {}
        if set(runtime)=={'bootstrap.py','primitive_main.py'}:
            for record in result.get('primitive_measurements',{}).values():
                execution=record.get('execution') or {}
                for filename,key in [('bootstrap.py','bootstrap_hash'),('primitive_main.py','driver_sha256')]:
                    if execution.get(key) and execution[key]!=sha(runtime[filename]):
                        raise ValueError('Retained runtime source does not match measurement provenance.')
            contents.update(runtime)
        else:
            contents['README.txt']+='Runtime source was not retained for this historical receipt; no current program has been substituted as the executed program.\n'
        contents['README.txt']+='The primitive implementation hash covers five measurement modules, not the host renderer or this unsigned presentation. Remote replay also re-derives the verdict and checks any recorded confirmation; it cannot authenticate the human actor or scientific meaning.\n'
    if result.get('repair_proposal'):contents['repair-proposal.json']=json.dumps({'proposal':result['repair_proposal'],'approval':result.get('repair_approval')},indent=2)
    from .receipt_view import render_receipt,render_worksheet
    contents['receipt.html']=render_receipt(result,files)
    contents['review.html']=render_worksheet(result)
    contents['README.txt']='Obtain and verify a matching Asterisk release separately from this receipt. From that trusted installation directory (not inside the received bundle), run python -m asterisk verify /absolute/path/to/EXTRACTED_DIRECTORY to check bytes and recompute the entity measurement and verdict locally without credentials. Bundled Python is not executed by that command. A sender can replace the inputs, checker and manifest together; bundle-supplied code is not an independent trust anchor. Open receipt.html in a browser for the offline evidence view. It makes no network requests. The HTML is an unsigned presentation. Neither recomputation nor matching hashes authenticates the author, original dataset or scientific meaning.\n'+contents['README.txt']
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
