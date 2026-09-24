# RC4: a receipt another reader can interpret

22 September 2026. Local follow-up to Fable's RC3 decision review. The product remains entity-overlap only. Its value hypothesis is easier inspection by a second reader, not a more powerful join or demonstrated research benefit.

## Changes

- The portable receipt now states excluded row counts and exact excluded labels, distinct training and evaluation identity counts, distinct mapped identities over selected samples, and the measurement's scope sentence.
- Before confirmation and on the receipt, a non-blocking warning explains when every selected sample has a distinct identity and overlap is impossible under that binding. Surplus mapping rows are excluded from this diagnostic; incomplete coverage cannot trigger it. This diagnostic neither merges identities nor changes the verdict.
- CSV citations are marked as data or headers rather than identity documentation.
- The plan headline uses the user's claim rather than model-written scope.
- Reviewer summaries require `independent: true` in addition to human actor, consent and unseen labels. Missing, false and string values are excluded. Independence remains a self-report, not authenticated evidence.

Fable's retracted validation-guard proposal was not implemented. Primitive measurement code, gate, driver and Sandbox image are unchanged. The product snapshot changes because presentation and review tooling changed.

## Verification

The new regression tests first produced six failures and one pass on RC3. After the fixes: 283 passed, 9 skipped in the full Python suite. The nine skips remain the optional sklearn-dependent cases. JavaScript syntax and the existing comparison UI test pass. The package builder also runs the suite on a separate disposable extracted source copy; this uses installed dependencies, not a fresh dependency installation.

Fable's 100-row reproduction returns the same scoped measurements: selecting `train`/`test` excludes 50 `Test` rows, while including both test spellings reveals 40 shared identities. The receipt now discloses the exclusions explicitly. No verdict was changed to make this example pass.

Generated HTML content was checked by regression tests. A fresh visual browser inspection was not completed: local HTTP binding was denied by the execution sandbox and the browser blocked file URLs. No alternative browser path was used.

## Remaining boundaries

The full review contains more than the executive summary. These findings are recorded, not represented as fixed by this narrow change:

- Similar-looking ID warnings do not cover all invisible Unicode characters or cross-script confusables. Measurement remains exact and case-sensitive.
- The bundle's legacy bootstrap and absent primitive driver need correction before claiming it retains the actual executed program. Unsigned manifests prove internal byte consistency, not authorship; the primitive hash does not cover receipt presentation. Replay does not independently authenticate a rendered verdict.
- Runtime driver/image checks and the environment-override deployment path need verification and correction before hosting. Release-time freeze checks do not substitute for runtime verification.

RC3's six live proposals are known-case development results; they are not a new RC4 live run. V3 acceptance remains failed. No real human sessions, adoption or time-saving evidence has been collected. No deployment, public repository publication, video upload or submission occurred in this follow-up. Hosting remains paused; the review's 2 GB server suggestion is not authorization to provision it.

## Release reference

The full snapshot is `.data/primitive-v4/freeze-rc4-2026-09-22/snapshot.json`; `current-freeze.json` records its hash. RC3 snapshots and archives are retained unchanged. Trusted primitive hash remains `d718f875426d0ae9be9358e08c3c3e0a378c1e8dcc6ced0c7d989f3774d110e3`; driver hash remains `cf87ab3ec129a16c6f5836c14ba0e3d3683bc72e98c47fdb48fe0ab65f6fc64a`. Those hashes do not describe the entire app. The current baked image is `80519d96-3de8-4f48-95ed-2de62a8351d4`.
