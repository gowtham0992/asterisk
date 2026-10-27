# AWS workspace deployment — 27 September 2026

Workspace: https://asterisk.gowthamsarveswaran.com/static/ladder.html#propose

This is a password-protected research preview. Username: `reviewer`. The generated password is stored locally in `.data/deployment/preview-password.txt` (mode 0600); never include it in the public repository. Supply it separately in judge testing instructions. A subsequent live hosted smoke test used the shipped fictional example: one Nemotron call and one fresh Sandbox replay, recorded below.

## Installed infrastructure

- AWS Lightsail `asterisk-workspace`, us-east-1a, Ubuntu 24.04, `small_3_0`: 2 GB RAM, $12/month base charge, plus applicable taxes and Nebius usage. No paid add-ons were enabled.
- Attached static IPv4: `54.197.129.253`. Cloudflare DNS-only A record `asterisk` points there. Existing domain records were unchanged.
- nginx terminates HTTPS; HTTP redirects to HTTPS. Let's Encrypt certificate expires 26 December 2026; certbot renewal timer and nginx reload hook are installed.
- HTTPS/HTTP public; SSH restricted to the deployment client’s two observed IPv4 /32 addresses. If that address changes, update the instance firewall using `nebius`; do not widen SSH to the entire internet.
- Dedicated `asterisk-deploy` role: hosting inspection in us-east-1 and lifecycle/firewall/access operations on this instance only. No IAM administration or modification of Kin/Mettle resources.
- systemd runs the app as `asterisk`, one worker, with read-only application code, writable persistent data, automatic failure restart, and the ladder hosting profile.
- Runtime credentials: `/etc/asterisk/runtime.env`, root-only. systemd injects them into the service. No credentials were shipped in the source archive.
- SQLite: `/var/lib/asterisk/asterisk.sqlite`. Daily verified backups in `/var/lib/asterisk/backups`, seven copies retained. These are same-server backups, not protection against losing the server/disk.

## Installed artifact and verification

Initial release directory: `/opt/asterisk/releases/20260927-da4301f`, retained for rollback. The current symlink points to `/opt/asterisk/releases/20260927-3df6961` after the disclosure update below.
Source archive SHA-256: `adf8f0219b349918be4fbf571f5d2c957ffb799353639b2e0c281f6413040317`.
All 421 release manifest entries matched installed bytes, checked as the service user.

A fresh dependency installation on Ubuntu passed 568 Python tests, with 10 skipped and three deprecation warnings. Compared with the local run's nine skips, the additional skip is the Node-dependent ladder builder contract test; Node is not installed on this Python server. Tests ran in a separate extracted directory, without provider credentials, not in the installed source tree.

Public HTTPS verification passed:

- Unauthenticated workspace/API access returns 401; health endpoint returns 200.
- Authenticated session sets Secure and HttpOnly cookie; ladder page and module assets load.
- A fictional dataset measures a violation, saves and exports a receipt.
- Missing request header and foreign Origin are refused; another session cannot retrieve the receipt.
- Saved receipt remains readable after a verified service stop/start; test receipt deleted afterward.
- SQLite backup restored into a scratch database, integrity check passed, saved receipt present.
- Initial-release withdrawal/recovery exercised by stopping the app, confirming its port was unavailable, restarting, and reopening the receipt. This is not a cross-version rollback test.
- After recovery: service active, zero automatic restarts, no error-level journal entries during the check.
- AWS-to-Nebius model catalog returned HTTP 200 and listed the configured Nemotron 3 Super model. This verifies authentication/connectivity. A subsequent full live chain also passed (below).

## Operations and remaining work

Use AWS profile `nebius` for instance management. SSH key and known-host record are local under `.data/deployment/`, excluded from commits/releases. Keep the key private.

Service commands on the host: `sudo systemctl status asterisk`, `sudo systemctl restart asterisk`, `sudo journalctl -u asterisk`. Do not print the runtime environment or include it in diagnostics.

For the initial release, withdrawal is `sudo systemctl stop asterisk`; nginx then reports unavailable and data remain on disk. Recovery is `sudo systemctl start asterisk`. Before later upgrades, retain the previous artifact and exercise a version-switch rollback against a database copy.

The public landing page has been rebuilt locally at `artifacts/public-site-aws` with the real workspace URL. GitHub Pages publication, public source release, video and final Devpost submission remain separate unfinished deliverables. No autonomous monitoring or independent human usability study is claimed.

## Live hosted chain — 27 September 2026

One fixed run of the shipped fictional slide example passed end to end in 11.95 seconds. Nemotron 3 Super used one call, 3,133 total tokens and 9.54 seconds; no repair or rerun was needed. Asterisk measured one shared patient affecting one of four evaluation rows. One fresh Nebius Sandbox run matched the local result exactly, and the server retained a receipt with actual Sandbox provenance and exported its HTML. No meaning confirmation was fabricated; the confirmation list was empty and the outcome was an overlap violation.

Program hash: `1316fb4cf3720cf9f5488f166d3f2728526ebba6c3318d267c6df4f6113cca43`.
Result hash: `28c5239ba11d4e1c3fa73778a4f260ef1cb71ca2cae5d6ff1c5605cfe4e58f3a`.
Private test records and the exported receipt are under `.data/deployment/live-chain/`; they are excluded from the source release and Git. This verifies one hosted example, not model accuracy across datasets or researcher usefulness.

## Hosted disclosure update — 27 September 2026

Release `3df6961` replaces ambiguous “local” wording with explicit server upload and measurement wording. Selecting Preview uploads the selected files to Asterisk; only the displayed subset is subsequently sent to the model. Sandbox replay is a separate upload of the supplied files. The wording appears before these actions. No measurement algorithm, proposal prompt or replay program changed; the program hash still matches the successful live run above.

Focused checks: 12 Python and 9 JavaScript tests passed. All 422 new source manifest entries matched installed bytes. The previous virtual environment is reused because the lockfile is byte-identical; retain the prior release while this virtual environment is referenced.

A real version rollback was exercised: new release → retained `da4301f` → new release. Both versions read the same saved fictional receipt, and the restored new release served the corrected disclosure and export. The test receipt was then deleted. No additional inference or Sandbox calls were used for this update.

Updated archive SHA-256: `03b88521089fd9a870e09d9f17a973850d9908ae88f2d6cc0603d3bd225d44f8`.

## Deployed hardening: provider and receipt limits

The release-hardening code reserves provider calls in the application SQLite database before external execution. Defaults are 10 calls per session and 100 globally per UTC day, configured with `ASTERISK_LADDER_SESSION_DAILY_CALLS` and `ASTERISK_LADDER_GLOBAL_DAILY_CALLS`. One proposal reserves two calls, including its possible repair; a replay reserves one. Failed and unused reservations remain counted. These are conservative call limits, not a provider-billing dollar guarantee. Manual measurement, exports and saved-receipt reads remain available at the cap.

Only one provider operation may be in flight per owner. A crashed operation's lock expires after 30 minutes; daily usage is not refunded. Receipt writes atomically enforce 30 records per owner and 256 MiB of serialized receipt payloads globally. The latter excludes SQLite overhead, proposal metadata and backups. Users can export and delete their saved receipts to release capacity. A successful replay whose save fails still returns its result and warns against spending on another replay.

These limits were deployed with the 28 September hardening and remain in the 30 September release. Their compatibility with unrestricted judge testing is unresolved; see [submission gates](../current-readiness.md).

## Source and presentation sync — 30 September 2026

Hosted release `/opt/asterisk/releases/20260930-dab958b` includes the supported-scope copy, evaluation labels, current first-run instructions and aligned judge materials from GitHub main `dab958b`. All 434 installed hashes were checked as the service user. HTTPS checks compared the three changed product assets with the archive and exercised the fictional pending → confirmed measurement. No additional model or Sandbox calls occurred. Database backup preceded deployment; the previous 28 September release remains available for rollback. Asterisk was active and the backup timer enabled after deployment.
