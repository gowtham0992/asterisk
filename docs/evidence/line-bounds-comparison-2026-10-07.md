# Fresh preparation comparison — 7 October 2026

Keep the shipping v4 prompt. The bounds-only v6 candidate is promising on this small comparison but did not meet the exact precommitted promotion rule. Its implementation is retained only in the research harness; it is not selectable in the product and was not deployed.

## Observed results

Eight cases, each attempted twice per arm, using the same Nemotron 3 Super model and one permitted validator repair. These are 16 attempts per arm, not 16 independent datasets or trials.

| Measure | Shipping v4 | Bounds-only v6 |
|---|---:|---:|
| Correct attempts | 13/16 | 16/16 |
| Cases correct in both attempts | 6/8 | 8/8 |
| Unsupported bindings on abstention controls | 1 | 0 |
| False pending-clear results on supported cases | 0 | 0 |
| Invalid first replies | 2 | 0 |
| Observed citation-beyond-file errors | 0 | 0 |
| Provider calls, including repairs | 18 | 16 |
| Reported tokens | 77,583 | 46,699 |

V4 failed to produce valid JSON for the long fictional join document in both attempts. It also proposed an identity binding once when the documentation explicitly denied that meaning. V6 passed those controls in both attempts. No human confirmation occurred. No Sandbox calls occurred. Judge allowance was not used. The conservative token-cost estimate in the separate $2 research ledger settled at $0.186423 with no outstanding reservations; this is not an invoice or verified provider charge.

The promotion rule required all supported cases correct in both attempts, no unsupported or false-reassuring proposals, at least two additional correct attempts, fewer invalid first replies **and fewer citation-bound errors**. The last condition was not satisfied: both arms had zero observed citation-bound errors. We did not relax the rule after seeing results. This is an inconclusive test of the citation-error hypothesis, despite the better preparation point estimate. No repeated batch was substituted.

## What the cases actually contain

- **AT&T ORL:** 400 relative filenames read from the original archive ZIP listing. Image bytes were neither retained nor sent. Two researcher-authored splits test subject-directory parsing; a third case withholds the directory meaning and expects abstention. These are real filenames with authored splits, not a newly discovered flaw in an official benchmark split. Both arms passed all three cases in both attempts. [AT&T archive documentation](https://www.cl.cam.ac.uk/research/dtg/attarchive/facedatabase.html).
- **UCI Pendigits:** published row counts, local filename-plus-row sample identifiers and documentation. No coordinates, class values or writer mapping. Both arms abstained correctly in both the missing-mapping and per-row-uniqueness variants. This proves behavior on the supplied projection, not that writer mappings are absent from every published representation. [UCI dataset](https://archive.ics.uci.edu/dataset/81/pen+based+recognition+of+handwritten+digits).
- **Three fictional controls:** a documented cross-file specimen join, its definition late in a long document, and an explicit denial of the specimen binding. These were builder-authored before the model calls, as were all case references.

The candidate kept v4's documentation arrays, grammar, judgment rules and worked example. It added document line-count metadata and citation-bound instructions only. It did not force a ladder when evidence was missing or change the measurement engine.

## Corrections and limits

The initial online scorer incorrectly compared entire population records, including citation ranges and specification hashes. It provisionally marked some equivalent proposals incorrect and as false reassurance. That was a scorer defect, not an observed model safety failure. The offline scorer now compares subject grouping, sample-to-partition mapping and finding status; a regression test accepts changed valid citation ranges and rejects swapped partitions. Original records and provisional scores remain retained. Cases, references, model requests and pass criteria were unchanged. This correction used no extra model calls.

The failed terminal JSON attempts retain usage and error records but not their full raw replies. Their underlying generation mechanism cannot be diagnosed from those records, and their citation-error status is unknown beyond the recorded validation error. This limits the claim about citation errors further; it cannot justify promotion.

This is a small builder-authored comparison: two real datasets with correlated variants and three original controls. It is neither independently authored acceptance nor human usefulness evidence. The previous 5/10 shipping set-D result remains published. The new unsupported binding means historical language such as “misses were always abstentions” must remain confined to its historical evaluation; it is not a property of the product.

Experimental source: research/ladder-line-bounds-v6/{variant.py,study.py,score.py,PROTOCOL.md}. Private packet, references, replies, archive hashes and ledger: .data/line-bounds-v6-20261007; excluded from source releases. Tests: the experimental build passed 610 Python tests with 9 existing skips; after withdrawing it from application code, 29 focused shipping-proposer and research regression tests passed. The isolated research wrapper reproduces every frozen request byte for byte, while the product default remains v4. The deployed app remains release 1d55a9a.
