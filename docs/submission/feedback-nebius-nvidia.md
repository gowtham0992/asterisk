# Feedback on Nebius Token Factory, Sandboxes and NVIDIA Nemotron

Draft for the feedback submission; not sent. The most useful improvement for Asterisk is better conversion of explicit documentation into a bounded extraction rule. Our current implementation uses Nemotron 3 Super through Token Factory, validates the proposed JSON, permits one repair, then measures with application code and optionally replays in a Nebius Sandbox.

## 1. Explicit identity rules are often declined

In [set A](../../evaluation/ladder-proposal-v2/RESULTS.md), Super abstained on 30 of 33 replies, including documentation that states how subject numbers appear in filenames. Across the four development sets, tested Super configurations scored 21/41, Ultra 24/41 and the Sonnet comparison 36/41. These are bounded, developer-authored evaluations with differing prompts and correction opportunities—not an overall model ranking or a claim about private training data.

**Request:** add evaluation and training examples where a model must translate an explicit naming convention into typed extraction: basename, delimiter field, character range or a provided lookup. Include exceptions requiring a mapping table or refusal. Correct JSON alone does not establish the right grouping.

## 2. The output language changes what the model can solve

Our initial prompt left the grammar implicit. Super returned 40 invalid replies out of 54 in [the first development run](../../evaluation/ladder-proposal-v1/RESULTS.md). That result primarily tested our underspecified contract.

Later, adding character-range and delimiter-field expressions increased Super from 3/10 to 5/10 on set D. The shipping v4 prompt still failed its pass rule. [Set-D results](../../evaluation/ladder-proposal-v5/RESULTS.md) also record seven invalid first attempts, six due to out-of-range citations; one repair fixed six of the seven.

**Request:** provide a worked documentation-to-JSON example that includes exact field types, line-range validation, missing-definition behavior and one repair using the validator's actual error. Include guidance on completion-token budgets for this pattern. Our app uses a fixed maximum and disables SDK automatic retries so application behavior stays bounded.

## 3. Provider delays need a bounded failure mode

[Set D](../../evaluation/ladder-proposal-v5/RESULTS.md) records three Ultra connection-error attempts lasting about 270 seconds each, plus an earlier request that stalled for about 25 minutes before the process was stopped. Failures remained failures under the protocol. Those evaluation settings and observed durations are not the hosted app's current timeout settings.

**Request:** return an actionable bounded timeout with a correlation identifier, and document how client timeouts interact with server work. A research workflow must be able to say execution is incomplete rather than leave the user guessing whether it finished or will be billed.

## 4. Sandbox provenance should retain the operation identifier

The installed `contree-sdk` 0.3.6 implementation starts an operation and waits using its UUID, but the returned image-run object does not retain that UUID. We inspected the installed SDK, not a guarantee about every SDK version. Our 28 September hosted replay matched the local checker on a fictional example; the receipt explicitly describes that as server-attested reproducibility.

**Request:** expose the operation UUID in the successful run result, alongside the image and execution metadata, and document its retrieval/verification lifetime. That would improve traceability. It would not, by itself, authenticate an unsigned receipt or establish the scientific meaning of an identity column.

## What worked

Token Factory made the actual Nemotron proposal available through the OpenAI-compatible client, and a fresh Sandbox ran the same checker for exact-result comparison. The hosted fictional proposal → measurement → replay → saved/exported receipt chain completed in 10.29 seconds on 28 September, using one Super call and one Sandbox run. That is integration evidence on one example; researcher usefulness and general preparation reliability remain unmeasured.

## Evidence inventory

- [Initial malformed-reply run](../../evaluation/ladder-proposal-v1/RESULTS.md).
- [Set A and abstentions](../../evaluation/ladder-proposal-v2/RESULTS.md).
- [Set D, repairs, timeouts and combined scores](../../evaluation/ladder-proposal-v5/RESULTS.md).
- [Hosted smoke and scope](release-review-resolution-2026-09-28.md).
- Installed-code paths: `app/ladder_api.py` (bounded client call), `app/ladder_proposal.py` (validator and repair), `app/ladder_sandbox.py` (replay attestation).

The source release includes reports and application code. Private run packets, full model replies and provider credentials remain excluded. These observations describe the recorded versions and runs; they do not assert that today’s provider documentation lacks every requested feature.
