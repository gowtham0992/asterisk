# Fresh real-data workflow: UCF101, 7 October 2026

Asterisk completed its own browser workflow on the unmodified public UCF101 recognition-task split-1 lists: live shipping-v4 Nemotron preparation, reviewed corrections, local measurement, recorded meaning confirmation, one live Nebius Sandbox replay, private receipt, evidence ZIP download, and offline recomputation from a separate trusted release checkout. All 13,320 derived group identities match an independent regex calculation frozen before inference.

This was an agent-operated workflow test, **not a human researcher session or evidence of demand**. The confirmation checkbox was exercised by Codex. The receipt retains an unverified, self-reported confirmation; it must not be presented as a practitioner endorsement.

## What was measured

| Quantity | Independent reference | Asterisk |
|---|---:|---:|
| Training clips | 9,537 | 9,537 |
| Evaluation clips | 3,783 | 3,783 |
| Training action-qualified groups | 1,818 | 1,818 |
| Evaluation action-qualified groups | 707 | 707 |
| Shared groups | 0 | 0 |
| Affected evaluation clips | 0 | 0 |
| Unmapped selected rows | 0 | 0 |

Sources: the [official split archive](https://www.crcv.ucf.edu/data/UCF101/UCF101TrainTestSplits-RecognitionTask.zip), [dataset page](https://www.crcv.ucf.edu/research/data-sets/ucf101/), and the paper's [naming convention](https://arxiv.org/html/1212.0402). The filename carries action, group and clip; groups are local to actions. This verifies recorded action-qualified groups, not unseen actors, sites, visual similarity or model accuracy.

Only original filename lists and researcher-authored setup notes were supplied. No videos, frames, audio, demographics or biometric fields were downloaded or transmitted. Original lists, call transcripts, SQLite records and the evidence ZIP remain private and outside the source release. The notes explicitly explain naming, partition roles and Asterisk's text-list column. This is aided preparation, not autonomous discovery from opaque files.

The published archive contains a capitalization mismatch for HandstandPushups between the folder and filename. The independent parser accepts only case-equivalent folder/filename action labels and uses the filename's action label as its namespace, matching the actual extraction. It rejects other malformed names and duplicate clip IDs.

## What failed or needed help

1. Both split `.txt` files initially became documentation in the UI. Preparation remained disabled until two explicit file-role corrections. This is an observed import usability problem.
2. Nemotron's first reply incorrectly chose individual filenames for the claim and used an invalid sample expression. Application validation rejected it. The normal one allowed repair returned the correct action-plus-group derivation. **First attempt failed; repaired proposal passed.** No extra inference retries were used.
3. The repaired proposal cited lines 9–10 of the notes, leaving the naming and text-column passages outside its citations. The correction form retained the proposed sources, labels and expression. I added lines 7–14 and a scope description; original citations survived. No group-binding correction was needed after the automatic repair.
4. As a separate correction exercise, I temporarily previewed the group number alone. It collapsed 707 evaluation groups into seven IDs. I restored the action-qualified rule before validation or measurement. This was not a model mistake and is not counted as a necessary correction or a measured violation.

The corrected spec remained traceable to the original model proposal. The saved receipt says specification edited, inputs unchanged. This is a useful inspection and handover path, but does not establish an advantage over a handwritten script or a general agent.

## Execution evidence

- Model: Nemotron 3 Super, shipping prompt v4.
- Two provider calls: initial attempt and one validation repair; 11,134 total tokens.
- Provider work: about 33.1 seconds across the calls (UI provider-stage duration 33.19 seconds).
- Conservative estimated token charge: **$0.016701**, charging all observed tokens at the output rate. Not a provider bill. Fixed local estimate cap: $0.25. Hosted judge reserve was not used.
- One Sandbox request, `python:3.12-slim`; 0.643 seconds of reported Sandbox execution. This excludes infrastructure/request time.
- Replay matched local measurement exactly. Result hash: `d8e479c7166bf65795f5fccd66c1428d1d7fdfc4911dd6b5e62ea8a9441dc5d6`.
- Saved receipt: `81f43a87e0525f2ecedd54f4`, in the isolated trial workspace.
- Evidence ZIP downloaded through the product's explicit source-inclusion control. `verify-ladder` from a separate release checkout reported matching measurements, bytes and engine hashes, without network or bundled-code execution. An unsigned receipt still does not authenticate its original data or cloud execution.
- Three independent-reference fixture tests passed, including action qualification, the published case-only folder alias, duplicate IDs and malformed names.

The browser-control adapter stalled during file selection and download. No clean end-to-end user latency is reported; the measured provider and Sandbox durations above are separate and must not be substituted for it.

## Reproduce the calculations

`research/ucf101-researcher-trial/reference.py` takes the official ZIP and independently calculates counts and per-class reconciliation without importing Asterisk. `assess.py` compares the retained evidence ZIP and every derived row against that reference. The private freeze records hashes before model exposure. `PROTOCOL.md` records scope and fixed call limits.

Next product fix: make text filename lists easier to distinguish from documentation at import. The experiment did not modify shipping application behavior or promote the rejected v6 prompt.
