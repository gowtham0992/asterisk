# V4 release and rollback

This is an invitation-only, single-process research preview. Human utility and fresh v4 acceptance remain unmeasured. A public deployment has not happened; provide a hosting destination and public repository owner before claiming otherwise.

## Install and image

Use Python 3.14 and `requirements.lock.txt`. Store `NEBIUS_API_KEY` and `NEBIUS_PROJECT_ID` in the host secret manager; Sandbox access is required. No credentials belong in an artifact.

For a fresh host, create the base scientific image with `evaluation/probe-pilot/bake.py`, then inspect the exact trusted source upload inventory with `evaluation/primitive-v4/bake.py`. After inspecting it, `evaluation/primitive-v4/bake.py --execute` bakes a matching immutable image and records `.data/primitive-v4/environment.json`. These scripts use the existing SDK and are exercised on the development machine. Supply both `ASTERISK_PROBE_IMAGE` and `ASTERISK_PROBE_DRIVER_SHA256` if moving the image ID to another installation with the same account. The configured driver hash must equal the installed `sha256(DRIVER)`. Each remote launch also hashes the actual image driver before execution; stale driver bytes fail closed. Primitive output is separately checked against the installed measurement implementation. Image availability is account-specific.

The product uses Super only, requires a confirmed binding before execution and offers only entity overlap. Start locally with `sh scripts/start_preview.sh`.

## Host configuration

Use one worker and one replica, an HTTPS reverse proxy, a persistent SQLite disk and a protected credential store. Set:

- `ASTERISK_PUBLIC=1`
- `ASTERISK_ALLOWED_HOSTS` to the exact hosted domain, no wildcard
- `ASTERISK_PREVIEW_PASSWORD` to a random value of at least 24 characters; username `reviewer`
- `ASTERISK_DB` to an absolute persistent-disk path
- `ASTERISK_PROBE_IMAGE`, `ASTERISK_PROBE_DRIVER_SHA256`, `NEBIUS_API_KEY`, `NEBIUS_PROJECT_ID`

Use `sh scripts/start_hosted.sh`. The platform must terminate HTTPS, preserve scheme/host, and restrict direct ingress to its proxy. Configure `FORWARDED_ALLOW_IPS` with the actual proxy addresses; never blindly trust arbitrary forwarding headers. Public mode uses Secure, HttpOnly, SameSite Strict session cookies, exact host validation and shared preview authentication. This is not a multi-tenant production identity system.

The `/healthz` endpoint checks the database without paid inference. Keep an uptime check on it and monitor failed/stuck receipts and provider usage. Evaluation-ledger limits do not automatically cap interactive preview usage. Configure provider spending limits before opening judge access.

## Same artifact and tested rollback

Build `artifacts/asterisk-source.zip` using `scripts/package_release.py`. Deploy the exact tested archive. Its allowlist excludes `.env`, local databases, research data and private transcripts. Keep the previous archive and manifest.

Stop new work and wait for in-flight jobs before deployment. Back up SQLite using its backup API. Replace code, preserving the current database and external secrets. On failure, restore the previous code and its matching Sandbox image; do not restore an older database over new user records. In-flight jobs interrupted by restart remain explicit interrupted records.

Release checks: healthy database; correct auth/host behavior; isolation between two sessions; fresh-browser synthetic receipt from proposal through confirmed binding, result and export; byte verification; recorded matching Sandbox replay; refresh during and after execution. Rollback checks must load the same records before and after code reversal. A local compatibility check does not prove the host's proxy, disk or deployment mechanism.

Hosting, proxy configuration, public-domain TLS, judge access and production rollback remain pending a destination. Keep the service available through the judging period; verify the event's schedule discrepancy before release and plan conservatively for access starting 2 November.

## Rights and public source

The default public artifact includes application source under MIT, tests with original synthetic fixtures and implementation docs. It excludes the authored third-party dataset packet, model transcripts and private evaluation records. The review reports aggregate measurements and limitations only. Before adding any real dataset to the hosted demo or public repository, retain its source URL, revision, license and required attribution and verify the projected fields are permitted. Do not assume a tool repository's license covers external notebooks or datasets.

The public remote, actual hosted URL, YouTube video and Devpost submission remain external actions. Local prepared files are not evidence those actions occurred.

## Frozen preview operating limits

Do not enable `ASTERISK_LEGACY_AUDITS` for the judge preview. The historical API is read-only by default. One process-wide investigation lock serializes planning, execution and confirmation across sessions; a busy process can return 409 to another reviewer. Schedule the two sessions separately. This is appropriate for an invited preview, not a claim of concurrent multi-user capacity.

Build review packets with `scripts/build_review_packet.py` from an allowlisted release ZIP. It verifies source hashes, runs tests in a separate disposable copy, and archives only the original verified bytes. Test-created databases, credentials, caches and modified files cannot enter the output. The earlier September 18 review ZIP contained an empty test-created database and is retained only as a historical artifact; do not redistribute it as the current release.

Session-cookie expiry does not delete server-side session records. This preview has no automatic server-side session-retention policy. Treat access as a scheduled, invited session, protect the database, and arrange explicit record retention/deletion with participants. Shared preview authentication and owner isolation are not individual account management.
