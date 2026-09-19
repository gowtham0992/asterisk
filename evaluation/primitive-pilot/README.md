# Primitive acceptance experiment

The primitive engine is implemented. Development fixtures are not unseen acceptance cases. Do not run the 12-case experiment before a valid freeze, and do not describe missing human review as passed.

1. Bake the scientific base with `evaluation/probe-pilot/bake.py`, then bake trusted primitives with `evaluation/primitive-pilot/bake.py`. Both upload code to the configured Nebius project. Never include credentials in a Sandbox payload.
2. Run `evaluation/primitive-pilot/twins.py`. This re-executes six original development defect/repair pairs plus fresh primitive replays. Inspect `.data/primitive-pilot/twins.json`.
3. Run `evaluation/primitive-pilot/freeze.py`. It requires a matching image and six passing development twins, snapshots source/prompt/tool/protocol hashes and timestamp, and refuses overwrite.
4. Author cases after that timestamp. Use `.data/primitive-pilot/cases/manifest.json`, with input files alongside it. Do not copy the known pilot or development twins. Record source family (`yang`, `drug_response`, `planted`), URL, immutable revision, license, transformations, author, timestamp, expected verdict, metrics, and explicit `review_requires`. Each category requires two violations, one clean and one insufficient case, including a planted variant. Every violation requires a separate repaired twin.
5. Inspect the exact case upload inventory and authorize it before invoking `run.py PATH --confirm-upload`. The runner seals the manifest, checks original input hashes and current engine hashes, runs Super twice on each case and twin, and shares the existing cumulative $10 estimated ledger. Saved attempts are never overwritten or silently retried.
6. Supply independent human adjudications using `--report-only --review FILE`. `runs` maps `CASE-trialN` to `{"requirements":{"exact frozen review requirement":true}}`. Top-level `unsupported_definitives` and `corrections` contain the blind review count and actual observed correction counts. No LLM-generated human ratings.

Manifest shape (metadata placeholder, not an authored case):

```json
{
  "freeze_hash": "SHA256 of sorted-key JSON serialization of freeze.json",
  "cases": [{
    "id": "unique-case-id", "category": "preprocessing", "claim": "case claim",
    "author": "case author", "authored_at": "ISO8601 timestamp after freeze",
    "source": {"family":"yang", "url":"source URL", "revision":"immutable commit", "license":"private evaluation; not redistributed", "transformations":"document every change"},
    "directory": "case directory relative to manifest", "input_hashes": {"entry.py":"SHA256"},
    "expected": {"verdict":"violation", "metrics":{}, "review_requires":["precise evidence obligation"]},
    "twin": {"directory":"repair directory", "input_hashes":{"entry.py":"SHA256"}, "expected":{"verdict":"clear", "review_requires":["precise repair obligation"]}}
  }]
}
```

The Yang reference is [Data Leakage in Notebooks: Static Detection and Better Processes](https://arxiv.org/abs/2209.03345). The authors' [tool README](https://github.com/malusamayo/leakage-analysis) links to the separate [evaluation materials](https://github.com/malusamayo/GitHubAPI-Crawler/tree/master/evaluation_materials). User-supplied provenance reports 100 notebook-level labels; ZIP coverage and source-specific rights must be checked after the freeze. The MIT tool license does not establish rights to the crawler labels/notebooks. Keep these materials out of public archives. The multi-test labels do not establish checkpoint-selection ground truth.

Known pilot records remain under `evaluation/probe-pilot`. Their prior 8/10 and 9/10 label agreement is not primitive-gated accuracy. Their saved verdicts lack primitive measurements and therefore score zero admissible verdicts under the new contract. This is rescoring old records, not a fresh model run or a measured estimate of new-engine accuracy.
