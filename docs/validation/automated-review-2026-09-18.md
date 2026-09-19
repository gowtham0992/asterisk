# Fresh agent review — 18 September 2026

The user requested fresh agents because no practitioner contacts are available. Two agents receive no conversation history: one independently checks raw tables and compares preserved outputs; one reads a single receipt and answers comprehension questions before critiquing it.

These are automated development reviews, not human sessions, new acceptance results, independent case authorship, or evidence of time saved. The models may share biases with the builder. Branding reveals artifact origin. Expected labels and prior scores are withheld, but the existing cases are development material.

## Assignment fixed before review

Six entity cases: the three entity violations, the leaf-plot control, the PTB-XL group-respecting twin, and the incomplete-coverage case. Every Asterisk result uses historical v3 trial 1. General-agent results come from the preserved baseline. No result was rerun or selected for success. The comprehension review uses the PTB-XL random-split receipt.

`python scripts/prepare_agent_review.py` creates `.data/agent-review-2026-09-18/`. Inputs are hash-checked against both outputs. The baseline's case identifier is neutralized and its machine-specific reproduction command is removed; findings and evidence stay unchanged. The evidence reviewer writes its own checker without importing project code. The source mapping and original baseline hashes are retained separately in `facilitator-provenance.json`. Packet bytes are committed in `packet-manifest.json` before review.

The comprehension reviewer may read only `comprehension/receipt.html`. The evidence reviewer may read only the six `evidence/case-*` directories. Neither receives expected labels. Each writes timestamped results with `actor_type: automated_development_fixture` and `human_validation: false`; ratings are hashed before any outcome reveal.

No paid inference, fresh remote measurement, researcher contact, or human identity confirmation is part of this review. Agent execution time is not human task time. Findings may justify product fixes, whose checks must be reported separately from the original reviews.

## Committed findings and follow-up

Both agents completed. Evidence ratings SHA-256: `5393969d866150fef9d1a61bc56a0d78d9beace7111d004c835c29906482d77c`. Initial comprehension answers SHA-256: `cde3ac7be331a26930e158b025c4d68fb47a84feb08506e56e6fdfe0aefeb644`. Full reports and independent checker remain under the packet's `evidence-review-output/` and `comprehension-review-output/` directories.

The independent checker verified all 680 comparison witnesses and 57 retained Asterisk witnesses. Five Asterisk outcomes were supported; one historical run was safely insufficient but missed actual overlap because it used `partition` as the sample identifier. It incorrectly suggested duplicate recording identifiers; the raw identifiers were unique, with 623 shared patients affecting 692 evaluation rows. The original failure remains unchanged. Current preflight validates unique/nonblank selected sample identifiers; this review does not claim a new engine success.

Implemented presentation fixes in the app and portable receipt: explicit blocked state and selected join, same-column diagnosis, replay-of-error explanation, per-partition mapped/missing counts, and a conditional witness question. Portable receipts now place supplied identity documentation near the assumption, deduplicate repeated limitation text, and explain that historical requests may misdiagnose the failing column. No semantic confirmation is inferred from documentation.

The comprehension agent checked the first corrected receipt in an explicitly unblinded follow-up and found all five targeted fixes present. It still noted generic historical diagnosis, header-only historical citations and jargon. Later presentation notes distinguish retained diagnosis from configured-column errors; historical citations remain preserved rather than silently replaced. No subsequent blind study occurred.

Verification: regression test reproduced the blocked-state problem before the fix; full suite after changes: **227 passed, 9 skipped**, three existing deprecation warnings. Frontend module syntax check passed. All 43 original packet file hashes still match. Human review remains **unmeasured**. No new acceptance pass, model advantage, practitioner preference or time-saving claim follows from these results.

## Remaining findings closed in the next product iteration

- Invalid column choices now include structural recovery candidates: unique, nonblank split columns sharing values with the mapping key. They are suggestions for review, never automatic identity-role assignments. Both preview and final confirmation use the same validator.
- Blocked receipts separate preserved, potentially incorrect model requests from current guidance. The app no longer leads with the historical model's wrong data-defect diagnosis.
- App and portable receipt show exact, line-numbered documentation excerpts mentioning selected identifiers. These are explicitly lexical matches, not verified definitions; denials and nearby restrictions stay visible. CSV-header citations are labeled as column-name evidence only. Historical citations and results are unchanged.
- Binding, partition and replay are explained in ordinary language; selected partition labels are displayed, and the portable worksheet uses those labels. Repeated identical requests are deduplicated for display.

Three new regressions failed before the fixes and passed after implementation. Full suite: **230 passed, 9 skipped**, three existing warnings. Browser verification exercised wrong-column rejection, candidate suggestion and successful corrected preflight without recording confirmation or making a remote call. The known PTB-XL failure was checked locally with the corrected `ecg_id` selection: 623 shared patients and 692 affected evaluation rows, recorded separately in `.data/agent-review-2026-09-18/post-fix/column-recovery.json`. This is exposed development regression evidence, not a new blind result or acceptance run. The original 43-file packet still matches its committed hashes.

Human utility remains unmeasured; this is not a defect that software changes or agent reviews can resolve.
