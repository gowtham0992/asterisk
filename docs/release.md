# Release and rollback

Asterisk is a single-process research preview. Use the ladder profile below for the current product. Human usefulness remains unmeasured. Dated deployment observations are retained in the [AWS records](operations/aws-deployment.md); they are historical records rather than a live release pointer.

## Current ladder deployment

For the independence-ladder workflow, set `ASTERISK_HOSTED_WORKFLOW=ladder` before running `sh scripts/start_hosted.sh`. The launcher still requires the exact hostname, preview password, persistent database path, Nebius API key and project ID described below. Public authentication and session isolation are unchanged.

This profile does not require `ASTERISK_PROBE_IMAGE` or `ASTERISK_PROBE_DRIVER_SHA256`: ladder replay sends the installed checker source and approved inputs to a disposable `python:3.12-slim` Sandbox and compares its output with the local measurement. Sandbox access is still required for replay. It does not remove the legacy screens or enable their remote execution without their own image configuration. Use `/static/ladder.html` for a new ladder and `/#ladders` for saved receipts.

The default `ASTERISK_HOSTED_WORKFLOW=legacy` preserves both baked-image startup checks. Unknown profile names fail startup. Select that profile when offering the historical single-binding workflow; its image instructions follow.

The launcher profiles were exercised locally with a fake interpreter: ladder configuration reaches the server command without a legacy image, missing required settings fail, and the default legacy profile rejects a missing image or driver. This does not verify a cloud proxy, persistent disk, credentials or live provider execution.

`tests/test_ladder_public_lifecycle.py` additionally runs the real app in public mode in two separate Python processes against one temporary SQLite database. It verifies authentication, Secure/HttpOnly/SameSite cookie settings, exact-host rejection, CSRF rejection, save/reopen/export, isolation between authenticated owner sessions, and deletion of the receipt and its retained inputs. Requests use an HTTPS TestClient origin, not a real TLS proxy. No provider calls occur.

## Legacy single-binding installation and image

Use Python 3.14 and `requirements.lock.txt`. Store `NEBIUS_API_KEY` and `NEBIUS_PROJECT_ID` in the host secret manager; Sandbox access is required. No credentials belong in an artifact.

For a fresh host, create the base scientific image with `evaluation/probe-pilot/bake.py`, then inspect the exact trusted source upload inventory with `evaluation/primitive-v4/bake.py`. After inspecting it, `evaluation/primitive-v4/bake.py --execute` bakes a matching immutable image and records `.data/primitive-v4/environment.json`. These scripts use the existing SDK and are exercised on the development machine. Supply both `ASTERISK_PROBE_IMAGE` and `ASTERISK_PROBE_DRIVER_SHA256` if moving the image ID to another installation with the same account. The configured driver hash must equal the installed `sha256(DRIVER)`. Each remote launch also hashes the actual image driver before execution; stale driver bytes fail closed. Primitive output is separately checked against the installed measurement implementation. Image availability is account-specific.

The historical single-binding workflow uses Super only, requires a confirmed binding before execution and offers only entity overlap. The ladder workflow offers Super and Ultra and measures multiple identity levels. Start locally with `sh scripts/start_preview.sh`.

## Host configuration

Use one worker and one replica, an HTTPS reverse proxy, a persistent SQLite disk and a protected credential store. Set:

- `ASTERISK_PUBLIC=1`
- `ASTERISK_ALLOWED_HOSTS` to the exact hosted domain, no wildcard
- `ASTERISK_PREVIEW_PASSWORD` to a random value of at least 24 characters; username `reviewer`
- `ASTERISK_DB` to an absolute persistent-disk path
- `NEBIUS_API_KEY`, `NEBIUS_PROJECT_ID`
- `ASTERISK_HOSTED_WORKFLOW=ladder` for ladder replay, or `legacy` (default) with both `ASTERISK_PROBE_IMAGE` and `ASTERISK_PROBE_DRIVER_SHA256`

Use `sh scripts/start_hosted.sh`. The platform must terminate HTTPS, preserve scheme/host, and restrict direct ingress to its proxy. Configure `FORWARDED_ALLOW_IPS` with the actual proxy addresses; never blindly trust arbitrary forwarding headers. Public mode uses Secure, HttpOnly, SameSite Strict session cookies, exact host validation and shared preview authentication. This is not a multi-tenant production identity system.

The `/healthz` endpoint checks the database without paid inference. Keep an uptime check on it and monitor failed/stuck receipts and provider usage. Interactive ladder calls have persisted daily call reservations and an in-flight session limit; saved receipts have count and payload-size limits. These are not a dollar-cost guarantee. See the [AWS configuration records](operations/aws-deployment.md) when operating that preview.

## Same artifact and tested rollback

Build `artifacts/asterisk-source.zip` using `scripts/package_release.py`. Deploy the exact tested archive. Its allowlist excludes `.env`, local databases, research data and private transcripts. Keep the previous archive and manifest.

Stop new work and wait for in-flight jobs before deployment. Back up SQLite using its backup API. Replace code, preserving the current database and external secrets. On failure, restore the previous code and its matching Sandbox image; do not restore an older database over new user records. In-flight jobs interrupted by restart remain explicit interrupted records.

Release checks: healthy database; correct auth/host behavior; isolation between two sessions; fresh-browser synthetic receipt from proposal through confirmed binding, result and export; byte verification; recorded matching Sandbox replay; refresh during and after execution. Rollback checks must load the same records before and after code reversal. A local compatibility check does not prove the host's proxy, disk or deployment mechanism.

The AWS preview has recorded proxy, TLS, persistence and rollback checks. Recheck the running release and operational configuration before any new deployment; dated observations do not establish current health.

## Rights and public source

The default public artifact includes application source under MIT, tests with original synthetic fixtures and implementation docs. It excludes the authored third-party dataset packet, model transcripts and private evaluation records. The review reports aggregate measurements and limitations only. Before adding any real dataset to the hosted demo or public repository, retain its source URL, revision, license and required attribution and verify the projected fields are permitted. Do not assume a tool repository's license covers external notebooks or datasets.

A local source package is not evidence of a successful deployment. Verify the deployed bytes and live access boundaries separately.

## Frozen preview operating limits

Do not enable `ASTERISK_LEGACY_AUDITS` for the judge preview. The historical API is read-only by default. The historical investigation workflow has a process-wide lock; a busy operation can return 409 to another reviewer. The ladder workflow separately limits provider operations per session. These bounds do not establish production multi-user capacity.

Build review packets with `scripts/build_review_packet.py` from an allowlisted release ZIP. It verifies source hashes, runs tests in a separate disposable copy, and archives only the original verified bytes. Test-created databases, credentials, caches and modified files cannot enter the output. The earlier September 18 review ZIP contained an empty test-created database and is retained only as a historical artifact; do not redistribute it as the current release.

Session-cookie expiry does not delete server-side session records. This preview has no automatic server-side session-retention policy. Treat access as a scheduled, invited session, protect the database, and arrange explicit record retention/deletion with participants. Shared preview authentication and owner isolation are not individual account management.
