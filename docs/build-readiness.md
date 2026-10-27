# Asterisk — build readiness

**Historical build log.** The dated entries below describe past states and include superseded scope and access failures. For the current product, retained experiments and evidence limits, use [current readiness](current-readiness.md). Do not use this history as deployment or submission status.

## Per-audit Sandbox integration — 17 September 2026

Sandbox execution is now wired into the accepted-rule API and browser workflow. Local execution remains the default. An unchecked control on each review screen authorizes sending that audit's full input files to Nebius; the server rejects a remote request without explicit upload confirmation. No `.env` default was changed. This supersedes the standalone-only status below.

The trusted captured checker runs in a disposable Python 3.12 sandbox with JSON stdin, a 30-second run timeout, and a bounded SDK wait. Credentials are not supplied to the sandbox process. A local replay must exactly match the remote output before completion. Errors remain retryable in review; completed retries do not rerun; deleted audits are not resurrected by an in-flight check. This is a single-process local preview, not distributed job coordination.

Runtime provenance is visible and exported; the evidence ZIP retains the executed program under its hash manifest. Image tags and unsigned hashes do not attest to an immutable remote environment. This still uses a fixed deterministic checker, not an agent writing arbitrary research code.

Validation: 57 automated tests pass, including consent enforcement, default-local behavior, invalid/truncated/mismatched responses, sanitized SDK failures, retries, concurrent requests, deletion during execution, and export reproduction. A deliberately weakened mismatch guard caused the regression test to fail before restoration. A live browser audit used Nemotron and Sandbox execution, found the expected 16 shared synthetic specimens, and its exported evidence reproduced exactly offline. The live clean control found zero shared entities and its export also reproduced exactly. Local evidence: `.data/sandbox-integration-live/verification.json` and `.data/sandbox-integration-live/clean/verification.json`.


## Sandbox execution verified — 17 September 2026

The activation email was followed by successful image listing and a disposable remote Python execution using the saved key/project. This supersedes earlier 403 and pending-access notes below. `scripts/smoke_sandbox.py` ran on `python:3.12-slim` (Python 3.12.13) with contree-sdk 0.3.6, exit code 0, and correct synthetic overlap counts (one shared entity, two affected test rows). No research files or credentials were passed into the sandbox.

Evidence: `.data/sandbox-checks/20260918T012114592785Z.json` (UTC; 17 September in Denver). This verifies standalone remote execution only. The product is not yet wired to Sandbox execution, and no model-generated code was used in this smoke test.

The installed SDK supports `IAMAuth(token=..., project_id=...)` via `ContreeConfig`. Its canonical environment variable is `NEBIUS_PROJECT_ID`; the smoke script also accepts our existing `NEBIUS_AI_PROJECT` as a compatibility alias. No dependency upgrade or secret-file edit was necessary. Context7 had no matching contree-sdk documentation; the installed implementation was inspected directly.


Checked live through Devpost MCP on 17 September 2026 UTC / 16 September in Denver. Product root: `nvidia/asterisk`. This is a planning reference, not an assertion that the project is complete or eligible.

## Project and scope

Devpost project: https://devpost.com/software/asterisk-p4qs38

Verified project ID: 1432165. Name: Asterisk. Tagline: “Check what your benchmark measures”. State: submission_draft; submitted_at is null. Description is empty, video URL is null, and hackathon website URL is null. The account is registered for the event. The account-level “submitted” relationship also appears for drafts and must not be treated as completed submission.

The product brief is at `../asterisk-project-idea.md`. First slice: accept a generalization claim and local CSV/documentation artifacts; propose a cited entity-independence rule; obtain researcher acceptance; execute the audit; return inspectable evidence and unresolved questions. Start with entity leakage. Use the reproduced historical DermaMNIST result as an example, plus independent cases and controls to evaluate the agent.

## Official build requirements and design consequences

Source: https://nebiusglobalaihackathon.devpost.com/rules

> Entrants must create a working software application that runs on either Nebius Token Factory or Nebius AI Cloud and uses at least one NVIDIA open source model

The rules define the runtime requirement as a Token Factory inference API call or deployment/execution using Nebius AI Cloud compute. Our proposed implementation uses Nemotron inference through Token Factory.

The Coding and Agentic Engineering track says:

> Build coding agents and developer tools: agents that write, run, and test code in Token Factory Sandboxes.

Plan for Token Factory Sandbox execution if entering that track. Official Sandbox documentation has been reviewed. The live image-list request returned 403 for the supplied key/project; Sandbox execution is not integrated. Best Apps and Agents is an alternative if the finished workflow better matches that track; do not assume any generic sandbox is equivalent to the named service.

## Deliverables to build toward

The exact requirements and field IDs are retained in `devpost-reference.json`; full legal text is in `official-rules.md`.

- Working demo URL for Asterisk. The form marks the field optional globally because Physical AI has an exception; Asterisk must follow the prose requirement.
- Public GitHub, GitLab, or Bitbucket repository containing source, assets, setup/run instructions, and an open-source license visible on the repository page.
- Public YouTube demonstration. Use a target under three minutes because formal rules say “less than three (3) minutes,” while the overview says three minutes or shorter. Include working footage and narration explaining Nebius/NVIDIA use.
- English submission materials or English translations.
- Judge access free of charge and without restriction until judging ends; supply testing credentials if needed.
- Track, new/existing status, model choice and rationale, and substantive platform/model feedback. Required questions cover quality, prompting/fine-tuning, comparisons, infrastructure, recommendations, inference experience, desired improvements, and future model features.
- Submitter type, organization or N/A, residence, Canadian province or N/A, age and employment declarations. Do not infer these personal answers.
- Tavily-use answer; its bonus requires a functional runtime call. City selection is optional.

## Dates, judging, and discrepancies

Submission deadline: 30 October 2026, 10:00 a.m. Pacific / 11:00 a.m. Denver / 17:00 UTC.

Formal rules give judging as 1–15 December 2026; the dates endpoint gives 2 November–15 December. Both agree on the end date and the submission deadline. Plan for judge availability through 15 December, and clarify the start date if needed. Winners are scheduled on or around 11 January 2027.

The four equally weighted criteria are Technological Implementation, Design, Potential Impact, and Quality of the Idea. The API gives a five-point scale. The formal rules break ties by comparing criteria in their listed order, starting with implementation. Build implications: real model/tool execution; a complete usable workflow; measured benefit for research engineers; and demonstrated advantage over a general coding agent.

The September 11 announcement emphasizes agents that plan, write, test, and iterate on a real repository and multi-step autonomous workflows. It does not change the formal requirements.

Listed prizes include $20,000/$10,000/$6,000 overall awards, Jetson Orin Nano track awards, a $3,000 Tavily bonus, city awards, and feedback awards. Formal rules limit each project to one overall OR track award plus one bonus. The resources copy says city attendance is unnecessary, while formal rules and the submission field require attendance. Do not claim city eligibility without clarification from the organizer.

## Organizer resources

These links and credit instructions were returned in the live event overview:

- [Nebius for AI Builders](https://dev.nebius.com/)
- [Nebius Builders Program](https://dev.nebius.com/builders): additional $25 Token Factory credits and program resources.
- [Token Factory credit form](https://nebius.com/promo-code?utm_promo_event_code=2026-devpost-global-ai-hack&utm_promo_code_type=Token_Factory&utm_promo_activation_code=NEBIUS-DEVPOST-GLOBAL26): advertised $25 credits, activation code `NEBIUS-DEVPOST-GLOBAL26`.
- [Nebius Discord](https://discord.gg/ZdC3rXMJH)
- [Builders & Brews events](https://luma.com/builderandbrews)
- [Hackathon discussion forum](https://nebiusglobalaihackathon.devpost.com/forum_topics); formal rules list support@devpost.com for questions.

Credit redemption has not been verified. The September 9 announcement includes a session recording and setup resources; its full body and links are preserved in `devpost-reference.json`.

## What is still missing

- Live Nemotron inference is verified. Remaining credit balance is unknown. Sandbox image-list access returns 403; execution remains blocked. No secrets should be pasted into chat.
- The first local implementation and current SDK documentation are recorded in architecture.md. Verification is recorded in verification.md.
- Dataset-specific redistribution rights remain unresolved. Begin with original synthetic fixtures; review rights before publishing external data.
- Independent evaluation cases, agent-vs-baseline results, and user validation remain to be produced.
- The user acknowledged the Nebius rules; local acknowledgment is recorded. The parent directory’s Devpost state belongs to the Amazon event and remains untouched.

The first local audit workflow runs with live inference. Remote execution and competitive advantage remain unvalidated.

## Sandbox access update — 16 September 2026

The user reports submitting the Token Factory Sandbox beta access request. The supplied console screenshot shows the Sandbox beta request screen for project aiproject-e00h0qc96emn0depx1. Approval and working API access are not yet verified; the earlier image-list 403 remains the last observed API result. Continue local repository evaluation while access is pending.

## Evaluation update — 16 September 2026

The [real-metadata pilot](../evaluation/real-pilot/REPORT.md) found identical correct results for Asterisk and a fresh Codex agent across three related tasks. The [repository pilot](../evaluation/repository-pilot/REPORT.md) found four correct scoped Codex conclusions; all four repository inputs are outside the current Asterisk contract. Neither pilot establishes a competitive advantage or human time savings. A researcher verification study is proposed, not completed.
