# Reviewed preparation engine

Shared implementation for the experimental preparation editor in the main app. Importing this package starts no HTTP server or inference request.
The main app registers draft storage and policy previews, with editing for saved
drafts. Native file intake includes local CSV/JSON field projection and a consent-bound
proposal preview. Saved drafts can continue directly
to a fresh manual split-check setup after explicit preparation review.

- `intake.open_inputs` validates supplied sources and the starting proposal.
- `ReviewSession.preview` recomputes explicit policies and invalidates confirmation.
- `draft.save` / `intake.reopen` retain previewed choices without confirmation.
- `ReviewSession.confirm` records the explicit local interpretation.
- `verify_record.verify` recomputes a confirmed record.
- `handoff.archive` produces input files for a separate, unconfirmed split check.
- `store.DraftStore` persists validated drafts per workspace owner, with revision
  checks that reject stale saves even when another request commits during
  validation. Callers must supply the owner from the server session. Reopening
  recomputes the review and never restores confirmation. Storage is limited to
  ten drafts per owner, 120-character titles and 32 MB per draft. Deletion also
  requires the current revision. The main app now provides draft import, inspection, renaming, download and
  deletion and explicit preview/save of observation policies.
- `api.register` exposes session-owned draft CRUD under `/api/preparations`.
  See [the API contract](../../docs/design/preparation-draft-api.md).

The files under `research/extraction-observation-review/` with these names are
compatibility entry points, not second implementations. The prototype HTTP
server and browser UI remain separate; the budgeted provider adapter is shared.

Runtime dependencies are still the retained closed executor in
`evaluation/extraction-v1/executor.py` and, for optional model history, the
v3 proposal parser and its v2 dependency. An integration/release must include
these exact dependencies. They were not rewritten or promoted by this move.
Automatic extraction acceptance remains failed; this package does not change it.

The source catalog lives in `catalog.py`. The main and prototype editors share
`static/preparation-fields.js` and the modules in `static/preparation-support/`.
Prototype entry points retain compatibility imports; there is one implementation
of the controls, expression builders, evidence selection and prepared-row reader.

`proposal.py` shares consent-bound payload construction with the prototype.
`proposal_store.py` stores owner-scoped expiring previews and consumes each ticket
transactionally before a completion attempt. Proposal endpoints are registered,
with the native intake UI. The provider stays disabled by default; importing the
package never initializes it. Explicit startup configuration is described below.


`provider.py` uses application-owned completion, deadline, worker and budget
modules. It no longer imports the provider implementation from `evaluation/`.
The extraction executor and proposal grammar still use explicitly packaged
versioned evaluation modules; this change does not promote model acceptance.

For a new installation, create an estimated budget once, on persistent local
storage, with `python -m app.preparation.init_budget --path /absolute/path/budget.json
--limit-usd 0.50` (one command). Its parent directory must already exist.
The command is offline, refuses existing files and symlinks, and accepts a cap
above zero and no greater than $1. It does not enable inference. Never initialize
a replacement for a missing or spent live ledger; recover the original instead.

Set `ASTERISK_PREPARATION_BUDGET` to that absolute path and provide
`NEBIUS_API_KEY` through the environment. Preparation still stays disabled unless
`ASTERISK_PREPARATION_NEBIUS=1`. The explicit configuration needs no research
records, extraction baseline, project ID or `.env` file. Missing, malformed or
exhausted state fails closed; startup never creates a budget. These are estimated
token-cost limits at retained rates, not a provider billing guarantee.

If `ASTERISK_PREPARATION_BUDGET` is absent, the existing research workspace keeps
its original `.data/probe-pilot/budget.json` and extraction cost baseline. This
compatibility path does not reset existing costs. Do not switch the development
workspace to a fresh ledger to bypass its cumulative cap.

A POSIX file lock serializes participating preparation adapters sharing the same
persistent ledger. Do not run legacy evaluation runners concurrently: they do not
participate in this lock. This is not a distributed budget service and must not
be deployed with separate per-worker or ephemeral ledger copies.

The clean-archive test initializes a fresh ledger, configures the app and executes
a completion through an injected stub with sockets blocked. It does not establish
live provider availability, privacy projection, or real-dataset acceptance.

Preparation handoff serializes the full review record as compact JSON. This removes
formatting whitespace only; all source text, lineage, decisions and hashes remain.
The original 10 MB per-file / 16 MB total expanded import limits still apply. A
preparation whose complete compact record exceeds those limits fails export; no
evidence is silently truncated. Native CSV originals are limited to 10 MB; native
JSON originals may be inspected locally up to 32 MB, then must fit the existing
server upload limits after field projection.
