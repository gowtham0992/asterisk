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
DOCS += ['app/preparation/README.md','static/reproductions/dermamnist-summary.json','docs/current-readiness.md','docs/readiness-history-2026-09-26.md',
         'docs/design/published-example-2026-09-23.md','docs/design/guided-example-2026-09-23.md']

# The preparation app loads these retained implementations at runtime. Include
# exact code paths, never the surrounding evaluation inputs or result records.
DOCS += ['evaluation/extraction-v1/executor.py',
         'evaluation/extraction-v2/proposal.py',
         'evaluation/extraction-v3/proposal.py',
         'evaluation/extraction-holdout-v1/completion.py',
         'evaluation/extraction-holdout-v1/deadline.py',
         'evaluation/extraction-holdout-v1/worker.py']

# Public support files exercised by the shipped standalone tests and freeze tool.
DOCS += ['evaluation/real-preparation-v1/PROTOCOL.md',
         'evaluation/real-preparation-v1/DECISION.md',
         'research/extraction-observation-review/verify_record.py']

# Current readiness evidence: reviewed prose reports only, never run packets.
DOCS += ['docs/validation/product-finish-audit-2026-09-26.md',
         'docs/validation/frog-trial-followups-2026-09-26.md',
         'research/anuran-user-trial-2026-09-26/REPORT.md',
         'research/preparation-failure-routing/REPORT.md']
DOCS += ['research/identity-choice-preflight/REPORT.md',
         'research/identity-choice-preflight/READER-TASK.md',
         'docs/reviews/external-product-direction-2026-09-26.md']

# Product ladder specs, public derived summaries and fictional examples only.
# Raw datasets, model replies, frozen evaluation cases and run records stay out.
DOCS += ['site/index.html', 'site/site.css', 'site/evidence.json', 'site/.nojekyll']
DOCS += ['public_site/index.html', 'public_site/site.css', 'docs/submission/public-site.md']
DOCS += ['static/ladders/'+name+'.json' for name in (
    'index','experiment','wsibench-report','wsibench-cross-task','ptbxl',
    'esc50-fold1','esc50-fold2','urbansound8k-fold1')]
DOCS += ['static/ladder-example-clean/'+name for name in ('spec.json','split.csv','subjects.csv','README.md')]
DOCS += ['static/ladder-example/'+name for name in ('spec.json','split.csv','subjects.csv','README.md')]
DOCS += ['static/ladder-example-propose/'+name for name in ('train.json','test.json','README.md')]
DOCS += ['examples/ladders/'+name+'.json' for name in (
    'sources','wsibench-report','wsibench-cross-task','ptbxl',
    *('esc50-fold'+str(i) for i in range(1,6)),
    *('urbansound8k-fold'+str(i) for i in range(1,11)))]
DOCS += ['examples/ladders/docs/'+name+'.md' for name in ('esc50','ptbxl','tcga-barcode','urbansound8k')]
DOCS += [str(p.relative_to(ROOT)) for p in (ROOT/'docs/submission').glob('*.md')]
for folder in (ROOT/'evaluation').glob('ladder-proposal-v*'):
    DOCS += [str(p.relative_to(ROOT)) for p in folder.glob('*.md')]

# Reproducible experiment code and prose only, never private packets or replies.
DOCS += ['research/ladder-line-bounds-v6/'+name for name in ('variant.py','study.py','score.py','PROTOCOL.md')]

DOCS += ['research/ladder-messy-v6/'+name for name in ('study.py','PROTOCOL.md')]

# Fresh real-data test utilities only; never its downloaded metadata or records.
DOCS += ['research/ucf101-researcher-trial/'+name for name in ('reference.py','assess.py','PROTOCOL.md','test_reference.py')]

# Research-only comparison utilities, never captured prompts, replies or private inputs.
DOCS += ['research/ladder-source-grammar-v7/'+name for name in ('variant.py','study.py','score.py','test_score.py','PROTOCOL.md')]

# Research-only focused comparison; private packets and model replies excluded.
DOCS += ['research/ladder-focused-v8/'+name for name in ('variant.py','study.py','test_study.py','PROTOCOL.md','REPORT.md')]


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
