# Fresh messy-file preparation comparison — 7 October 2026

**Keep shipping v4. Do not promote the bounds-only v6 candidate.** The earlier candidate advantage did not repeat. No app, model-default, measurement or confirmation behavior changed; the hosted release remains 1d55a9a.

| Corrected-run measure | Shipping v4 | Candidate v6 |
|---|---:|---:|
| Correct attempts | 16/16 | 15/16 |
| Unsupported bindings on abstention controls | 0 | 0 |
| Wrong pending-clear results | 0 | 0 |
| Rejected-call corrections | 1 | 1 |
| Structural citation-review flags | 3 | 8 |
| Provider calls, including repairs | 17 | 17 |
| Reported tokens | 57,661 | 56,054 |

Eight correlated cases, each attempted twice per arm; these are sixteen attempts per prompt, not sixteen independent datasets. The candidate failed a supported fictional contrast case that v4 passed. Its abstention requested documentation that specimen IDs did not overlap between training and evaluation. That is the answer the application should measure, not an input needed to choose the identity binding. In the second attempt it handled that same case correctly. This is an observed regression, not proof that the line-count metadata caused it.

The promotion rule was fixed before the corrected run: at least 14/16, at least two more correct attempts than v4, all abstention controls correct, no wrong pending clear, no paired regression against a correct baseline response, and no larger total of rejected-call corrections plus structural review flags. The candidate failed the advantage, paired-regression and correction/flag conditions. No favorable reruns or changed thresholds replaced that result.

Structural review flags count required field references missing from supplied citations. They do not establish semantic correctness or the number of edits a person would actually make. No humans participated, and neither preparation time saved nor researcher demand was measured.

## Inputs and scope

- **UCI Multiple Features:** original archive hashes, six 2,000-row feature files and documentation stating cross-file correspondence to the same original digit character. The test retained only file names/row counts, authored identifiers `<feature-file>:<original-row-number>`, and authored splits. Cross-view separation shares 2,000 original patterns; grouping original rows across the split shares none. A separate writer question correctly abstains without writer identity. These are authored projections, not a claim of leakage in a published benchmark split. Both prompts passed all three cases in both attempts. [UCI source, R. Duin, CC BY 4.0](https://archive.ics.uci.edu/dataset/72/multiple+features).
- **UCI Libras Movement:** 360 published rows projected to sample IDs and an authored assignment; no signer mapping, coordinates or movement-class values. Both prompts correctly abstained on signer independence. This is about the supplied projection, not every available representation. [UCI source, Dias, Peres and Bscaro, CC BY 4.0](https://archive.ics.uci.edu/dataset/181/libras+movement).
- **Four fictional microscopy fixtures:** join, split and identity definitions in separate documents; definitions late among blank maintenance-log lines; current meanings distinguished from misleading old interpretations; an explicit denial of specimen identity.

Prompts and payload rules were unchanged from the previous comparison. References were not transmitted to the model. Only documentation, column profiles and the approved identifier examples went to Nebius. No feature vectors, movement coordinates, images, personal fields, Sandbox uploads or judge allowance were used.

## Builder error, interruption and exposure

My initial case builder had an indentation error and froze only five cases instead of the intended eight. The scorer's self-test caught an impossible pass condition, but inference had already started. I stopped that batch and retained it as invalid-pilot rather than hiding or scoring it. A case-count assertion and all three scorer tests then passed before starting the corrected 32-proposal run. The invalid pilot is excluded from every table above. Its five overlapping cases are disclosed; this corrected test is not entirely unexposed. Neither prompts nor the overlapping references were tuned to pilot responses. New source inventories, protocols, hashes and raw corrected-run replies are retained separately.

The initial interruption may have lost raw responses; their cost reservations remain conservatively retained in the pilot ledger and were carried into the corrected run's $2 research cap. The cumulative conservative estimate is $0.1904835, including that carried charge. It is not a provider invoice. Corrected-run responses, including terminal invalid outputs, are retained by the improved research runner. No provider-error retries were performed.

Authorship is shared with the implementation; cases are correlated and independently authored acceptance is not claimed. The historical shipping 5/10 result remains valid for its own set. The previous bounds-only comparison's 16/16 versus 13/16 remains recorded, alongside its failed promotion gate. The new result is counterevidence to generalizing that improvement.

Code and prospective rule: research/ladder-messy-v6/{study.py,PROTOCOL.md}. Private packet, archive inventories, source hashes, exact requests, raw replies, pilot and ledger: .data/ladder-messy-v6-20261007; excluded from source releases. The scorer tests accept equivalent citations, reject inverted partitions, reject all-abstain behavior and ties, and enforce paired regressions. They passed before the corrected run. Application source and shipping tests were not changed, so this adds no new product-test count.
