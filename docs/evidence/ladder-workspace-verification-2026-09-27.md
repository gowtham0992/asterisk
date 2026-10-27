# Ladder workspace verification — 27 September 2026

The independence ladder now persists as an owner-scoped workspace receipt. Both local measurement and the proposed-ladder flow offer Save to workspace; a successful Sandbox replay records its server provenance automatically. Saved receipts can be reopened, exported as HTML or JSON, and deleted with their inputs.

## Boundaries

Saving recomputes the measurement on the server; clients cannot supply a verdict or execution provenance. Local receipts explicitly say no Sandbox replay is recorded. Meaning confirmation is self-reported, not verified reviewer identity. Stored inputs remain private to the owner session. Exports contain measurements, witnesses, spec and hashes, but do not embed full input tables or upstream model proposal history. They are unsigned presentations, not authenticity certificates, and are distinct from the single-binding evidence ZIP.

If storage fails after a paid replay succeeds, the successful result remains available for download; the UI does not require another replay.

## Verification

- Working source Python suite: **556 passed, 9 skipped**, three dependency/lifecycle deprecation warnings.
- Clean source archive extracted outside the checkout: **556 passed, 9 skipped** using the existing virtualenv dependencies, not a new dependency installation.
- JavaScript suite from that extracted source: **164 passed**.
- All **412 source manifest entries** in the tested archive matched their bytes. This report was added afterward; the final package has one additional documentation file.
- Regression coverage includes owner isolation, CSRF, rejected client verdict/provenance fields, HTML escaping, preserved pending confirmation, corrupted record rejection, replay provenance, and successful replay surviving storage failure. Provider execution in these regression tests is mocked.
- Browser: fictional local example measured, saved, listed, reopened, and exported as readable HTML. The receipt distinguishes zero shared scans from two shared subjects. The downloaded HTML contains no executable script and states that execution was local.
- Narrow viewport: 375px page width, no horizontal overflow. No browser console errors observed.
- No paid inference or Sandbox calls were made for this integration.

## Commit scope and remaining work

The user authorized committing the current product plus this integration, excluding credentials, raw research data and experiment records. Files are selected through the source release allowlist: application, tests, scripts, product documentation, fictional examples, and public derived gallery summaries. Private datasets, databases, model replies and experiment run packets are excluded. No push or deployment is part of this change.

The local preview runs at http://127.0.0.1:8792 with an isolated synthetic-test database. Hosting, public repository visibility, video, final submission, and evidence from real human readers remain separate work. These checks establish implementation behavior, not researcher demand or hackathon competitiveness.
