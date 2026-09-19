# Asterisk v3 acceptance — failed

18 September 2026. All 36 scheduled attempts completed once, with no case edits, implementation changes, or retries to replace failures. The model received case inputs and claims, not expected labels. This report describes automated agreement; it is not independent human validation.

## Release decision

Use the existing **entity-only fallback** for the local preview. `sh scripts/start_preview.sh` sets `ASTERISK_ENTITY_ONLY=1`; the live configuration endpoint was checked and returned only `entity_overlap`, with Sandbox availability true. This is a scope reduction, not a passing acceptance result. Entity overlap itself missed PTB-XL in both trials. Do not advertise general leakage detection, checkpoint support, an acceptance pass, or measured researcher benefit.

The frozen engine, prompts, gates, cases and scoring code remain unchanged. Checkpoint analysis and all failures remain available for inspection. Do not reopen the analyzer against these exposed cases and call the result unseen acceptance. The existing frozen UI can still show a checkpoint example; the server blocks its execution. This preview is not a finished public launch.

## Results

| Measure | Observed result |
| --- | --- |
| Primary cases, trial 1 | 9/12 automated correct |
| Primary cases, trial 2 | 9/12 automated correct |
| Entity primary cases | 5/6 in each trial |
| Checkpoint primary cases | 4/6 in each trial |
| All primary and twin attempts | 28/36 automated correct |
| Defect–repair pairs | 4/6 pass; PTB-XL and DGL regression fail |
| Primitive replay | 44/44 matching |
| Export bytes | 490 retained manifest entries verified |
| Estimated batch token cost | $0.3142914 |
| Highest estimated attempt cost | $0.0496323 |
| Shared ledger settled total | $6.13009898 |
| Outstanding prior reservations | $0.05083452 |
| Remaining under original $10 cap | $3.8190665 |
| Blind human evidence review | Unmeasured |
| Practitioner comprehension | Unmeasured |
| Matched general-agent baseline | Unmeasured |

Both trials returned the same final verdict for every variant. A pending identity confirmation is not a confirmed clear. No label-disagreeing definitive verdict was observed, but the formal human-reviewed false-definitive metric remains unmeasured. Missing human review is not evidence of a zero error rate. Replay establishes repeatability of the chosen measurement, not correctness of the chosen question.

| Variant | Verdict in both trials | Automated expected result matched? |
| --- | --- | --- |
| E1-ptbxl-random | `insufficient` | No |
| E1-ptbxl-random-twin | `clear_pending_confirmation` | Yes |
| E2-har-window-random | `violation` | Yes |
| E2-har-window-random-twin | `clear_pending_confirmation` | Yes |
| E3-parkinsons-recording-random | `violation` | Yes |
| E3-parkinsons-recording-random-twin | `clear_pending_confirmation` | Yes |
| E4-leaf-plots-control | `clear_pending_confirmation` | Yes |
| E5-ptbxl-coverage-gap | `insufficient` | Yes |
| E6-gait-loader-only | `insufficient` | Yes |
| C1-tgsa-holdout-selection | `violation` | Yes |
| C1-tgsa-holdout-selection-twin | `clear` | Yes |
| C2-dgllife-regression-holdout-selection | `insufficient` | No |
| C2-dgllife-regression-holdout-selection-twin | `insufficient` | No |
| C3-retina-report-selection | `violation` | Yes |
| C3-retina-report-selection-twin | `clear` | Yes |
| C4-dgllife-classification-control | `insufficient` | No |
| C5-tgsa-helper-absent | `insufficient` | Yes |
| C6-scene-runtime-selected-metric | `insufficient` | Yes |

## Failures retained

**E1 PTB-XL, both trials:** the model supplied `sample_column="partition"` rather than `ecg_id`. The primitive correctly rejected repeated partition labels as sample identifiers. The final explanation incorrectly attributed the ambiguity to duplicate ECG identifiers in the data. The supplied ECG keys are unique; a separate CSV join reproduced 623 shared patient IDs and 692 affected evaluation rows. The repaired twin returned pending confirmation. The pair fails because its defect side abstained instead of detecting overlap. This is an argument-binding and explanation failure, not evidence that the original tables have duplicate sample IDs.

**C2 DGL-LifeSci regression, both trials and both variants:** the analyzer returned insufficient, so neither the planted selection defect nor the validation-selection twin met the authored contract. The retained outputs name the missing unambiguous selection chain and include structural candidates. This report does not assert an unverified internal root cause or modify the analyzer to fit the case.

**C4 DGL-LifeSci classification control, both trials:** insufficient rather than the expected scoped clear. This is a capability failure, not a false clear. TGSA and the original retina pair did flip correctly in both trials; those successes do not rescue checkpoint acceptance.

## Input integrity and disclosures

Original ZIP SHA-256: `c4907e667a971cdf2cd54c14ca3d4f1f70f3cd340859f458eeba078493320b85`.
Packet manifest: 68 files verified, zero mismatches. Twelve primary cases and six repaired variants passed preflight. Author timestamps follow the implementation freeze. The original ZIP, separate review, labels, inputs, inventory, attempts, completions and exported evidence are preserved under `.data/primitive-v3/`.

Freeze hash, compact canonical JSON: `2f44ee375bce6db35e2c3bc1ff217b9d4649feb7187fa88a26c897ad29a93e3d`.
Implementation hash: `38976ac98097ebd764bacae6f0283ec802bbe77c5ebedf53a888186b3b9dea5a`.
Nebius image: `c1998ec3-70fe-4589-bdce-c3ce07584aa0`.
Upload inventory hash: `9f2ce736d8ebf743a081f9131c086bf46608d1d744e72c1a9d62ace2ac4d51ad`.
The freeze check passed again after completion.

Fable authored the cases and the review that motivated v3: this is shared authorship, not independence. DGL-LifeSci was new at repository level; TGSA had repository-level exposure. PTB-XL and HAR had dataset-name exposure; UCI174 is distinct from the previous UCI189 but shares the grouping concept. E1/E5, C1/C5, C2/C4 and C3/C6 share sources or structure. These represent at most three to four independent observations per category, not twelve independent studies. Author predictions remain in the sealed record. Planted changes are not claimed as defects discovered in upstream projects.

The packet records CC BY 4.0 for the public datasets, MIT for TGSA and Apache-2.0 for DGL-LifeSci; these are author-supplied provenance disclosures, not a new independent license audit. Payloads comprised the listed identity/partition/label tables, source and synthetic fixtures. No sealed labels were supplied to the model. No upstream project code was executed locally during this intake.

A separate standard-library CSV join reproduced the three overlap counts: PTB-XL 623 shared IDs / 692 affected rows; HAR 30 / 2,059; Parkinsons 27 / 39. It also reproduced zero overlap in the three repaired variants and incomplete coverage in E5. The Parkinsons dictionary says 31 people while the supplied mapping contains 32 distinct speaker IDs. Counts match the supplied mapping; the discrepancy needs human review. No case was changed to resolve it.

## Handoff and remaining work

Local packets are ready under `.data/primitive-v3/acceptance/review-packets/`: `blind-evidence.zip` contains 36 result/input sets and a rating template; `baseline-inputs.zip` contains the same 18 variant inputs and claims without Asterisk outputs or expected labels. Neutral names replace case IDs in the review results. The private label map stays outside both ZIPs. Both packet manifests were verified. Do not give the private map or this report to the blind reviewer before ratings are committed.

These packets have not been sent to anyone. A real independent reviewer must assess the evidence before labels are revealed; a separate practitioner must perform the comprehension task. The matched baseline still needs execution and independent artifact-reproducibility scoring. None can be replaced by an LLM declaring the product successful. The entity-only fallback is active, but its PTB-XL binding failure means it still needs a defensible subsequent validation plan before reliability claims or public launch.

Machine-readable result: `.data/primitive-v3/acceptance/report.json`; preserved final decision: `.data/primitive-v3/release-decision.json`. Provider billing was not independently verified; costs above are ledger estimates.
