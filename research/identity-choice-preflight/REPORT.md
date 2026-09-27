# Identity-choice preflight: ESC-50

26 September 2026. Developer investigation: initial offline preflight, followed by the two-call development test below. No Sandbox calls, audio downloads or public redistribution. This is development evidence, not part of a frozen acceptance set.

## Finding and fix

The application omitted documentation after line 100 from its model request. In the pinned ESC-50 README, the original-clip identifier and fragment-letter definitions occur on lines 141–142. Both were absent from the approved payload even though the full document fits the existing request bound. The source was retained locally; this was an inference-context omission, not source loss.

The application request now includes every physical line of recognized documentation when the complete request fits its existing 100 KB bound. Larger documentation is rejected before inference, rather than truncated. The preview, consent hash, retained request and cost reservation all cover the complete request. Historical evaluation profile code remains unchanged. This does not promise that a model will interpret the evidence correctly.

Regression: two late-definition tests failed before the fix and passed after. The focused documentation, proposal, runtime and prompt-contract suites passed **33 tests**, with three existing deprecation warnings. Both implicit Markdown detection and explicit documentation selection are covered, including exact approved-message dispatch and oversized-document rejection. No running-server restart or browser verification is claimed for this change.

The real-file reproduction changed from 100/208 README lines to 208/208, with neither identity-definition line omitted. The complete preview occupies 45,551 bytes under the script's JSON serialization (previously 31,801).

## Why this dataset helps test the product bet

Source: [ESC-50 official repository](https://github.com/karolpiczak/ESC-50), commit `33c8ce9eb2cf0b1c2f8bcf322eb349b6be34dbb6`. The original metadata CSV has 2,000 rows and seven columns; all seven were retained. The upstream README describes source-group-respecting folds and labels the full dataset CC BY-NC 3.0, with ESC-10 under CC BY. Keep downloaded material private in this development preflight; this does not authorize a public dataset bundle.

The independent CSV calculation imports no Asterisk measurement code. The same script separately invokes the actual application request builder to inspect what the model would receive.

| Binding | Published fold 1 vs folds 2–5: shared values / affected test rows | Authored random 400-row holdout: shared values / affected test rows |
|---|---:|---:|
| filename | 0 / 0 | 0 / 0 |
| src_file | 0 / 0 | 121 / 134 |
| target | 50 / 400 | 50 / 400 |
| take | 8 / 400 | 7 / 400 |

The random holdout uses seed 20260926 and is our constructed variant, not a published leakage finding. Category labels and fragment letters can repeat without identifying a shared original recording. Unique filenames can conceal shared source recordings. Neither the most repeated nor least repeated column determines the scientific unit.

This dataset is now exposed during development and cannot be presented as an untouched held-out acceptance case. The six-task, three-domain comparison remains unassembled and unrun; this preflight does not replace it.

## Two live development calls

After the documentation fix, `live_esc50.py prepare` saved both complete inputs, application payloads, source hashes and reference answers before `run` dispatched either request. All seven CSV columns were retained. File membership defined the two partitions; an added three-line experiment document explained that role without naming the entity column. The original fold field was retained even in the constructed random partition. No expected answer was sent to the model.

Both calls used the actual `ProposalRequest` and the existing budgeted Nebius adapter with `nvidia/nemotron-3-super-120b-a12b`. Exactly two calls completed, with no correction or retry. Estimated inference cost: **$0.0107262**; provider billing is not independently verified. No Sandbox measurement or receipt was created. Extraction and counts were checked locally; both proposals remained review-required.

| Case | Chosen sample / entity | Locally recomputed shared IDs / affected rows | Evidence citation |
|---|---|---:|---|
| Published fold 1 | filename / src_file | 0 / 0 | README 147–156: table schema, not the identity definition; experiment line 3 gives the claim but not file roles |
| Authored random 400 | filename / src_file | 121 / 134 | README 136–143 includes the original-clip definition; experiment 1–3 includes file roles |

All 1,600 training and 400 evaluation rows were preserved in each case. The model did not choose the unique observation ID or the repeated category label as the entity.

**Decision: the full precommitted evidence requirement failed.** Correct bindings and counts in both calls do not excuse the missing definition citation in the published-fold response. This is not a false production clear: neither proposal was confirmed or turned into a verdict. It is a review-quality failure that matters to the proposed product advantage.

Even the stronger random-case citation defines CLIP_ID in the filename rather than explicitly defining the CSV field src_file. A separate developer check found that the filename's CLIP_ID equals src_file on all 2,000 rows. That check strengthens the interpretation but was not part of the model's submitted evidence and must not be credited to it.

The next design implication is specific: a comparison interface needs to expose the evidence connecting a candidate field to its claimed meaning. Merely listing multiple overlap counts is insufficient. No automatic semantic approval or more correction calls were added as a response to this failure.

Raw protocol, packet, requests, responses, measurements and developer adjudication are retained in `.data/identity-choice-preflight/esc50-live/`. Re-running `run` is refused once `started.json` exists. This is not a general-agent comparison, independent evaluation or evidence of researcher time savings.

## Reproduction

From the project root, run `.venv/bin/python research/identity-choice-preflight/esc50.py` after obtaining the three files listed in `.data/identity-choice-preflight/esc50/provenance.json`. The script checks upstream hashes, recomputes comparisons and inspects a fresh application payload. No credentials are read and no network call occurs in the script.

Raw downloads, provenance and latest computed output are under `.data/identity-choice-preflight/esc50/`; they are not part of the public source package.
