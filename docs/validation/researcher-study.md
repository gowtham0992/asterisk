# Researcher utility and setup evaluation

Status: **unmeasured**. The local worksheet and summary command are implemented; no person has completed this study. Automated QA is excluded from human summaries.

## First question: is the receipt worth using?

Recruit the two real practitioners specified in the v4 protocol. No message is sent automatically. Obtain consent and use aliases. Keep expected answers out of review materials until the notes are downloaded and committed. Do not use the walkthrough as an unseen acceptance case.

For the evidence reviewer, prepare equivalent Asterisk and coding-agent outputs for the six cases required by the protocol. Preassign blinded A/B labels and counterbalance presentation order. Record prior exposure; repeated review of the same case can create a learning advantage, so do not treat second-view timing as an independent measurement. Prefer additional reviewers assigned opposite first-view formats if recruiting permits. The creator must not coach a review.

Open `review.html` from the exported ZIP beside `receipt.html`. Start the timer when the reviewer begins. Pauses are explicit; both active and wall times are retained. The reviewer answers checked/found/unknown/next action, identifies source rows, rates evidence support and reports assistance. Download notes before revealing labels. The format-preference explanation matters as much as the timing; self-reported support is not ground truth.

The second reviewer does the five-minute comprehension task from reviewer-b.md. Grade against the protocol only after preserving verbatim answers. No automated score substitutes for this review.

Collect JSON notes locally and run:

```
.venv/bin/python scripts/summarize_reviewer_notes.py /path/to/notes
```

The command excludes automated fixtures and nonconsenting/nonblind records. It reports observations, not a release pass. Keep original notes and assignment separately. Check aliases for accidental duplicates. Small samples establish initial usability signals, not population-level superiority.

## Second question: does the AI proposal help?

The input form now offers **Set up columns myself**. It produces no inference request or preview upload. Both modes use the same local profiles, binding review, confirmation, measurement and replay. Manual source excerpts are references rather than a model's semantic interpretation.

Before collecting results, assign comparable unfamiliar schemas to AI-assisted and manual setup, alternating which mode each participant sees first. Do not let the same person learn the exact binding in one mode and call the second mode faster. Keep claims, necessary documentation, interface, hardware and completion criteria comparable. Record each task's complexity and prior exposure.

Receipts retain `setup_observation`: setup mode, original proposal, confirmed fields, field changes, review-start and confirmation times. AI proposal generation latency is outside the review interval. Also record end-to-end task time externally, including file preparation and model latency; otherwise the two modes are not comparable. Idle time can inflate the stored wall interval. A changed field is not automatically an AI error; a blinded adjudicator checks the documentation.

Measure correct initial bindings, corrections, final binding correctness, active and total task time, assistance and preference. Do not claim a model advantage unless it reduces effort without hiding wrong bindings. Failures stay in the denominator. Report manual setup as a useful alternative if AI does not help.

## Decision

Use the existing safety and comprehension thresholds. Continue the utility claim only when the reviewer can reproduce a witness without builder assistance and gives a meaningful reason to prefer the receipt. If it offers no benefit over the baseline, change the workflow or narrow the claim. Do not add detector categories to compensate for an unproven benefit.
