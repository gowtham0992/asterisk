# Fable full-review response — RC2

All locally implementable findings in the 19 September review are addressed. This is a versioned correction to RC1, not new acceptance or a human-utility result. Feature expansion is stopped.

| Finding | Resolution | Evidence |
| --- | --- | --- |
| F1 freeze drift | Full allowlisted product snapshot RC2 supersedes RC1 and the old v4 snapshot, preserving both. Trusted code/image still match. | Current-freeze pointer, freeze verification, drift regression |
| F2 legacy surface | Writes and examples default to 404; owner-scoped historical reads/export remain. Explicit development opt-in only. | Default-denial and legacy-history regression |
| F3 packet runtime files | Packet builder verifies archive bytes, tests a disposable copy, and includes only original verified bytes. | Database/hidden-path rejection and test-mutation regression |
| F4 missing control | Added exactly one size-matched arm, all five seeds, relative 1.60% repair difference and post-review disclosure. | 74 identical files across two executions; original fits unchanged; control matches independent supplied values to six decimals |
| F5 near identities | Case/NFKC/spacing collision diagnostic in binding preview, receipt and offline receipt; no normalization or verdict change. | Four near-ID regressions, surplus exclusion, browser warning |
| F6 formula-looking CSV IDs | Exact CSV preserved; rows.json prioritized and text-import caution displayed in UI/export guidance. | UI inspection; existing exact-value export tests |
| F7 CSV dialect | Preserve header record line endings; explicitly disclose normalized quoting in signed proposal. | CRLF regression and repair safety suite |
| F8 UX mismatches | Focused run error beside run button; repair citations and limitations labeled as references/repair notes. | Credential-free synthetic browser run; live repair-child inspection |
| F9 serialization | 409 names the across-session single-job limit; invited-preview operations documented. | API text and release instructions |
| F10 security residuals | Retained protections; disclose server-session retention and shared preview credentials. No broad auth rewrite. | Existing API/security suite; release limitations |
| F11 stale surfaces | Removed initial New audit button, Super default/session metadata, current v4 doc has one test count and current freeze reference. | Workspace browser check, configuration and release verification |

Verification: 250 passed, 9 skipped (disabled scientific tracing), three existing deprecation warnings. JS syntax and whitespace checks pass. Extracted packet tests use the existing dependency interpreter in a clean temporary source tree, not a newly installed environment. No paid inference or new remote measurement was required for these changes; the trusted measurement code and baked image are unchanged. Historical replay evidence remains historical.

## Still external and unmeasured

Two actual practitioners have not been recruited or observed. Invitations and protocols are prepared in docs/validation; agents are not substitutes. Preserve the 28 September decision gate and the existing thresholds.

Public repository, HTTPS hosting/judge access, real under-three-minute video and Devpost submission are not complete. The draft entry, demo script, source archive and host/rollback instructions are prepared. Repository owner, hosting destination and outreach scope remain unspecified. No publication, outreach or video upload has occurred. Before release, verify event requirements and owner eligibility; do not present prepared materials as a submitted entry.

Remaining advantage claim: easier verification is an unmeasured hypothesis. V3 acceptance remains failed; the agent comparison is not matched and demonstrated no correctness advantage. No test count, control experiment or automated review changes those facts.
