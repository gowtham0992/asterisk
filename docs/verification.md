> Historical record. Current release and runtime configuration: [RC5 status](reviews/rc5-runtime-provenance.md). The older image IDs and test counts below do not configure the current release.

# Current v2 verification — 18 September 2026 (Denver)

Current release: primitive-v3. See [the 18 September v3 report](../evaluation/primitive-v3/REPORT.md) for the narrowed two-category scope, human binding confirmation, Gate A/B results and remaining acceptance work. Sections below retain earlier implementation history and do not supersede that report.

V2 completed its 36-run known-case regression: **11/12 automated-correct in both trials, 4/6 repaired pairs passing, 39/39 primitive replays matching, and 36/36 bundles verified**. The reliability gate still fails. No new unseen v2 evaluation has occurred; independent human evidence review and practitioner sessions remain unmeasured. See [the full v2 report](../evaluation/primitive-v2/REPORT.md) for the two remaining abstention gaps.

All **188 local tests passed**. The new baked image passed all six original development defect/repair pairs and three additional synthetic smoke checks, each with matching remote replay. The app preview was restarted and the browser verified that new investigations open and old records remain accessible with their legacy-evidence label. Release ZIP verification is recorded in `artifacts/primitive-v2-status.json`.

The release allowlist includes the v2 tooling and excludes private `.data` inputs, transcripts and research bundles. V1’s failed experiment and source archive remain preserved.

## Preserved v1 verification — 17 September 2026 (Denver)

The v1 trusted image was `b9669248-af89-4e94-9b92-90623611392c`, primitive implementation `2b7803e2d1690ab392e47660f32ceeb7cd3e097573b6937ba66c5a91d1351d6c`. Six original development defect/repair pairs returned violation/clear, with twelve matching fresh primitive replays. These cover entity witnesses and reordered columns, full-matrix fitting inside a fold, prefit preprocessing before a pipeline, and checkpoint source chains including renamed symbols. The local and extracted-release suites each passed 111 tests.

The engine and evaluation protocol were frozen at 2026-09-18 05:04:48 UTC before authoring the 12-case acceptance set. The set and six repaired twins were authored at 05:09:41 UTC. They use pinned public sources and original controlled cases, with source transformations recorded. The author also implemented the engine; post-freeze authorship is permitted by the protocol but is not independent human review. GraphDRP was excluded because a search snippet revealed its split before the freeze.

The completed acceptance batch failed: 7/12 automated gated-correct verdicts in each trial, 2/6 pairs passing both trials, and 54/54 retained primitive replay matches. All 36 exported bundle manifests verified. Independent blind review remains unmeasured. The acceptance batch and blind review are separate from these development results. Consult `.data/primitive-pilot/acceptance-report.json` for measured rows; no missing row is a pass. Yang notebook content and private research bundles are excluded from the source release.

The following sections retain prior workflow verification history.

# Verification record

## Per-audit Sandbox integration — 17 September 2026

Sandbox execution is now wired into the accepted-rule API and browser workflow. Local execution remains the default. An unchecked control on each review screen authorizes sending that audit's full input files to Nebius; the server rejects a remote request without explicit upload confirmation. No `.env` default was changed. This supersedes the standalone-only status below.

The trusted captured checker runs in a disposable Python 3.12 sandbox with JSON stdin, a 30-second run timeout, and a bounded SDK wait. Credentials are not supplied to the sandbox process. A local replay must exactly match the remote output before completion. Errors remain retryable in review; completed retries do not rerun; deleted audits are not resurrected by an in-flight check. This is a single-process local preview, not distributed job coordination.

Runtime provenance is visible and exported; the evidence ZIP retains the executed program under its hash manifest. Image tags and unsigned hashes do not attest to an immutable remote environment. This still uses a fixed deterministic checker, not an agent writing arbitrary research code.

Validation: 57 automated tests pass, including consent enforcement, default-local behavior, invalid/truncated/mismatched responses, sanitized SDK failures, retries, concurrent requests, deletion during execution, and export reproduction. A deliberately weakened mismatch guard caused the regression test to fail before restoration. A live browser audit used Nemotron and Sandbox execution, found the expected 16 shared synthetic specimens, and its exported evidence reproduced exactly offline. The live clean control found zero shared entities and its export also reproduced exactly. Local evidence: `.data/sandbox-integration-live/verification.json` and `.data/sandbox-integration-live/clean/verification.json`.


Verified 16 September 2026 (Denver), using the local application on port 8765.

## Automated checks

24 tests passed. They cover full-row entity matching, distinct-image leakage, clean and incomplete controls, ambiguous mapping rejection, malformed CSV rejection, literal source citations, record ownership, request-origin checks, input limits, review-before-execution, provider failure recovery, and exported evidence replay with tamper detection. The model boundary is stubbed in offline API tests.

Two deliberate mutations in disposable copies were caught: treating incomplete coverage as clear, and removing the audit ownership check. The live source was not modified by these checks. A dependency deprecation warning remains from Starlette's AnyIO import.

## Live model and browser checks

Provider: Nebius Token Factory. Model: nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B. All cases use original synthetic fixtures; these are functional smoke checks, not independent evaluation or a model-quality benchmark.

| Case | Observed outcome | Provider metadata |
| --- | --- | --- |
| Overlapping split | 16 shared specimens; 16/40 evaluation rows affected; full mapping coverage | 12.16 seconds; 2,758 tokens |
| Independent split | Zero overlap; full mapping coverage | 14.99 seconds; 2,989 tokens; one attempt |
| Missing mapping | No verdict; requested mapping evidence | 16.21 seconds; 3,038 tokens; one attempt |

A prior clean-example attempt was rejected for invalid citations and mapping fields. Inspection showed the model attributed documentation to a CSV and omitted the metadata join. The prompt now labels artifact types explicitly and describes citation filename and join-field contracts. Validation remains strict; only whitespace differences in quotations are normalized back to the actual source text. One bounded repair attempt is available.

Human review remains necessary: the successful clean proposal overstated the implication of entity independence, and the missing-evidence response asked for a column already described in the documentation. Deterministic result copy states that this check does not establish model accuracy or certify an experiment. Citation matching establishes provenance, not semantic correctness. Further model/prompt evaluation is required.

Verified browser flows include creating an audit, accepting a proposed rule, rendering overlap and clean results, missing-evidence handling, reload persistence, switching audits, and uploading three local example files through the file chooser. Inspected desktop, 768-pixel tablet home, and 375-pixel result/missing-evidence layouts. This is not a full accessibility audit.

## Infrastructure and remaining work

Inference credentials work. Token Factory Sandbox image-list access returned `403: Insufficient permissions: list` for the supplied project and key. No remote Sandbox execution is claimed. The local app binds to loopback and is not publicly deployed.

Before submission: resolve Sandbox authorization or choose an appropriate track, evaluate independent cases against a general-agent baseline, improve model explanations and evidence questions, review redistribution rights for any external dataset, harden and host the demo, publish the licensed repository, and prepare the video/submission. No winning advantage has yet been measured.

## Reliability follow-up

Added six frozen synthetic cases and a live prompt-comparison harness. Both prompts passed 6/6 automated decision checks; manual review found unsupported caveats in both. See [the full evaluation](../evaluation/README.md) and its complete raw reports. The rule screen now states scope in fixed language and preserves generated prose in an explicitly unverified notes disclosure. Verified this in the browser, including expanding the original notes on a saved audit.

The offline suite now has 29 passing tests, run in two file orders. New tests catch a scorer accepting the wrong entity, falsely clear coverage, blanket abstention, and premature acceptance of invalid model citations. Deliberate mutations in disposable copies caused all five new tests to fail. No benchmark superiority is inferred.

## Correction workflow verification

36 tests pass, including seven new revision cases: preserved original with corrected execution/export replay; invalid column, overlapping labels, and fabricated citation rejection; owner isolation on raw-input and revision routes; missing-evidence input copying; draft-rule bypass rejection. Each new case was observed failing under a deliberate mutation in a disposable copy. The suite passed again in a different file order.

Browser checks: edited the old overlap proposal's semantic name from subject to specimen, deliberately submitted conflicting partition labels and observed inline rejection with form values retained, saved a corrected child for review, accepted it, and observed 16 shared specimens / 40% affected rows. The original result remained available.

Recovered the insufficient synthetic audit by copying its files, uploading specimens.csv, and requesting a fresh live proposal (20.89 seconds, 2,833 tokens, one attempt). After review it returned the expected 16 shared specimens / 40% affected rows. The parent remained insufficient. Verified reload persistence, original links, cancel, and 375-pixel layouts for both editors. No new external dataset or competitive benchmark was introduced.

## Evidence and comparison follow-up

47 tests pass, including eleven new cases for retained checker code after a simulated application upgrade; changes to checker, rule, and report files that leave counts unchanged; result checking under Python -O; correctly labeled legacy exports; incompatible legacy rejection; changed-contract comparisons; absent measurements versus zero; comparison ownership; and absent/deleted parents. Every new case was observed failing under a deliberate mutation in a disposable copy. The full suite passed again in a different file order.

Browser verification: opened Compare with original for the mapping-supplied revision, saw specimens.csv added and the original findings shown as unavailable, and successfully initiated the evidence ZIP download. Source model proposals and original records remain unchanged. No additional model calls were required for comparison or export.


## Repository release follow-through — 17 September 2026

87 automated tests pass. A prior extracted release passed all 85 tests then present; the current source archive adds the two probe-format regressions. Mobile layout was checked at 390×844 without horizontal overflow. The original synthetic evidence export passed its hash verifier and a separate remote replay with an unchanged bootstrap. Local previous/current/previous archive rollback preserved an audit in the same SQLite database. These checks do not establish hosted availability or scientific validity.

The corrected Super development series completed 20 attempts, with expected-verdict agreement of 8/10 and 9/10, both required abstentions correct, no false violations on controls (two incomplete controls), and matching successful-probe replay in all 20. See evaluation/probe-pilot/probe-review.md for evidence-quality weaknesses. Independent semantic review, the two-practitioner check, an unseen-repository evaluation, hosting and recorded video are still open.
