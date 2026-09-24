> Historical record. Current release and runtime configuration: [RC5 status](rc5-runtime-provenance.md). The older image IDs and test counts below do not configure the current release.

# V4 release candidate: feature freeze

The current product supports entity-overlap split receipts only. Feature work is stopped. V3 acceptance remains failed; this release is not a new acceptance pass or a demonstrated human-utility success.

## Current release identity

The release freeze is `.data/primitive-v4/freeze-release-rc2/snapshot.json`; `.data/primitive-v4/current-freeze.json` identifies its full snapshot hash. The snapshot includes the complete allowlisted application, CLI, UI/assets, tests, release tooling, documentation and dependency files. Its hash is external to these frozen source bytes to avoid a self-referential hash.

Trusted measurement implementation: `d718f875426d0ae9be9358e08c3c3e0a378c1e8dcc6ced0c7d989f3774d110e3`.

Matching Nebius image: `19f2ccbc-efd4-4312-9f53-356ef1ac4f9b`.

RC1 snapshot `23ac6cd726309a24a211535bcf76e5c538848700bae99e79fe29e7735234895e` is preserved and superseded by this explicitly versioned review-fix release.

The earlier `26fcfca8133c780d79224f818761caa3e2ebd965c9267654bbd739ffbafc02db` snapshot is superseded for the current product. Its source, image and historical results remain unchanged at `.data/primitive-v4/freeze/`. It must not be presented as covering this release. The new snapshot records its predecessors explicitly.

Verify against the current tree:

```sh
.venv/bin/python evaluation/primitive-v4/freeze.py --output .data/primitive-v4/freeze-release-rc2 --verify
```

## What is shipped

Nemotron Super proposes a cited binding, or a person sets up columns manually. Confirmation is tied to the claim, arguments and input hashes. Trusted measurements and fresh Sandbox replay produce the receipt. Column meaning remains a human-recorded assumption, not independently verified truth. Portable receipts, exact revision comparisons, reviewed partition-reassignment proposals, full affected/unmapped exports, notebook arrays and the local repeat-check CLI are included.

Legacy `/api/audits` mutations and `/api/examples/*` are disabled by default with 404. Saved legacy records remain readable/exportable and are labeled historical; they do not acquire current confirmation/replay guarantees. `ASTERISK_LEGACY_AUDITS=1` is an explicit historical-development opt-in, never a setting for this release preview. Historical tests opt in separately.

## Verification and known boundaries

Current suite: **250 passed, 9 skipped**. The skips are scientific tracing tests for disabled categories; three existing deprecation warnings remain. The new regressions cover default legacy-write denial while preserving history, packet isolation from test-created runtime state, and full-product freeze drift detection. Seven further regressions cover case/Unicode/spacing warnings without verdict changes, surplus identity exclusion, CRLF repair and control-arm selection. Browser QA verified pre-confirmation warnings, focused inline no-key errors and repair-reference labeling; the warning and experiment pages have no document overflow at 390px. This was automated QA, not a human session. A clean extracted source copy is tested by the packet builder using the existing dependency environment; this is not a fresh dependency installation.

The 100,000-row synthetic measurement and fresh replay match the local output, with roughly 1.4 seconds remote execution per run excluding network setup. The original 47-file experiment remains preserved. The disclosed post-review size-matched control extension reproduces all 74 output files byte for byte. Mean MAE increases are 0.1169 after repair (1.60% of mean overlapping MAE) and 0.0040 for control; all seeds are reported. Control MAEs agree with Fable’s independent solver to six decimals. The control was added after its results were known; it is not preregistered or unseen.

Fable reports reproducing the prior 240-test build, independent numerical agreement and adversarial/API/browser checks. Those are external automated observations, not independent human sessions. The subsequent changes cover release-surface gating, packaging, snapshot mechanics, non-verdict identity warnings, CSV-format disclosure, UI corrections and the disclosed control extension. No detector category or verdict path was added. Fable has not reviewed these final changes.

## Evidence that remains missing

V3 acceptance was 9/12 automated primary label matches per trial, 28/36 across all attempts and 4/6 pairs. It remains failed. The later coding-agent comparison matched all 18 authored variant labels, but differed in model, token budget, runtime and tools; it is not a matched performance study. No correctness advantage is claimed. Human evidence review and practitioner comprehension remain unmeasured. No evidence establishes reduced verification effort.

The two real sessions follow the existing v4 protocol, without relaxed thresholds or agent substitutes. Target scheduling by 21 September and completed, committed records by 28 September. If they do not occur, choose a qualified minimal submission or stop; do not add features to compensate. The source remains feature-frozen unless a reproduced release-blocking defect requires an explicitly versioned correction.

Public repository/hosting, a tested judge path, a real under-three-minute video and final entry remain submission tasks. No public push, deployment, outreach, upload or Devpost submission is implied by this freeze. The local preview is an invited single-process application, not a multi-user service benchmark.
