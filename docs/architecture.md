Current product: v4 entity-only split receipts. See [v4 implementation](reviews/v4-implementation.md). The architecture below is retained development history and does not supersede v4.

# Current repository investigation architecture — v2

Current release: primitive-v3. See [the 18 September v3 report](../evaluation/primitive-v3/REPORT.md) for the narrowed two-category scope, human binding confirmation, Gate A/B results and remaining acceptance work. Sections below retain earlier implementation history and do not supersede that report.

Nemotron selects one of four baked measurement primitives. `entity_overlap` reuses the fixed CSV checker and independently verifies train/test witnesses and per-partition mapping coverage. `fit_sites` resolves bounded AST fit-site flow. `fit_trace` executes the actual supplied scientific script under protected fit/split hooks; unsupported syntax or ambiguous fingerprints return unavailable. `symbol_chain` checks five connected source roles using bounded tracing across supplied local imports, functions and instance methods. Unsupported or unresolved paths remain insufficient.

Notebook-export normalization is limited to the standalone display-only `%matplotlib inline` directive and its supported IPython equivalent. It preserves original line positions and records source hashes and replacements. Execution magics and shell commands are rejected. Normalization never executes uploaded code on the host.

The model receives category-specific tools, argument schemas and retained feedback for correcting invalid calls. Omitted transformer classes select all supported transformers; the harness continues to observe every supported fit. Recovery remains within the existing 15-call and 400,000-token limits and does not bypass the evidence gates.

`submit_verdict` accepts only retained primitive IDs and source line ranges. It computes the allowed verdict from primitive outputs, includes all retained measurements, and rejects contradictory model submissions. Generated probe output is exploration only. A fresh remote primitive replay is required; mismatches invalidate the submitted verdict. Immutable image/source hashes identify which implementation produced a record. Unsigned hashes do not prove external authenticity.

The baked trusted inventory includes `source_analysis.py` and `checkpoint.py` alongside the checker, fit tracer and primitive dispatch. The app uses a matching image from `.data/primitive-v2/environment.json`, or an explicit image override that must pass provenance checks. V2 evaluation snapshots archive all application modules, prompt, tool schemas and protocol. The preserved v1 experiment remains a failed historical result; known-case regressions and any future unseen acceptance have separate outputs.

The UI labels historical free-form results as legacy, displays trusted measurements separately from exploration, and exposes unsupported categories under the October 8 fallback. The local fixed CSV audit workflow remains available. The following sections retain its earlier implementation history.

# Asterisk local research preview

## Per-audit Sandbox integration — 17 September 2026

Sandbox execution is now wired into the accepted-rule API and browser workflow. Local execution remains the default. An unchecked control on each review screen authorizes sending that audit's full input files to Nebius; the server rejects a remote request without explicit upload confirmation. No `.env` default was changed. This supersedes the standalone-only status below.

The trusted captured checker runs in a disposable Python 3.12 sandbox with JSON stdin, a 30-second run timeout, and a bounded SDK wait. Credentials are not supplied to the sandbox process. A local replay must exactly match the remote output before completion. Errors remain retryable in review; completed retries do not rerun; deleted audits are not resurrected by an in-flight check. This is a single-process local preview, not distributed job coordination.

Runtime provenance is visible and exported; the evidence ZIP retains the executed program under its hash manifest. Image tags and unsigned hashes do not attest to an immutable remote environment. This still uses a fixed deterministic checker, not an agent writing arbitrary research code.

Validation: 57 automated tests pass, including consent enforcement, default-local behavior, invalid/truncated/mismatched responses, sanitized SDK failures, retries, concurrent requests, deletion during execution, and export reproduction. A deliberately weakened mismatch guard caused the regression test to fail before restoration. A live browser audit used Nemotron and Sandbox execution, found the expected 16 shared synthetic specimens, and its exported evidence reproduced exactly offline. The live clean control found zero shared entities and its export also reproduced exactly. Local evidence: `.data/sandbox-integration-live/verification.json` and `.data/sandbox-integration-live/clean/verification.json`.


## Sandbox execution verified — 17 September 2026

The activation email was followed by successful image listing and a disposable remote Python execution using the saved key/project. This supersedes earlier 403 and pending-access notes below. `scripts/smoke_sandbox.py` ran on `python:3.12-slim` (Python 3.12.13) with contree-sdk 0.3.6, exit code 0, and correct synthetic overlap counts (one shared entity, two affected test rows). No research files or credentials were passed into the sandbox.

Evidence: `.data/sandbox-checks/20260918T012114592785Z.json` (UTC; 17 September in Denver). This verifies standalone remote execution only. The product is not yet wired to Sandbox execution, and no model-generated code was used in this smoke test.

The installed SDK supports `IAMAuth(token=..., project_id=...)` via `ContreeConfig`. Its canonical environment variable is `NEBIUS_PROJECT_ID`; the smoke script also accepts our existing `NEBIUS_AI_PROJECT` as a compatibility alias. No dependency upgrade or secret-file edit was necessary. Context7 had no matching contree-sdk documentation; the installed implementation was inspected directly.


## Scope and decisions

A researcher supplies a claim, CSV split data, optional mapping data, and supporting documentation. A live NVIDIA Nemotron model proposes a cited independence rule. The researcher accepts the rule, a deterministic engine checks complete inputs, and an evidence bundle can replay the result offline.

Use a single FastAPI process, SQLite, and browser-native JavaScript. This keeps the first end-to-end workflow inspectable, easy to run, and inexpensive to change. There is no existing application stack in this folder to preserve. Avoid a second frontend build process until the interface requires it. SQL queries are parameterized; no model-generated SQL or Python is executed locally.

The persistent unit is an immutable input set plus a proposal, accepted rule, and result. An audit moves from draft to review (or insufficient), then complete. Inference failures leave the draft intact and can be retried. Executing a completed audit returns its recorded result. Each browser gets an opaque HttpOnly session cookie and only accesses its own records. Reopening an audit survives refresh. This is local session isolation, not a public-user authentication system.

Bounds: eight artifacts, 4 MB total UTF-8 content, 20,000 rows per CSV, 80 columns, 16,000 characters per document, 30 audits per browser. These support the initial examples and historical metadata case. Large repositories and concurrent multi-user workloads require a job queue and stronger auth; they are not hidden claims of this preview.

## Trust boundaries

An uploaded artifact can contain misleading instructions, malformed CSV, hostile filenames, or HTML. It must not gain filesystem access, change agent instructions, execute code, expose a secret, or cross session boundaries. Inputs are stored as JSON in SQLite rather than written to user-chosen paths. Filename, body, schema, and CSV limits are enforced server-side. Model citations must exactly match a document; schema fields and join semantics are checked by code. Exact quotation does not establish that a quote supports an interpretation; researcher review remains necessary.

The UI uses textContent for all artifact and model content. A restrictive content security policy, same-origin mutation checks, a custom request header, and loopback host validation protect the local server. It serves only the static directory. Inputs and keys are excluded from version control; credentials remain server-side. The server must remain bound to 127.0.0.1 until deployment authentication and abuse controls exist.

Documentation and the first five CSV rows are sent to Nebius for the proposal. Complete CSV contents stay local in the current executor. UI copy discloses this before inference. A future remote executor must disclose the additional data transfer.

## Sandbox integration findings

Context7 resolves Nebius to the solutions library, not Token Factory's current documentation. Following the official quickstart's live navigation revealed:

- https://docs.tokenfactory.nebius.com/sandboxes/overview
- https://docs.tokenfactory.nebius.com/sandboxes/sdk/python_sdk/getting-started
- https://docs.tokenfactory.nebius.com/sandboxes/sdk/python_sdk/running-commands
- https://docs.tokenfactory.nebius.com/sandboxes/cli/tutorial/installation
- https://docs.tokenfactory.nebius.com/api-reference/sandboxes/images/list-publicly-available-images

The Sandbox endpoint is https://api.tokenfactory.nebius.com/sandboxes. Documented IAM authentication includes a bearer token and a project header. With the user-provided project and saved key, a live image-list request returned HTTP 403: Insufficient permissions: list. No sandbox job was started.

The published packages also differ from the current documentation: installed contree-client 0.4.0 exposes ContreeClient as the synchronous HTTP client; contree-sdk 0.3.6 has an older constructor than the current guide. Do not copy the guide blindly or claim Sandbox integration is working. The Sandbox packages are isolated as optional dependencies; the running preview does not import them.

Next: establish Sandbox permissions; verify the package/client contract and a bounded test run; run the portable checker remotely; retain operation/checkpoint IDs and metrics; clearly display the actual executor. No silent fallback from a requested remote execution to local execution.

## Verification sequence

1. Deterministic overlap, clean, incomplete, ambiguous, and malformed cases.
2. API session isolation, traversal/body limits, provider failure, premature execution, and replayed execution.
3. Export bundle replay, then deliberately tamper with an input and confirm replay fails.
4. Live Nemotron proposal and browser acceptance for overlapping, clean, and insufficient examples.
5. Keyboard, responsive layouts, loading/errors, refresh/history, and literal hostile text rendering.

These are implementation checks, not evidence of superiority over a baseline agent. The 12-case pilot and controlled baseline comparison in the project idea remain required before competitive-performance claims.

The rule-review interface treats selected executable fields and literal citations separately from model prose. Fixed scope copy explains what the checker establishes. Raw generated explanations and caveats are preserved under Unverified model notes; source matching does not validate their meaning.

Sandbox authentication follow-up: the [official authentication guide](https://docs.tokenfactory.nebius.com/sandboxes/cli/tutorial/installation) accepts NEBIUS_API_KEY plus NEBIUS_AI_PROJECT. The [profile guide](https://docs.tokenfactory.nebius.com/sandboxes/cli/tutorial/configuration) distinguishes authenticated tokens from projects that lack Sandbox permission. The current 403 does not establish whether the missing permission is caused by account entitlement, project configuration, or token scope. No access rights were changed. Ask the project administrator or Nebius to verify Sandbox access for the supplied project; do not request broad administrative permissions speculatively.

## Researcher corrections

Corrections are append-only child audits, not mutations of an existing proposal/result. `revision.parent_id` links the source, with a kind and correction note. Rule revisions preserve the original `proposal` and `inference`, store the researcher contract in `reviewed_rule`, and return to review with no result. Execution and ZIP export select `reviewed_rule` when present, otherwise the original proposed rule; existing records remain compatible. Input revisions clone the submitted input set and begin at draft with no inherited inference. Every new endpoint checks the browser owner through the existing object access guard. New-record quota and insert use one SQLite write transaction.

Rule edits reuse the literal citation and full contract validation path. Schema-valid fields do not establish scientific suitability, so acceptance remains explicit. Revision creation is intentionally non-idempotent in this local preview: explicit repeated submissions may create separate recoverable records, bounded by the quota; buttons are disabled during requests. Public deployment should add submission idempotency and authentication. Unsaved editor state is local and discarded on navigation, as disclosed in the form.

## Evidence versioning and revision comparison

The process captures its imported audit engine source at startup; new completed records store that source and its SHA-256 fingerprint. Source is excluded from normal API responses, retained in the local record, and included in exported bundles. Exports verify the stored source hash. Legacy records without source are never relabeled as original captures: the current engine must reproduce their entire result, otherwise export fails with 409. Compatible legacy exports explicitly mark revalidation at export time.

Evidence v2 includes a manifest of UTF-8 file hashes. The standalone verifier checks the manifest before importing the bundled checker and uses explicit result comparisons instead of assertions, so Python -O does not disable validation. This provides integrity relative to an unsigned manifest and replay, not an authenticity attestation.

Revision comparisons read both records through owner checks. File differences use full-content SHA-256 hashes; fields come from the effective rules. Missing measurements remain null, partition-label ordering is normalized for comparison, newly available rules are distinguished from changed executable contracts, and the UI warns against causal/performance interpretation. A deleted parent returns a normal unavailable-record error while the child remains accessible.
