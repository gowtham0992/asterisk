# Receipt-first restructuring — 23 October 2026

Technical verification record for the receipt-first product workflow. The change preserved the prompt, measurement engine, supported datasets and provider limits.

## Changes

- The default ladder URL and `#receipt` show the saved WSI-Bench result: 0 shared slide IDs, 42 shared patient IDs, 43 affected evaluation rows out of 208. The retained patient witness is expanded with its two different slide names and source references. The patient definition is shown with its recorded source.
- The primary action loads the same pinned identifier-only projection through the existing benchmark endpoint, fills the claim and opens Define. It supplies no reference answer to the proposer and makes no inference or Sandbox call. The current allowance is visible before starting.
- The WSI introductory figure labels site sharing as expected context. This is presentation only; no source measurement, kind, spec, finding or overlap arithmetic changed. Other measured ladders keep their recorded semantics.
- `/public/` serves the existing static introduction without a login: result, witness, recorded quote, limits and a credentials-free local path. Only four exact GET/HEAD paths are exempt from preview authentication. APIs, workspace pages, unlisted paths and mutations remain protected. There is no script, upload form or analytics on the public page.
- The product, public page and README share “Clean by slide. Shared by patient.” The README opens with the audience, result, technology roles and local run. The complete earlier single-binding sections survive in `docs/history/single-binding-readme-2026-10-23.md`, with links adjusted for the new location.
- Super's default is explained using the retained Ultra latency/connection-error observations. The shipping 5/10 result and later unsupported binding are explicit. Historical dated test counts remain historical; the current run is below.

## Verification

Full local suite on this restructuring: **620 Python tests passed, 9 existing scientific-trace skips; 194 JavaScript tests passed**. Existing deprecation warnings remain. Provider calls are mocked in automated tests.

The new public-route regression was observed failing with 401 before the change. It now verifies all four public assets, no session cookie, security headers, and continuing denial of unauthenticated workspace/API/mutation/traversal requests. Builder checks compare the displayed witness and definition with retained source records. Figure checks ensure the contextual label does not mutate the measurement and that failed fetches display an error.

An agent-operated local browser journey verified the saved result, primary-action file loading (9,748 training and 208 evaluation identifier rows), normal review controls, public page, and the credentials-free subject-disjoint example stopping at pending confirmation. No model or Sandbox request was made. Both new pages had no horizontal overflow at 375px and 768px. Desktop was inspected and the landing spacing revised once. This is not human usefulness evidence.

## Deployment boundary

The existing host was inspected before release: `/opt/asterisk/releases/20261009-99844a9`, service active. The deployment preserves preview credentials, judge reserve, storage and the identifier cache. Verify the current release using `sudo readlink -f /opt/asterisk/current` and compare returned asset bytes with the release manifest; do not infer a current hash from older dated readiness sections. The deployment command record is retained privately in `.data/deployment/`.
