# Judge testing instructions — hosted preview

Asterisk checks whether a train/test split separates the identity level required by a research claim. The model proposes how to recover identities from documentation; application code computes overlap and retains source-row evidence.

**Hosted workspace:** https://asterisk.gowthamsarveswaran.com/static/ladder.html#propose (dedicated judge login required). Supply judge credentials separately in Devpost’s testing instructions, never in source. Repository: https://github.com/gowtham0992/asterisk. The owner is keeping it private until closer to submission. All published source is on `main`; the landing page is in `site/`. GitHub Pages is unavailable while the repository is private under the current plan. Use the hosted workspace directly.

**Release status, 28 September:** review hardening is deployed; the packaged source hashes match the installed runtime. The hosted fictional model → measurement → Sandbox replay → saved receipt/export smoke passed. The public repository and video are still pending.
## First look: a real finding without a model call

Open **Benchmarks** in the hosted workspace. Its WSI-Bench figure is a saved measurement from pinned public files: zero shared slides but 42 shared patient identifiers, affecting 43 of 208 evaluation rows. The gallery shows recorded measurements and source-row witnesses. This is not a newly executed Sandbox receipt.

The distinction matters when a claim requires unseen patients. The finding does not, by itself, establish a performance penalty or make every use of this split invalid.

## Try the application

1. Open the hosted workspace URL above and sign in using the separately supplied judge credentials.
2. Select **Load real benchmark** to use the installed identifier-only WSI-Bench projection, or select **Try a synthetic example**. This loads a fictional slide dataset and its documentation; no personal research data are required.
3. Select **Preview what will be sent**. Inspect the model payload. No inference has happened yet.
4. Send the preview to the selected Nemotron model through Nebius Token Factory. This is the live model step. It can return a proposal, require correction, or abstain.
5. If a usable proposal appears, review every raw partition label → role mapping, counts, exclusions, derivation rule and citation, then select **Measure on server**. This runs on the application server, outside the Sandbox. The model's text is not accepted as a measurement.
6. Inspect the patient level and a source-row witness. The fictional documentation defines the patient as the first 11 characters of the slide name. Different slide identifiers can therefore refer to the same patient. Confirm meaning only when the documentation supports it; absence of overlap alone does not establish independence.
7. Optionally select **Replay in a Nebius Sandbox**. A successful replay recomputes the measurement on separate infrastructure and requires the result to match. A failure remains a failure; it must not be described as a match.
8. Select **Open saved receipt** after successful replay, or **Save to workspace** after a local measurement. Reopen the record from the workspace's Independence ladders list and download HTML or JSON. Local-only execution is labeled separately from a matched replay.

If the model cannot establish an identity definition, inspect the missing information rather than expecting an automatic pass. Select **Define the unit yourself** to continue without a model. A manually supplied definition is a user action, not evidence that the model succeeded. Choose the documentation and line range explicitly.

## Try the confirmation path without inference

Expand **Advanced → Measure a ladder spec you wrote yourself** and select **Load subject-disjoint example**, then **Measure on server**. This is fictional data and a supplied specification. The result should say no shared values, with confirmation pending. Review the derivation, test-label mapping and population before ticking the confirmation. Confirm and measure again, save the result, and open its readable receipt. It should identify a confirmed claim and user-supplied specification, without claiming a model call or Sandbox execution. The overlapping-subject example beside it should produce a violation.

Dedicated `judge` credentials use the cumulative reserve described in [judge access](judge-access-2026-10-07.md), without the preview daily caps. The UI shows remaining calls. Preview credentials still use daily limits. Provider limits may return 429. They preserve manual measurement and receipt access; do not repeatedly retry or create new sessions to evade them. Defaults reserve 10 calls per session and 100 globally per UTC day; proposals reserve two calls and replays one. Receipts are capped at 30 per workspace.

## What to assess

- Can you identify the exact research claim and the identity level it depends on?
- Do the cited definitions support the chosen extraction rule?
- Can you follow an overlap witness back to the recorded training and evaluation rows?
- Does the receipt make its execution mode, meaning confirmation and unmeasured questions clear?

The receipt is unsigned and does not certify scientific validity. The public page does not accept uploads; files are handled by the separate workspace. Workspace sessions are isolated, but shared preview login is not individual account management.

## Evidence and limitations

The recorded evaluation covers 41 cases across different tested configurations. Super proposed 21 ladders correctly, Ultra 24 and Sonnet 36. Guarded model runs produced zero false reassurance on those cases, not proof of perfect preparation or future safety. The shipping v4 Super prompt scored 5/10 on set D and failed that set's pass threshold. Real researcher usefulness and time saved remain unmeasured.

Local verification of the source archive at commit `1e2ab4c`: 569 Python tests passed, 9 skipped, and 164 JavaScript tests passed. The clean extraction reused installed dependencies. This does not establish cloud TLS, credential validity, service availability, or a successful live provider run of the final hosted build.

Hosted checks on 27 September verified TLS, preview authentication, session isolation, fictional measurement/save/export, backup restore and restart persistence. AWS-to-Nebius catalog authentication passed. A subsequent shipped fictional example passed one live Nemotron call, one fresh Sandbox replay with exact match, saved receipt and HTML export in 11.95 seconds. The 28 September hardened build repeated that chain in 10.29 seconds, including recorded model provenance. These are deployment checks, not accuracy evaluations.
