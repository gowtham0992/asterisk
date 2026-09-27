# Do not integrate the routing loop

The frozen comparison failed. All 48 scheduled attempts completed once, using 52 inference calls and no Sandbox calls. No prompts, source files, expectations or frozen scoring rules were changed during the run. Production remains unchanged.

| Measure | One corrective request | Router, then optional correction |
| --- | ---: | ---: |
| Exact successful repairs | 7/8 | 3/8 |
| Accepted extractions on controls that required refusal | 4/16 | 1/16 |
| Invalid attempts | 3/24 | 13/24 |
| Calls | 24 | 28 |
| Median attempt seconds | 5.290 | 6.828 |
| Estimated inference USD | 0.0269643 | 0.0344886 |

Total estimated inference cost: $0.0614529, within the $0.5308974 conservative reservation and existing configured caps. Provider billing was not independently checked. An attempt's elapsed time includes all its calls and local routing. The two trials per case are correlated repetitions, not independent datasets.

## What failed

The router often understood the structural issue but changed source paragraph boundaries when quoting it. For example, tree-prefix trial 2 cited a nonexistent second line, splitting a single source line into two. Other quotes reproduced only the first sentence of a line while claiming the whole line. Exact citation validation correctly rejected them; they are not relabeled successes.

More seriously, conflicting-device trial 2 identified the contradictory device assignments, chose `revise_expression`, and its correction replaced the documented observation identifier with row numbers. The deterministic executor accepted this structurally valid extraction even though it violated the fixture's scientific meaning. The baseline made the same change in that trial. It also enabled deduplication despite explicit documentation denying retransmissions, and twice bypassed undefined repeat meaning. These are incorrect accepted *extractions*, not issued scientific receipts: this experimental runner has no confirmation or verdict step and is not integrated in the product.

For space-fields trial 1, the router requested missing evidence even though the source documented the field layout. The actual obstacle was unsupported whitespace parsing. This preserves the original problem: a model may attribute a capability limit to missing scientific evidence.

The router reduced control extractions in this tiny packet but failed both its absolute repair threshold and the required advantage over baseline, and its control error was disqualifying. Do not add it to the application or spend on reruns of this packet to obtain a pass.

## Verification and limitations

`replay.py` reparsed retained completions and recomputed accepted extraction tuples against the frozen source files. Cached correctness/extraction fields are not used. All accepted outputs reproduced locally; reproducibility does not validate a changed observation definition. The source freeze is still valid. Twenty-three offline tests cover routing validation, exact rows, adverse scoring and provider failure without retry.

Control explanations were inspected by the implementation agent and bound to response digests in `.data/preparation-failure-routing/run-1/adjudications.json`. This is developer adjudication, not independent human review. Invalid routes remain invalid and unreviewed. The decision fails without relying on any favorable prose adjudication.

The experiment used full tiny synthetic files and deliberately supplied failed starting proposals, not the production profile-based proposal workflow. Its router prompt appends routing instructions to the application's extraction-language instructions; the result tests this exact interface, not all possible routing designs. Twelve builder-authored fixtures do not support a general model accuracy or production failure-rate estimate. Reference answers were written before inference but the designer knew them. Preserve all earlier failures and the experimental feature label.

## Product implication

Keep explicit observation-identity review. A new automatic correction must not change that binding merely to satisfy the executor. Any future proposal to automate correction needs a separately justified mechanism and fresh cases; this failed run does not authorize weakening citation checks, silently substituting row IDs or treating model refusal as a scientific verdict.

Retained run: `.data/preparation-failure-routing/run-1/`. Fixed payload: `freeze.json`. Scores and usage: `RESULTS.json`. No production source was changed by this experiment.
