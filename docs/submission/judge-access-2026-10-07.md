# Dedicated judge access

The `judge` login uses a separate server-held secret, supplied privately in testing instructions. Client-supplied role headers do not grant it. It can use the ladder workflow; unrelated legacy/preparation APIs are refused. Receipt ownership still belongs to the browser session, not the shared login.

Dedicated access does not use preview session/day caps. Its call reserve is cumulative across days, browser sessions and restarts. Failed calls and unused repair reservations stay counted. It expires after December 15. The workspace shows the remaining reserve before live use. Manual measurement and receipt access remain available when live allowance is unavailable.

The owner approved **$25 total estimated judge inference spending**. At a conservative $0.15 per reserved provider call, 166 calls reserve $24.90. Requests are bounded to 120 KB including repair history and responses to 8,000 tokens. The estimate uses the first-party Nemotron Ultra ceiling of $1/M input and $3/M output; Super is less expensive. A proposal reserves two calls and a Sandbox replay one. This is deliberately conservative, not a provider-billing guarantee: token pricing and Sandbox beta terms can change. Check prices again before the last-week release and before judging. Do not automatically refill or remove the emergency reserve.

First-party price source inspected October 7: https://github.com/nebius/token-factory-cookbook/blob/main/models/nemotron/nemotron3-ultra-550b-a55b.md . There is no new hosting tier or subscription here.

Runtime configuration:

- `ASTERISK_JUDGE_PASSWORD`: distinct random secret, not in Git or docs.
- `ASTERISK_LADDER_JUDGE_TOTAL_CALLS=166`.
- `ASTERISK_LADDER_JUDGE_UNTIL=2026-12-16T08:00:00+00:00` (end of December 15 in Denver).
- `ASTERISK_BENCHMARK_DIR=/var/lib/asterisk/benchmarks`: identifier-only benchmark cache, outside source control.

A funded emergency boundary is still a restriction. The implementation removes the small daily preview bottleneck; it does **not** establish organizer approval of the hackathon's unrestricted-testing clause. No organizer has been contacted. Keep that compliance question explicit rather than calling a finite reserve unlimited.

The repository remains private; the owner plans public source, video and final submission for the last week. No publishing or final submission happens through this change.
