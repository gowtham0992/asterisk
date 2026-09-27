# Follow-ups from the new-domain researcher walkthrough

The frog trial was concrete progress: a new domain completed live preparation, measurement, replay and local verification. It also identified product friction. The broader user goal, “make it awesome,” remains active; this list is an implementation queue, not a replacement definition of that goal.

Completed in this turn:

- The result sidebar now exposes the retained preparation model and provider even when the final binding was reviewed manually.
- Offline HTML carries the same distinction between proposed extraction and measured overlap.
- Attribution requires the preparation to recompute against the actual supplied tables. Invalid, missing and non-model records do not acquire model credit. Retained metadata is explicitly not provider-authenticated proof.
- 34 focused Python tests passed; all 147 JavaScript tests passed. The actual saved frog receipt visibly showed the model/provider in the running browser, with no browser errors. Offline rendering against the same persisted result was checked separately. No new inference or Sandbox call was needed.

Remaining from this trial:

- Evaluation-purpose handoff is implemented (see continuation below). Reduce the remaining repeated review steps without removing the identity decision.
- Reduce repeated source passages and make the review sequence shorter without removing the identity decision.
- Explain why a repair cannot preserve a viable test partition and what the researcher should consider next.
- Make domain-specific measurement language appropriate beyond medical images without changing historical trusted measurements silently.
- Measure researcher benefit with real independent readers; an agent-led walkthrough does not replace this evidence.

The local server is running the updated source with the existing database. Git inspection is unavailable because the machine's Xcode license has not been accepted; no license was accepted and no commit was made.


## Evaluation-purpose continuation

The optional “Who or what should be unseen?” field now travels through the consent-bound preparation payload, saved draft, reopen and handoff. It is locally retained user context, not new model prompt content. The split-check form receives the explicit intended unit; no identity confirmation is copied. Changing that context changes the payload hash. Legacy drafts without it remain unspecified. Recovery of a failed proposal retains it for manual setup.

Verification: 469 Python tests passed with 9 existing skips, followed by an additional passing API persistence test (18 proposal tests passed). All 149 JavaScript tests passed. API tests cover preview, mocked completion, review, save, reopen and handoff; UI tests cover visible saved intent and the actual handoff seed. The running native form was inspected in-browser with keyboard navigation and no console errors. No live model request was made for this change. Snapshot: `/private/tmp/asterisk-preparation-purpose.png`.

## Shared-passage continuation

The pre-run review now renders identical retained citations once per preparation record, while keeping each source file's observation and subject choices separate and naming which files cite each passage. Missing evidence, truncation, prior-confirmation limits and repair provenance remain visible. Full source lines remain available in a keyboard-operable disclosure; ordinary inputs without preparation keep the source browser open.

Verification: all 152 JavaScript tests passed. Renderer regressions cover shared citations, different coordinates, missing evidence, untrusted text and repair context. In the running app, the saved DermaMNIST repair review displayed the new passage layout and original-preparation warning. Keyboard expansion and literal source search worked (one matching line for “lesions”), with no browser errors. Screenshot: `/private/tmp/asterisk-grouped-evidence.png`. No model or Sandbox calls were made. The scientific checker and saved measurements are unchanged.

## Repair refusal continuation

An empty-partition refusal now reports which side would empty and the resulting training/evaluation counts. It directs the researcher to the affected groups, group-respecting split design, population/class coverage review and retraining, without promising that the other reassignment policy is scientifically appropriate. The refusal still creates no revision. Both directions are covered by preservation tests; all 11 repair workflow tests passed. Replaying the proposal locally against the saved frog receipt reproduced 7,195 training rows and zero evaluation rows. No inference or Sandbox execution was needed.

## Cross-domain receipt language

Portable receipts now explain exact-ID comparison, undocumented links, duplicate content and predictive-performance limits in domain-neutral terms. The original measurement scope is retained verbatim in its own disclosure, explicitly identified as historical checker wording. No measurement or trusted checker bytes were changed. The pre-run mapping label is now “Unit that should be unseen.”

Verification: 15 focused Python receipt tests and all 152 JavaScript tests passed. The saved frog result was rendered to `.data/anuran-user-trial-2026-09-26/receipt-domain-neutral.html`; the retained result hash was unchanged before and after rendering. This avoids changing the historical medical examples inside authenticated measurement records just to improve presentation.

## Observation-definition review after the routing failure

The failed synthetic routing experiment exposed a concrete mechanism: a correction can replace documented observation IDs with row identity and pass structural execution while changing the scientific unit. Automatic correction remains unintegrated. The existing manual preparation preview now compares observation policies directly, independently of whether original row extraction succeeded. It calls out observation-expression changes, gives an explicit warning for row-number substitution and explains the documentation requirement when combining repeated observations. These notices neither infer scientific meaning nor grant confirmation.

All 155 JavaScript tests pass. New tests cover an unexecutable starting proposal's policy transition, nested lookup edits, key-order invariance and collapse-policy changes. Existing saved/proposed policy defaults remain compatible. Live browser walkthrough of this specific notice is still pending; the test result is renderer and surrounding-suite evidence, not an independent usability finding.

Browser verification completed for the observation-policy notice. On saved synthetic repeated-record draft revision 2, previewed column `sample` → each source row and collapse → distinct. The screen showed training observations 2 → 3, evaluation 1 → 1, and all four source records changing observation identity. The new warning appeared before row-change details. Replaced raw JSON as the primary explanation with the existing plain-language identity formatter; exact expressions remain keyboard-expandable. Repeated the live preview after reload and verified the final wording and disclosure. Discarded the temporary edits through the unsaved-work dialog; the draft remains revision 2. No save, confirmation, inference or Sandbox call occurred. All 155 JavaScript tests pass. Screenshot: `/private/tmp/asterisk-observation-warning-final.png`.

## Capacity before inference

The real workspace reached its 10-draft limit. Previously, a new paid proposal could finish before draft creation disclosed the limit. Owner-scoped capacity is now reported by the read-only capability endpoint and checked before preview creation and again before claiming a ticket for inference. Rejection does not consume the ticket or contact the provider. Native intake shows the full-storage notice and a link to existing drafts; local field inspection remains available. Existing drafts were not removed.

Verification: 25 focused proposal/runtime tests passed, including filling the workspace between preview and dispatch, and checking that the ticket remains ready with zero provider calls. The broader Python run had 473 passes plus one outdated exact capability-response assertion; that assertion was updated for the added capacity field and passed in the focused run. All 155 JavaScript tests pass. Live browser reload shows the notice on the actual full workspace before upload (`/private/tmp/asterisk-capacity-warning.png`). The check is not a durable slot reservation across processes; saving still enforces the database limit.

After this source change, preserved all 39 frozen routing-study source files under `.data/preparation-failure-routing/frozen-source/`. The two changed application files were recovered from the earlier verified source ZIP and checked byte-for-byte against the pre-run hashes. No study result was rerun or rewritten; recovery provenance is retained there.
