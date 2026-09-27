# RC6: adversarial developer review — 23 September 2026

The review found consequential defects, including a plan-screen crash introduced in RC4 and missed by the passing Python suite. They are fixed below. This is developer self-review, not independent evaluation, human evidence or a new accuracy benchmark. The entity-only scope, failed v3 acceptance and unmeasured researcher benefit remain unchanged.

## Findings and changes

| Finding | Reproduction | Resolution |
| --- | --- | --- |
| P1: plan screen crashes | Browser manual plan reaches `a.input.claim`, but the public API exposes `a.claim` | Correct public field; cache-busted assets; a real-renderer regression test fails with the old expression and passes now |
| P1: contradictory retained receipt can display clear | Replace saved violation with clear without changing its overlap evidence | Recompute with installed primitives before presenting a v4 receipt; inconsistent evidence receives an explicit failure instead of a definitive headline |
| P2: incomplete manifest passes verification | Empty inventory, omitted result/input, or duplicate JSON keys | Require core artifacts and exact input inventory, reject duplicate keys and unsafe/symlink paths, bound verification sizes; verify hashes |
| P2: comparison/repair validates too little | Alter coverage, witnesses or a replay record while preserving two headline counts | Check the full measurement against original inputs and any claimed replay against retained evidence before comparison or repair |
| P2: startup changes unrelated parent-directory permissions | Database directly below `/private/tmp` fails at chmod; an owned shared directory would have its mode changed | Apply private mode when creating the database directory; preserve existing parent permissions |
| P2: reviewer download does not identify the receipt | Workspace points at generic worksheet with no receipt reference | Owner-scoped download embeds the canonical result hash; unfinished investigations return 409 and another owner gets 404 |
| Product friction: recipient recheck needs remote setup | Portable hash check cannot reproduce a scientific measurement | `python -m asterisk verify RECEIPT_DIRECTORY` checks inventory, recomputes from original inputs and checks the verdict using installed code, with no network or credentials; it never executes bundle-supplied Python |
| Unnecessary history processing | Listing all investigations loads full evidence and reparses tables | SQL projects only ID, title, state and creation time; detailed verification stays on the selected investigation |

One-row wording is also corrected. JS regression tests are included in source releases. No new audit category, hosting service, external messages or publication was added.

## Verification

- Python suite: 309 passed, 9 skipped (optional sklearn-dependent coverage). Existing FastAPI/AnyIO deprecation warnings remain; they are not runtime failures.
- Actual route/renderer JS test passes; restoring the old expression in a disposable copy makes it fail with the browser's original exception.
- New tamper tests were observed failing before the corresponding fixes. They cover inventory omission/duplicate keys, inconsistent verdict/count/confirmation/replay, and comparison evidence beyond headline counts.
- CLI tests regenerate the manifest after forging the verdict: byte integrity succeeds, semantic consistency fails with exit 1. An unchanged receipt exits 0.
- Browser: synthetic example → manual column selection → preview → confirmation → real Nebius Sandbox measurement and fresh replay → result → repair preview → separate unconfirmed revision. Observed one shared identity, one affected evaluation row of two, full coverage. The proposal moves one row, retains all three rows and leaves one evaluation row. The child requires new confirmation.
- The live synthetic receipt also passed installed local verification. No inference or third-party research datasets were used for this review. The synthetic UI confirmation is developer QA, not a human validation session.
- Browser screenshot inspected at the normal desktop viewport. This turn does not claim a new narrow-screen, screen-reader or offline-file-browser accessibility audit.
- Release builder tests an extracted source copy, not the tree it packages. This uses the existing interpreter and dependencies, not a fresh dependency installation.

## What is still not established

A receipt proves consistency within the recorded binding, not that an identity column has the correct scientific meaning. Hashes and replay do not authenticate the author or the person recorded as confirming a binding. A malicious author can replace every unsigned artifact with a different internally consistent experiment. The local verifier does not attest historical remote execution.

The general coding-agent comparison previously matched all 18 variant labels. There is no demonstrated detection advantage and still no measured time-saving or comprehension advantage for researchers. Human sessions, deployment, video and submission remain outstanding. No automated review resolves those questions.

The product is a bounded exact-identity evidence recorder with a useful repair/recheck workflow. It is not a general leakage detector or an established must-have research tool. Further detector features would not fix the missing evidence of demand.

## Release status

RC6 supersedes RC5 for the host application and receipt verification. The trusted measurement implementation and baked driver are unchanged. Current immutable snapshot: `.data/primitive-v4/freeze-rc6-2026-09-23`; its canonical digest is stored in `snapshot.sha256`. Source and review packets are `artifacts/asterisk-source-rc6-2026-09-23.zip` and `artifacts/asterisk-rc6-review-2026-09-23.zip`. Historical freezes remain intact.
