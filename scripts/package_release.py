"""Create an allowlisted source release; never include credentials or research inputs."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1]
TOP=['asterisk.py','README.md','LICENSE','.env.example','.gitignore','requirements.txt','requirements.lock.txt','requirements-sandbox.txt']
TREES=['app','static','tests','scripts']
DOCS=['evaluation/run.py','evaluation/cases.json','evaluation/README.md','evaluation/probe-pilot/budget.py','docs/architecture.md','docs/verification.md','docs/release.md','docs/demo-script.md','evaluation/probe-pilot/common.py','evaluation/probe-pilot/bake.py','evaluation/probe-pilot/replay.py','evaluation/probe-pilot/comprehension.md'] + ['evaluation/primitive-pilot/'+n for n in ('bake.py','freeze.py','run.py','scoring.py','protocol.md','README.md','twins.py','smoke.py','review_packet.py','REPORT.md')]

DOCS += ['evaluation/primitive-v2/' + name for name in (
    'README.md', 'protocol.md', 'v2harness.py', 'v2scoring.py', 'inventory.py',
    'bake.py', 'twins.py', 'freeze.py', 'run.py', 'REPORT.md')]
DOCS += ['evaluation/primitive-v3/'+p.name for p in (ROOT/'evaluation/primitive-v3').glob('*') if p.is_file() and p.suffix in {'.py','.md'}]
DOCS += ['docs/validation/researcher-study.md','docs/validation/automated-review-2026-09-18.md','docs/design/evidence-report.md']
DOCS += ['docs/repair-and-reuse-verification.md','docs/notebook-and-repair.md','docs/experiments/score-protocol.md','docs/experiments/score-results.md']
DOCS += ['docs/experiments/size-control-protocol.md','docs/reviews/fable-final-response.md','docs/validation/recruitment-kit.md']
DOCS += ['docs/build-readiness.md','evaluation/probe-pilot/protocol.md']
DOCS += ['evaluation/primitive-v4/'+p.name for p in (ROOT/'evaluation/primitive-v4').glob('*') if p.is_file() and p.suffix in {'.py','.md'}]
DOCS += ['docs/reviews/v3-acceptance-results.md','docs/reviews/v4-implementation.md','devpost-submission.md','docs/validation/reviewer-a.md','docs/validation/reviewer-b.md','docs/validation/ratings-template.json']

DOCS += ['docs/reviews/rc7-verification-wording.md','docs/reviews/rc6-self-review.md','docs/reviews/rc4-receipt-scope.md','docs/reviews/rc5-runtime-provenance.md']

DOCS += ['docs/validation/binding-recovery-and-newlines.md','docs/validation/live-binding-rc3.md','docs/comparison-contract-v2.md']

# Explicit public aggregates only; never admit arbitrary JSON trees.
DOCS += ['static/reproductions/dermamnist-summary.json','docs/current-readiness.md',
         'docs/design/published-example-2026-09-23.md','docs/design/guided-example-2026-09-23.md']

def release_files(root):
    paths=[root/n for n in TOP+DOCS if (root/n).is_file()]
    for tree in TREES:
        paths.extend(p for p in (root/tree).rglob('*') if p.is_file() and not p.is_symlink() and '__pycache__' not in p.parts and p.suffix in {'.py','.js','.mjs','.css','.html','.svg','.png','.webp','.sh'})
    return sorted(set(paths))

def package(root=ROOT):
    out=root/'artifacts';out.mkdir(exist_ok=True)
    target=out/'asterisk-source.zip';manifest={}
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for p in release_files(root):
            name=p.relative_to(root).as_posix();data=p.read_bytes()
            if p.is_symlink():raise ValueError('Symlink in release')
            z.writestr('asterisk/'+name,data);manifest[name]=hashlib.sha256(data).hexdigest()
        z.writestr('asterisk/RELEASE-MANIFEST.json',json.dumps(manifest,indent=2))
    print(f'{target}: {len(manifest)} files; secrets, local databases and third-party research datasets excluded')
    return target
if __name__=='__main__':package()
