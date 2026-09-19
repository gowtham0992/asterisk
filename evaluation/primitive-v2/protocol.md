# Primitive v2 evaluation protocol

Preserve v1 inputs, attempts, source snapshot and results unchanged. The old twelve cases are now **known regression cases**. Their scores cannot establish unseen performance, even when rerun after this fix. A regression experiment has its own immutable snapshot and output directory.

Before selecting, opening or authoring any new acceptance case, freeze and archive the full application source tree, trusted primitive source inventory, engine and primitive versions, system prompt, tool schemas, Sandbox image ID, shared budget implementation and this evaluation protocol. The freeze requires six passing development defect/repair twins on that exact primitive implementation. Changing any frozen source requires a new experiment and newly unseen cases. This protocol requires authorship after the freeze with timestamps, even if the author is independent. Retain the original source URL, immutable revision, license, all transformations and an explicit assertion that the source was not previously used. The assertion records provenance; it is not independently verified by a hash.

Twelve unseen cases: four per category (entity overlap, preprocessing, checkpoint selection), with two violations, one clear and one insufficient case in each category. Include unused permissively licensed drug-response repositories, Yang et al.'s notebook-level labeled evaluation set (private evaluation only, no redistribution), and a planted variant per category. Yang multi-test labels are not checkpoint labels. Each of the six violations has a defect-removed clear twin. Seal inputs, hashes, expected outputs and explicit review obligations before inference. Exact uploaded claims and inputs must have a reviewable inventory; labels are never sent to the agent.

Run Nemotron 3 Super twice on each base case and each twin: 36 attempts. One process holds the existing `.data/probe-pilot/batch.lock` and owns one shared `Budget` using `.data/probe-pilot/budget.json`. At most three in-process workers run. Retain the existing 15-tool-call, 400,000-token-per-attempt ceilings and $10 cumulative estimated token-cost cap. Unknown usage retains its reservation. An attempt is durably marked before executing; crashes and exceptions count as attempted incorrect, never disappear from the denominator, and are never automatically retried. A wholly unstarted case stays unmeasured. Do not overwrite attempts or v1 results.

| Metric | Pass | Fail |
|---|---|---|
| Evidence-gated correct verdicts, each trial | >=10/12 | <8/12 |
| False definitive verdicts on clear/insufficient controls | 0 | Any |
| False clear on a violation in a defect/repair pair | 0 | Any |
| Pairs with violation-to-clear change and replay match in both trials | 6/6 | <6/6 |
| Primitive replay match | 100% | Any mismatch |
| Blind reviewer: unsupported definitive verdicts | <=1 | >=3 |
| Estimated cost per attempt | <$2 | >$5 |
| Observed corrections before submission | Median <=1 | Median >=3 |

Intermediate numeric outcomes are inconclusive. An incorrect automated gate or failed replay is incorrect even when the final label matches. Report the automated-correct **upper bound** separately: each missing or failed independent evidence review can only lower that count. A complete trial with fewer than 8 automated-correct cases is therefore already a failure without a reviewer; incomplete trials also fail when successes plus unstarted slots cannot reach 8. Do not mask proven failure as unmeasured. A pass always requires completed independent review of every frozen `review_requires` obligation, blind evidence ratings and genuinely observed correction counts. Do not synthesize human reviews or practitioner sessions using an LLM.

Replays invoke the baked primitive with recorded arguments on original inputs in a fresh Sandbox. Free-form exploration output is inadmissible. Saved primitive sources and all attempt transcripts remain available for private inspection. The 8 October 2026 fallback remains: if sensitivity has not passed, expose only entity overlap and label code-level categories unsupported. Describe verdicts as gated by trusted measurements, never as verified by the model.
