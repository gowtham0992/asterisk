# Preparation reliability pass — 7 October 2026

## Shipped

Proposal rejection now distinguishes empty replies, duplicate JSON keys, and level-only transforms placed in source sample expressions. The last diagnostic names the bounded JSON path, such as `sources[0].sample` or `.lookup.on`, and explains that `field`/`characters` belong to level expressions. It runs only after the trusted population parser has rejected the source. It does not accept or rewrite a response and does not echo input values or unknown key names. Shipping v4 system-prompt bytes and the trusted measurement engine are unchanged.

Both pre-measurement proposal review and the assumptions shown before confirmation now display input-to-unit examples for round-trippable two-level definitions. The first six source rows are shown, explicitly including excluded rows and explicitly without an independence verdict. Missing/conflicting lookup values stay unmapped. Unsupported multi-level definitions, format/name mismatches and parse failures display an unavailable-preview explanation rather than invented values. Text previews now handle CRLF and CR line endings without retaining newline characters in identifiers. The existing complete rule review remains available.

## Fixed development comparison

The v7 candidate appended a source-sample and claim-level reminder to v4. The protocol, 24 requests, inputs and reference definitions were frozen before inference. Six exposed cases, two trials each, two arms; this is builder-authored development evidence, not held-out acceptance or human usefulness. Inputs were the previously observed UCF101 identifier-only lists plus original synthetic filename, mid-identifier, lookup, absent-actor and denied-specimen cases. No videos, personal fields, Sandbox calls or hosted judge requests were used.

| Metric | v4 | v7 |
| --- | ---: | ---: |
| First-call structurally valid | 9/12 | 10/12 |
| First-call semantically correct | 7/12 | 10/12 |
| Ultimately semantically correct | 7/12 | 11/12 |
| Rejected model replies | 5 | 2 |
| Wrong binding yielding pending no-overlap | 1 | 0 |
| Provider calls, including repairs | 15 | 14 |
| Returned total tokens | 59,637 | 58,564 |

Correctness compared every sample-to-unit mapping and partition, not just the overlap count. Both arms correctly abstained on all four absent/denying-control attempts. One v4 UCF101 response dropped the action namespace and returned only `gY`; the group count was wrong although the overlap headline remained zero. This was a pending, unconfirmed result, not a confirmed definitive verdict. One v7 UCF101 response was empty and its repair abstained despite the supplied naming definition. Therefore v7 failed the precommitted gate requiring both UCF101 first calls and all supported final attempts to be correct. **Do not promote v7.** No post-result retries were made.

The total conservative token estimate was **$0.1773015**, treating all returned tokens as output tokens, under the $1 study cap. This is not a provider bill. All 29 calls returned and all 24 attempts were recorded. Raw requests, responses, source files and budgets remain private under `.data/ladder-source-grammar-v7-20261007/` and are excluded from releases.

Scoring correction: the frozen runner's original `complete` flag incorrectly conflated invalid model output with incomplete inference. A separate scorer now identifies completed inference from the captured call trace while counting rejected model output as failures. The original summary, runner hash and exact frozen application bytes are retained; labels and thresholds did not change. Both original and corrected scoring reject promotion. A preflight-only freeze was replaced to remove dead code before any inference; both preflight artifacts are retained privately.

## Verification

- 615 product Python tests passed, 9 skipped; 183 JavaScript tests passed. Four research scorer tests passed separately.
- Regressions were observed failing before the error-message and preview changes. The original bad UCF101 response still rejects; its retained correct repair still accepts.
- Browser test used a local isolated database, the actual product UI and a retained wrong response; live inference and Sandbox execution were disabled. Review showed `g08`; correcting the field range to 2–3 showed `ApplyEyeMakeup_g08`, 1,818 training groups and 707 evaluation groups. Measurement stayed pending confirmation, with the corrected examples above an unchecked confirmation checkbox. This is an agent-operated fixture test, not a human session or another live model success.
- Neither the candidate nor the new diagnostics establish improved general preparation accuracy. The shipped retained acceptance result and absence of human usefulness evidence remain unchanged.
