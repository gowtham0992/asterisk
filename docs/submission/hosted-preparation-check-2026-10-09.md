# Hosted preparation check — 9 October 2026

The shipped v4 prompt remains unchanged. This change repairs executable validation, not scientific interpretation or the retained 5/10 semantic score.

## Fixed

Proposal validation previously read source populations but did not execute the proposed unit expressions. Missing columns and overlong identifier prefixes could pass validation and fail later. Every level is now derived locally before acceptance; a failure enters the existing single repair turn. Diagnostics identify the level position without sending unshared sample values back to Nebius. Explicit `missing: unmapped` remains supported and does not imply complete coverage.

Both new failure tests were observed failing before the fix and passing afterward. A third test preserves explicitly unmapped inputs. Full verification: 618 Python tests passed, 9 existing skips; 190 JavaScript tests passed.

## Hosted API journey

A fixed, original synthetic audio-recording example was submitted to the hosted application. It contains four fictional clip IDs, three fictional speaker IDs, and three documentation lines, with no personal data. Maximum authorization: two inference calls and one Sandbox call, no automatic retries, $0.10 inference cap.

The normal request headers were required; an initial request without them received 403 before inference. The corrected request used the same Origin and X-Asterisk-Request headers as the application.

Preview, proposal, interpretation review, local measurement, Sandbox replay and HTML/JSON/ZIP export all returned successful responses. Nemotron correctly selected the speaker grouping on its first call (2,582 total tokens, 5.39 seconds). The measured result was zero shared clips and one shared speaker, affecting one of two evaluation rows. The ZIP recomputed successfully from the trusted local installation: matching bytes, engine hashes, witnesses and violation. Synthetic binding confirmation was performed by the test author/agent, not an independent human participant.

The hosted judge allowance reserved three calls and moved from 157 to 154; actual provider use was one inference call and one Sandbox call. Private input, response and receipt records are retained under `.data/hosted-journey-20261009/`, excluded from releases.

## Limits

The in-app browser refused navigation with `net::ERR_BLOCKED_BY_CLIENT`. This was an HTTP/API journey, not a completed hosted browser usability study. No conclusion about realistic preparation accuracy follows from this small synthetic case.

The proposed newer prompt remains rejected under its original promotion criteria. The empty-response/token-exhaustion explanation remains a hypothesis; no undocumented provider controls were enabled.

Real researcher usefulness remains unmeasured. The user confirmed that no recruitment account or participants are available. The hosted comprehension study remains prepared but unpublished; agents are not counted as people.
