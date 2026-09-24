# Live binding development check — RC3

20 September 2026. Six live NVIDIA Nemotron Super proposals passed on three previously exposed cases, two trials each. No retries, prompt changes or simulated human confirmations. This is a targeted development result, not a fresh acceptance pass or independent evaluation.

| Case | Proposals matching documented binding | Gated result, both trials | Measurement |
|---|---:|---|---|
| PTB-XL planted record split | 2/2 | violation | 623 shared patients; 692 affected evaluation recordings |
| Original synthetic field-plot control | 2/2 | clear_pending_confirmation | zero shared plots; complete mapping |
| PTB-XL incomplete identity projection | 2/2 | insufficient | incomplete identity coverage; no clear verdict |

All six measurements matched fresh Sandbox replay. The model chose ecg_id as the recording/sample key and patient_id as the entity for both PTB-XL cases. It chose leaf as the sample key and plot as the entity for the synthetic control despite reversed mapping-column order. Comparing proposals against the supplied dictionaries was a post-run developer inspection, not independent human review.

The run called the product's real `propose_plan` and binding-preview functions, followed by the trusted remote measurement and gate. It did not drive the browser or record human confirmation. The separate browser recovery check is documented in `binding-recovery-and-newlines.md`; combining these records does not turn them into a single end-to-end browser evaluation of Nemotron.

Only the approved identity/partition projections and their documentation were used. No signals, diagnoses or demographics were transmitted. The run used the existing $10 development ledger; estimated settled inference cost was $0.0082845 at its recorded rates, not a provider billing reconciliation. Six conservative reservations totaled at most $0.1935. Sandbox image: `80519d96-3de8-4f48-95ed-2de62a8351d4`.

The protocol, exact transmission inventory, individual plans, measured results, replays, usage and post-run binding audit are retained outside the public product at `research/live-binding-check/`. No raw research inputs or private transcripts are added to the source release.

Earlier v3 acceptance remains failed. Two trials per exposed case are too few to estimate general reliability, and there is no before/after experiment establishing that recent context changes caused these successes. Researcher utility, human evidence review and unseen acceptance remain unmeasured.

## Release candidate

RC3 freezes the current allowlisted source and the verified image. The freeze now checks a separately recorded Sandbox-driver hash as well as the primitive implementation hash, because the newline fix changed the driver without changing the primitive. Previous freezes remain preserved and superseded, not overwritten. This release candidate is for deployment testing and submission preparation; it is not a public launch.
