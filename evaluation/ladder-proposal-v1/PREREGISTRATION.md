# Ladder-proposal experiment v1: pre-registration

Written 26 September 2026, after the cases were frozen (`cases.json`) and before any model call.

## Question

Given only a dataset's documentation, column counts and a few approved identifier values, does a model propose an
independence ladder whose claim level groups samples the same way as a hand-written reference? Does Nemotron do
this better than a general model and a plain script?

## Cases (frozen in `cases.json`, built by `build_cases.py`)

- **18 cases in total**: 12 real and 6 planted, drawn from six public datasets. None of these datasets was used to write
  the prompt or the gallery. The datasets are WSI-VQA, CAMELYON17, the NIH ChestX-ray14 subset (Patient ID ≤ 10000),
  HAM10000 with the ISIC 2018 test set, ISIC 2020, and Anuran calls.
- **Planted cases** move a few real rows so that a known number of claim-level units appear in both partitions. The builder
  asserts that each reference measures exactly that number.
- **Abstention cases.** Two cases require abstention: `nih-hospital` and `ham-patient`. The documentation defines no
  per-image hospital and no patient.
- **Two cases accept abstention *or* the reference ladder**: `camelyon-random` and `camelyon-grouped-planted`. In both, the
  patient is a filename prefix that the README does not define.

## Arms

All model arms receive the same messages, produced by `app.ladder_proposal.request(claim, files, share_examples,
documentation)`. That call uses the same system prompt as the product.

| Arm | Description |
|---|---|
| **N** | `nvidia/nemotron-3-super-120b-a12b` via Nebius Token Factory. Temperature 0, JSON response format, `max_tokens` 8000, one call per repeat, no repair turn. 3 repeats per case. |
| **G** | Claude Sonnet as a general agent, run as Claude Code subagents on the `sonnet` model. Each subagent reads the identical messages and returns its reply verbatim. 3 repeats per case, each in a fresh context. This deviates from the plan in the direction document, which named the user's Anthropic key; no Anthropic key is configured. |
| **S** | A deterministic leakcheck-style script. It is given the reference partitions, which is generous. It intersects every column whose name looks like an identifier and reports a violation if any overlap. It proposes no ladder, so it is scored on verdicts only. |

## Scoring (mechanical, `run.py score`)

**Scoring each reply**

- The reply is parsed with `ladder_proposal.parse` (structure, the claim must be unchanged, documentation citations,
  and a dry run). Anything that fails to parse is **invalid**.
- **Correct** means one of the following:
  - the reference is an abstention and the reply abstains;
  - the reply is a ladder and `semantic_match(...).same_grouping` holds at the claim level;
  - for the two accept-abstain cases, the reply abstains.
- A ladder reply is then measured with `app.ladder.measure` on the case files to get its verdict.

**Aggregating to a case**

- **Grouping match (primary):** a case counts as correct if at least 2 of its 3 repeats are correct.
- **False reassurance (harm):** any single repeat whose ladder yields `held_out_pending_confirmation` counts, when the
  reference verdict is `violation`, `not_established`, `insufficient` or an abstention. A case counts as a false
  reassurance if *any* repeat does this. This is the strict reading.
- **Correct abstention:** at least 2 of 3 repeats abstain on each of `nih-hospital` and `ham-patient`.
- **Verdict agreement (secondary):** the majority verdict equals the reference verdict.

## Rules (fixed before the run)

| Outcome | Condition |
|---|---|
| **Pass** | N ≥ 15/18 on grouping match **and** 0 false-reassurance cases **and** N abstains correctly on both abstention cases. |
| **Comparative claim** | Allowed only if N beats G by ≥ 3 cases. A smaller difference is reported as parity. |
| **Fail** | N has false reassurance in ≥ 2 cases, **or** N < 12/18. |
| **Inconclusive** | Anything else. |

## Stop conditions

- One frozen run. No prompt or scorer edits after seeing any model output on these cases. A revised prompt needs a new
  held-out set.
- N stops early if total tokens exceed twice the estimate recorded in `inventory.json`.
- Every raw reply is kept, including failures.

## What leaves the machine

The only content sent is the messages in `payloads.jsonl`:
- public documentation excerpts;
- the split notes the evaluation authors wrote;
- column names with counts;
- up to four example values from the approved identifier columns of public benchmarks.

These messages go to Nebius (arm N). Arm G runs inside this Claude Code session. No credentials or private data are sent.
The Nebius key is loaded by the app's own `.env` loader inside the runner process and is never printed or stored.

## Addendum A: secondary Nemotron arms

Written 26 September 2026, after the Token Factory model listing and before any reply was read or scored. Arm N
had started; only its token-usage log had been viewed.

- **Model IDs.** The Token Factory listing on 26 September shows `nvidia/Nemotron-3-Ultra-550b-a55b`,
  `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` and `nvidia/Nemotron-3_5-Lightning`.
- **Arms and protocol.** These three models run as arms **U**, **Nano** and **L**. They use the identical frozen
  payloads, settings and scorer (`run_arm.py`, which imports the frozen `run.py` unchanged), each as its own paid run.
- **Which arm the pass rule judges.** The pass, fail and inconclusive rule above judges **arm N (Super)**, because that is
  the model the product ships. The same rule is applied to every other arm and reported. If a secondary arm passes
  and N does not, the product switches model **only** after a replication run on a fresh held-out set.
- **Which arm the comparative claim uses.** The comparative claim against G uses the best Nemotron arm, only if it clears
  the ≥3-case margin, and names the arm.
