"""Build a local walkthrough from exposed PTB-XL development records; no provider calls."""
import json,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from app.receipt_view import render_receipt,render_worksheet,esc
from app.receipt_comparison import compare_receipts

def read(path):
    result=json.loads((path/'result.json').read_text())
    files={p.relative_to(path/'inputs').as_posix():p.read_text() for p in (path/'inputs').rglob('*') if p.is_file()}
    return {'input':{'claim':result.get('original_claim') or result['claim'],'files':[{'name':n,'content':v} for n,v in files.items()]},'result':result},files


def build():
    before,files=read(ROOT/'.data/primitive-v4/ptbxl-known-smoke/evidence')
    after,twin=read(ROOT/'.data/primitive-v3/acceptance/runs/E1-ptbxl-random-twin-trial2/evidence')
    comparison=compare_receipts(before,after)
    if not comparison['available']:raise SystemExit(comparison['reason'])
    manifest=json.loads((ROOT/'.data/primitive-v3/authored-packet/acceptance-cases/manifest.json').read_text())
    case=next(c for c in manifest['cases'] if c['id']=='E1-ptbxl-random')
    for fs,expected in [(files,case['input_hashes']),(twin,case['twin']['input_hashes'])]:
        if {n:hashlib.sha256(v.encode()).hexdigest() for n,v in fs.items()}!=expected:raise SystemExit('Authored case bytes changed.')
    out=ROOT/'.data/product-walkthrough';out.mkdir(exist_ok=True)
    (out/'before.html').write_text(render_receipt(before['result'],files));(out/'after.html').write_text(render_receipt(after['result'],twin))
    (out/'review.html').write_text(render_worksheet(before['result']))
    (out/'comparison.json').write_text(json.dumps(comparison,indent=2))
    report={'source':case['source'],'case':case['id'],'comparison':comparison,
            'disclosure':'Exposed, LLM-authored development case. Record-level random split planted by the case author, not a defect discovered in PTB-XL. Twin uses a group-respecting partition. Existing remote records retained; this script performs local input comparison only. Before uses v4, after retains its original v3 pending-confirmation verdict. No new acceptance, human validation or accuracy experiment.'}
    (out/'provenance.json').write_text(json.dumps(report,indent=2))
    summary={k:v for k,v in comparison.items() if not isinstance(v,list)}
    summary.update({k:len(v) for k,v in comparison.items() if isinstance(v,list)})
    (out/'summary.json').write_text(json.dumps(summary,indent=2))
    css=(ROOT/'static/receipt.css').read_text()
    page='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>PTB-XL split walkthrough</title><style>'+css+'</style><main><p class="eyebrow">ASTERISK / EXPOSED DEVELOPMENT WALKTHROUGH</p><h1>Different recordings.<br>The same people.</h1><p>'+esc(report['disclosure'])+'</p><section><h2>What changed</h2><p>Original: '+str(comparison['before']['shared_identities'])+' shared patient IDs affecting '+str(comparison['before']['affected_evaluation_rows'])+' evaluation recordings. Revised: '+str(comparison['after']['shared_identities'])+' shared IDs.</p><p>'+str(len(comparison['partition_moves']))+' recordings changed partition. '+str(len(comparison['samples_added']))+' added; '+str(len(comparison['samples_removed']))+' removed.</p><p>The revised result remains conditional on the identity interpretation. No accuracy effect is measured.</p><p><a href="before.html">Inspect original receipt</a> · <a href="after.html">Inspect revised receipt</a> · <a href="comparison.json">All row changes</a> · <a href="review.html">Reviewer worksheet</a></p></section><section><h2>Source and construction</h2><p>'+esc(case['source']['transformations'])+'</p><p>PTB-XL v1.0.3 · CC BY 4.0. Wagner et al. (2022), PTB-XL v1.0.3, PhysioNet, doi:10.13026/kfzx-aw45. Original publication: Wagner et al. (2020), Scientific Data, doi:10.1038/s41597-020-0495-6. PhysioNet: Pollard et al. (2026), Nature Health, doi:10.1038/s44360-026-00096-z. Source: <a href="https://physionet.org/content/ptb-xl/1.0.3/">PhysioNet</a>.</p><p>Only identity and partition metadata. No diagnoses, signals or demographics. Full provenance: <a href="provenance.json">provenance.json</a>.</p></section></main></html>'
    (out/'index.html').write_text(page)
    print(json.dumps({'output':str(out),'summary':summary},indent=2))
if __name__=='__main__':build()
