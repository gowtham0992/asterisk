# Asterisk

Local draft for **Best apps and agents**. Official submission fields and judging criteria were read through Devpost on 23 September 2026 (Denver); the captured requirements are in `docs/submission-requirements-2026-09-23.json`. No project content was written to Devpost during this preparation. Demo, public-source and video requirements remain incomplete.

## One-line Summary

Check whether your test subjects are new—and hand over the evidence.

## Problem

Different sample IDs do not necessarily mean different subjects. Two scans can belong to one patient; two recordings can belong to one speaker; two photographs can show one lesion. If those identities cross a split, evaluation cannot establish that the model generalizes to unseen subjects.

Our first user is a research engineer preparing a benchmark result for a collaborator or reviewer. Once the identity mapping is available, a join can detect overlap. The handoff still needs to explain which identity was checked, which rows were included, and how someone else can reproduce the conclusion.

## Solution

Asterisk turns that check into a split receipt. Supply the split table, identity mapping and documentation. NVIDIA Nemotron proposes the columns and a source citation. Review the proposal against full-table cardinalities and exact partition labels, then confirm what the identity represents.

A trusted checker runs in a Nebius Token Factory Sandbox, and a fresh Sandbox repeats the measurement. The receipt shows the result, original-row witnesses, excluded rows, mapping coverage and the assumption you confirmed. A collaborator can inspect those choices rather than relying on the model's explanation.

If the split needs a repair, preview the affected rows and new partition sizes. Approve a separate revision, confirm its binding and run a new check. The original receipt stays intact.

## Why This Matters

This is a concrete benchmark failure mode. A 2025 Scientific Data audit reported 641 lesions shared between training and testing in the original DermaMNIST split. Our local reproduction from the authors' pinned metadata matches those 641 lesions, with 693 of 2,005 test images belonging to shared lesions. The public case-study page links the source files and provides a command that checks their hashes and independently cross-checks the computation.

That is a reproduction of a known finding, not a new discovery. Lesion overlap does not establish patient overlap or quantify accuracy inflation. The case study is local deterministic computation, separately labeled from the live Sandbox receipt workflow.

Source: https://www.nature.com/articles/s41597-025-04382-5

## How We Used AI

NVIDIA Nemotron 3 Super, served through Nebius Token Factory, proposes a cited binding between the research claim and supplied table columns. It helps interpret documentation; it does not generate the trusted checker or decide the measured verdict. A person must review the identity semantics. Manual column setup is also available.

Nebius Sandboxes separate execution from the application process and allow a fresh replay of the trusted measurement. The application checks implementation, driver and input provenance and suppresses a definitive result if execution or replay fails.

Neither NVIDIA nor Nebius is mathematically necessary to perform a join. Their role here is documented model-assisted setup and isolated, repeatable execution. We claim no demonstrated correctness advantage over a general coding agent.

## How We Used Codex

Codex helped implement and test the API, browser workflow, deterministic measurements, receipt verification and release packaging. It reproduced review findings, added regression tests, inspected responsive layouts, and verified the packaged source in a fresh environment. External model reviews contributed hypotheses; their claims were checked against executable evidence. Those reviews are not independent human usability studies.

## Key Features

- Cited model proposals, editable column bindings and explicit human confirmation.
- Original-row witnesses, complete mapping coverage and excluded-row accounting.
- Trusted Sandbox measurement with fresh replay and explicit failure states.
- Separate repair revisions that retain the original evidence and require new confirmation.
- Offline HTML receipts and recomputation using a separately obtained trusted installation.
- Notebook/CLI input preparation, saved column configurations and a guided synthetic example.

Automatic native-metadata extraction is experimental and is not a shipped feature. Preprocessing and checkpoint-selection checking are not shipped categories.

## Architecture

A FastAPI server serves a plain JavaScript interface and stores owner-scoped records in SQLite. Token Factory supplies Nemotron inference. Application-owned Python runs the entity-overlap measurement in the configured Sandbox image; a second execution must match. Exports retain inputs, reviewed arguments, assumptions, measurement records and hashes. The hosted configuration is an invitation-only, single-process research preview, not a multi-tenant research platform.

## Testing Instructions

1. Install Python 3.14 and the locked requirements, following README.md. Configure the Nebius key/project and a matching baked Sandbox image outside the source tree.
2. Start the preview and select **Explore a synthetic example**. This example contains one shared specimen affecting one of two evaluation rows.
3. Inspect the files. Use the optional Nemotron proposal to exercise inference, or the documented manual binding to exercise only the measurement workflow. Confirm the binding and authorize the listed provider upload before running.
4. Inspect a witness, preview a repair, and run a separately confirmed revision. Export the evidence.
5. From a separately obtained and verified Asterisk installation, run `python -m asterisk verify /absolute/path/to/receipt`. Do not run it from inside a received bundle. This checks measurement and decision consistency, not the author's identity or the truth of the source data.
6. To reproduce the known DermaMNIST result without credentials or uploads, follow the published-example page and run `scripts/reproduce_dermamnist.py` against its two pinned upstream CSVs.

The verified source archive passed **315 tests, with 9 skipped**, both in an extracted source copy and in a fresh isolated Python 3.14.7 environment on macOS arm64. The skips concern retained scientific-trace tests for disabled categories. Linux deployment and hosted rollback are not yet verified.

## Public Demo Link

**TODO:** working HTTPS demo and testing credentials. A local preview does not meet the public-access requirement. Keep credentials out of this description.

## Public Repository Link

https://github.com/gowtham0992/asterisk — **currently private**, not yet eligible as the required public code repository. Draft PR #1 contains the verified working-source package. Visibility and merge decisions remain outstanding. The application has an MIT license; this does not relicense research datasets.

## Demo Video

**TODO:** record and upload a public YouTube video. Target 2:40, leaving margin below three minutes. Follow `docs/demo-script.md`: published problem, actual synthetic workflow, witness, separate repair and receipt verification. Retain real model corrections and disclose any time compression. No simulation presented as a live provider call.

## Screenshot Shot List

Capture these from the final candidate, excluding keys, private records and browser account details:

1. Published example: 641 shared lesions, attribution and local-reproduction label visible.
2. Actual Nemotron proposal: documented identity binding, column counts and partition labels.
3. Completed synthetic receipt: one shared specimen, affected rows, coverage and scope.
4. Expanded original-row witness alongside its identity mapping.
5. Original and repaired receipts, showing separate revisions and the remaining evaluation size.

Screenshots are not yet a completed final submission asset set.

## Submission Readiness Notes

Live Devpost inspection: registered; Asterisk is a submission draft with no video, demo URL or final submission timestamp. The code has a tested private handoff. Hosting, public visibility, final video, screenshots and owner declarations remain outstanding.

The four live judging criteria are Technological Implementation, Design, Potential Impact and Quality of the Idea. Implementation has executable evidence; design has developer browser QA. The potential-impact claim remains a hypothesis until real researchers assess the handoff. We should not replace that missing evidence with more agent reviews or inflated accuracy claims.

## Known Limitations

V3 acceptance failed: 9/12 primary cases matched per trial and 4/6 defect–repair pairs passed, although all 44 measurements replayed. The supported workflow was narrowed to entity overlap. A general-agent practical comparison matched all 18 authored variant labels; there is no claimed correctness advantage. Human evidence review and practitioner comprehension remain unmeasured.

Native extraction failed its original feasibility run and a later synthetic challenge. V3 interface repairs passed 16/16 now-exposed development trials, not fresh acceptance; the feature remains outside the product.

A separate five-seed experiment measured a 0.117-point mean MAE increase after removing planted participant overlap, compared with 0.004 for a size-matched row-removal control. The control was added after review. This is a modest descriptive result in one constructed setting, not a general effect or a discovered defect in the source dataset.

The checker only covers recorded identities under the confirmed binding. It cannot establish missing identity links, detect all duplicated content, certify an experiment or validate medical performance. A human confirmation is an assumption record. Hashes and replay do not establish scientific meaning or authenticate a sender. A trusted recipient must obtain their checker independently of the received bundle.

## TODO Official Form Fields

Draft answers below map to live field IDs; they have not been sent. Owner declarations and numeric satisfaction ratings require the owner's answers.

| Field | Draft answer or remaining action |
| --- | --- |
| 28261–28262, submitter type/organization | TODO: owner declaration |
| 28265–28266, residence/Canadian province | TODO: owner declaration; do not infer from device timezone |
| 28267, track | Best apps and agents |
| 28268–28269, new/existing and updates | TODO: owner confirms whether any project existed before August 26, 2026 |
| 28270, public source | Private repository above; make public only after owner authorization and final source review |
| 28271, working demo | TODO: HTTPS test URL; required by the prose for this track despite globally optional field metadata |
| 28272, model and rationale | Nemotron 3 Super for a bounded documentation-to-column proposal. This is a practical choice, not a measured best-size claim. No fine-tuning. |
| 28273, quality rating | TODO owner numeric score. Observed strengths: useful cited proposals. Observed failures: wrong identifiers, invalid structured outputs and mistaken abstentions. Human review and strict validation remain necessary. |
| 28274, prompting | Task-specific prompts, source previews, explicit output contracts and deterministic validation; no fine-tuning. |
| 28275, comparison | A general coding agent matched 18/18 authored labels in a practical comparison. No matched, general model-performance advantage is established. |
| 28276, Nebius capabilities | Token Factory inference for proposals; Sandboxes for isolated trusted measurement and fresh replay. No self-managed GPU training or autoscaling claim. |
| 28277–28278, recommendation/inference ratings | TODO owner numeric scores. Development feedback: inference and disposable execution supported the workflow; access setup and version/provenance alignment required care. |
| 28279, improvements | Clearer SDK/version alignment, consistent structured-output/tool support documentation, and more actionable typed errors. |
| 28280, model roadmap | More reliable schema adherence, calibrated refusal and faithful distinction between a missing field and missing evidence. |
| 28282, Tavily runtime use | No |
| 28281, IRL city | Leave blank unless the owner confirms attendance and eligibility |
| 28283–28284, age/employment | TODO: owner declarations |

The live form did not request a Codex session ID; none is included. Recheck final rules and form before any submission.
