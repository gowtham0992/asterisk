# Focused preparation v8 — reject promotion

9 October 2026. The full fixed batch completed without provider failures. This is implementer-authored development evidence on twelve original fictional cases, not held-out accuracy or human usefulness evidence.

| Metric | Shipping v4 | Research v8 |
|---|---:|---:|
| First-call semantic correctness | 19/24 | 22/24 |
| Final semantic correctness | 21/24 | 22/24 |
| Provider calls | 27 | 25 |
| Returned total tokens | 75,601 | 72,675 |
| Missing/denying/unsupported/unknown-partition controls correctly abstained | 8/8 | 8/8 |

**Decision: keep v4.** v8 did not achieve all 24 correct and had a paired final regression on the per-sample-ID trap. An improvement of one final answer is insufficient under the frozen gate. Historical 5/10 retained results remain unchanged.

## Failures retained

- First v8 namespaced-line trial: duplicate JSON keys, followed by duplicate keys in the one permitted repair. Both provider responses finished with `stop`; this was not token-limit exhaustion.
- Second v8 per-sample-ID-trap trial: it abstained, asking for proof that animals were assigned exclusively to train or evaluation. That is the condition being tested, not required evidence for defining the recorded animal identifier. The existing prompt answered correctly. This is a model reasoning failure, not a missing input.
- Both v4 namespaced-line trials abstained despite the supported documented filename convention. First v4 per-source override trial also failed; two qualified-night replies needed validation repair.

The independent per-row reference maps were written before inference. Scoring follows original observation rows through source lineage, permitting a valid renamed sample key, and compares complete unit grouping plus partitions, including excluded rows. Matching an overlap headline alone is insufficient. Four scorer tests verify complete grouping, abstention controls, incomplete-run rejection, paired regressions and a minimum improvement requirement.

## Cost and provenance

48 proposals and 52 calls; no post-result retries. All inputs were original fictional identifier tables and documentation. No personal fields, real research data, Sandbox calls, or hosted judge allowance were used. Exact requests, raw replies, finish reasons, token details, inputs, references and implementation hashes remain private in `.data/ladder-focused-v8-20261009/` and are excluded from releases. The conservative estimate is $1.48276 using $10/million for all returned tokens, under the fixed $3 cap; this is not a provider bill. No reservations are uncertain.

A preflight-only packet was replaced to make scoring independent of a valid sample-key renaming and to add scorer tests, before any inference. Both preflight files remain retained. Frozen thresholds, cases and references were not edited after inference.

## Consequence

Do not present this candidate as a fix for preparation reliability. It remains research-only. The smaller-output approach improved some development results and failed others. Another prompt tweak on these cases cannot establish fresh accuracy. Scientific interpretation continues to require explicit review; neither a valid JSON object nor a successful replay establishes it.
