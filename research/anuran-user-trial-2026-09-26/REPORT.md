# Asterisk researcher trial: frog-call bioacoustics

26 September 2026. Completed against the running local product on port 8782. No product or prompt changes were made for this trial.

Asterisk completed a new-domain browser workflow with a live Nemotron proposal, full-table Nebius Sandbox measurement, fresh Sandbox replay and locally recomputed evidence. It caught a researcher-created syllable split that cannot support an unseen-recording claim. A recording-group control returned zero overlap, with human confirmation correctly still pending.

## Research question and provenance

Could a species classifier evaluated on held-out call syllables claim to generalize to frogs absent from training?

Source: [UCI Anuran Calls (MFCCs), dataset 406](https://archive.ics.uci.edu/dataset/406/anuran+calls+mfccs), DOI 10.24432/C5CC9H; Colonna, Nakamura, Cristo and Gordo; CC BY 4.0. The downloaded source README line 21 describes 7,195 syllables from 60 recordings and says each audio corresponds to one frog. The recorded identity supports detecting shared recordings. It cannot establish that an individual never appears under another recording ID.

`prepare_trial.py` creates both partitions reproducibly with seed 20260926, preserving every source row and field. These are **our experimental splits**, not official UCI splits or a newly discovered defect in a published benchmark. Expected counts and source hashes were written to `.data/anuran-user-trial-2026-09-26/reference-answer.json` before the model request. That script imports no Asterisk code.

## What actually ran

1. Loaded the two researcher-exported CSVs, the original README and a six-line experiment description in the native preparation browser form.
2. Selected only RecordID from both tables. The 22 acoustic feature columns and three taxonomy labels remained local. Documentation was included in full; it contains the dataset authors' public professional contacts.
3. Reviewed the payload and made one live `nvidia/nemotron-3-super-120b-a12b` call. It chose file-plus-row observation IDs, RecordID as subject, train/test by file membership, and README line 21 as evidence. No extraction edit or retry was needed. The model did not receive reference answers or compute the verdict.
4. Saved the unconfirmed preparation and continued through the browser's split-check workflow. Explicitly recorded the reviewer as **automated agent / development review**.
5. Ran the trusted measurement and a fresh replay in Nebius Sandboxes. Inspected the witness for recording 1 in the browser: train_calls.csv@1 and test_calls.csv@1 map to the same recorded identity.
6. Previewed moving overlapping test rows into training. The product refused because this would empty evaluation. No repair was saved.
7. Materialized the primary evidence bundle using the same export function used by the product endpoint, from the persisted investigation, preserving exact text bytes. The installed CLI recomputed it successfully without credentials or executing bundled code. This primary bundle was not obtained through a browser download.
8. Ran the recording-group control through the **live product API in a separate test session**, using manually prepared split and identity tables. It made no second model call. It ran its own Sandbox measurement and replay, and its evidence ZIP and HTML were downloaded through the API. This was a supplemental control, not a second browser/native-preparation usability trial.

## Results

| Measurement | Random syllable split | Recording-group control |
|---|---:|---:|
| Training rows | 5,756 | 5,315 |
| Evaluation rows | 1,439 | 1,880 |
| Training recording IDs | 60 | 48 |
| Evaluation recording IDs | 56 | 12 |
| Shared IDs | **56** | **0** |
| Affected evaluation rows | **1,439 / 1,439** | **0 / 1,880** |
| Mapping coverage | 100% | 100% |
| Product verdict | violation | clear_pending_confirmation |
| Fresh Sandbox replay | matches | matches |
| Installed CLI recomputation | matches | matches |
| Recorded execution workflow time | 5.204 s | 4.600 s |

The execution times exclude file preparation, model proposal and review. No time-saving claim follows from them.

Primary investigation: `2b88129a59589fa38cb7468d` in the existing browser workspace. Control: `32287f442b500d5b08614c27` in the separate API test session.

One inference call and four Sandbox executions total. Ledger increment: **$0.00245970 estimated inference cost**, from $6.36025808 to $6.36271778. Provider billing was not independently verified. No cap increase was necessary; no Sandbox charge was measured.

## Would this help the researcher?

Yes, for this bounded task. A researcher can see why distinct rows are not independent frogs, inspect an actual pair, and give a collaborator a reproducible record. The appropriate action is to reconsider the split and evaluation claim before interpreting model performance. Moving every test row into training is not a meaningful repair.

Zero overlap is only one condition. The grouped control has all 10 species in training but only 7 in evaluation; that class-coverage fact came from a separate local count and is **not an Asterisk finding**. The tool does not select a statistically adequate partition, measure classifier accuracy, establish geographical generalization, or prove undocumented frog identities are distinct.

## Friction and limits observed

- The researcher must already produce experimental train/test files. Asterisk does not create these raw experiment artifacts.
- Projection required identifying RecordID before the model saw the data. This helped the model considerably; the run is not evidence of autonomous identity discovery among competing columns.
- The model chose the correct identity citation, but did not separately cite the experiment document for file-role meaning. That role was available in filenames and documentation and was manually reviewed by the agent.
- The preparation-to-check handoff asked for evaluation intent and another binding review despite already retaining the claim and extraction. These are defensible distinct decisions, but the repeated setup is burdensome.
- Source evidence is extensive and repetitive: the long README paragraph appears for both files. The retained preparation grows to about 3.3 MB for only about 34 KB of projected source material. This costs attention and storage, not demonstrated scientific value.
- The result sidebar says manual column review / no new inference even though upstream preparation used Nemotron. It is literally scoped to that step but easy to misunderstand.
- The measurement scope still mentions patients and duplicate images on this frog-audio case. Its limits remain conservative, but the terminology is unnecessarily medical.
- Initial checkbox interactions through browser automation sometimes toggled neighboring controls. Keyboard interaction corrected the selection before upload. This is recorded as automation friction, not proven human-facing app failure.
- The existing session had many development drafts. The primary consumed the remaining slot. No old drafts were deleted or quota bypassed; the supplemental API control did not need a preparation draft.

This was an agent-led, developer-informed walkthrough. I authored both splits, knew the reference answers, selected the uploaded field and reviewed the binding. It is **not** an independent human session, a blind acceptance evaluation, a general-agent comparison or evidence of adoption. A short join script also gets these counts once the identity is known. The demonstrated benefit is preserving and reviewing the interpretation plus replayable evidence—not exclusive detection capability.

## Retained artifacts

All data and execution records: `.data/anuran-user-trial-2026-09-26/`.

- `reference-answer.json`: independent counts and source hashes, pre-model.
- `investigation.json`: persisted primary execution record.
- `evidence/`, `evidence.zip`: primary export-function output.
- `verification.json`: primary installed-checker result.
- `control-request.json`, `control-response.json`: supplemental API control.
- `control-evidence.zip`, `control-export/`, `control-receipt.html`: actual API exports.
- `control-verification.json`: installed-checker recomputation.
- `browser-result.png`: primary browser result.

Reproduction scripts here preserve the researcher split construction and supplemental API procedure. `run_control.py` creates a new live record and triggers two Sandbox executions; do not run it merely to read this report.
