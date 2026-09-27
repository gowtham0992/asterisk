# Ladder-proposal experiment v2: pre-registration

Written 27 September 2026. The fresh cases (`cases.json`) are frozen. No model has seen the v2 prompt yet.

## Why v2 exists

Run 1 (`../ladder-proposal-v1`) failed for every arm under its pre-registered rule. The dominant cause was the
product's v1 prompt, not model judgement: it described the spec in prose, and 34 of the 54 Super replies were
structurally invalid (the other arms were similar). Their shapes were invented ones: `sample` as an example value,
`partition` as a label, levels without expressions. v1 therefore measured whether a model can guess an unstated JSON grammar.
That is not the product question.

**v2 changes (`app/ladder_proposal.py`, `SYSTEM_V2`):**
- the exact output grammar;
- one complete worked example on the fictional scan study shipped in `static/ladder-example`;
- documentation sent as numbered line arrays;
- at most one repair turn that shows the model only the validator's error, as the app's existing proposal flow does.

The judgement rules (derive a unit only when documented, abstain when the claim's unit is undocumented, cite
documentation) are carried over from v1 unchanged.

**Disclosure.** The same author (Claude, in this session) chose the fresh datasets and wrote v2. The v2 text contains
no dataset-specific guidance, and every judgement rule predates the fresh cases. The two abstention cases below test a
rule already in v1: "If the documentation does not define that unit, abstain instead of guessing".

## Runs

1. **Diagnostic D.** v2 prompt on the 18 v1 cases, arm N (Super) only. Those cases are no longer held out, so D is
   reported as a check on the fix and has no pass or fail.
2. **Confirmatory C.** v2 prompt on the 11 fresh cases below, with these arms:

   | Arm | What it is |
   |---|---|
   | **N** | `nvidia/nemotron-3-super-120b-a12b` |
   | **U** | `nvidia/Nemotron-3-Ultra-550b-a55b` |
   | **G** | Claude Sonnet subagents, first attempt only |
   | **S** | The script baseline from v1 |

   N and U use temperature 0, the JSON response format, `max_tokens` 8000, 3 repeats and at most one repair turn.

## Fresh cases (`cases.json`, built by `build_cases.py` from PhysioNet RECORDS lists, ODC-By 1.0)

| Case | Reference |
|---|---|
| mitbih-subject | abstain: the de Chazal DS1/DS2 split; "Records 201 and 202 came from the same male subject" and no file maps records to subjects |
| chbmit-case | held out: case = the documented chbNN prefix |
| chbmit-subject | abstain: "Case chb21 ... from the same female subject" as chb01, stated only in prose |
| chbmit-random | violation (24 cases shared) |
| chbmit-case-planted | violation (1 case, planted) |
| sleepedf-random | violation (36 subjects) |
| sleepedf-grouped | held out |
| sleepedf-grouped-planted | violation (1 subject, planted) |
| sleepedf-study | not established: the SC/ST study codes trip the product's naming-family check. This is a known product limitation, frozen as is. |
| ptbdb-random | violation (52 patients); abstaining is also acceptable |
| ptbdb-grouped | held out; abstaining is also acceptable |

## Scoring

Scoring is mechanical and uses the v1 `judge` logic unchanged.

- **Primary** (arms N and U): the *final* answer after at most one repair, which is the product's behaviour.
- **Secondary**: the first attempt. Arm G is scored on its first attempt only, so any comparison with G uses first
  attempts for every arm.
- **Case aggregation:**
  - A case is correct when at least 2 of its 3 repeats are correct.
  - A case is a false reassurance when *any* repeat's ladder yields `held_out_pending_confirmation` where the
    reference is `violation`, `not_established`, `insufficient` or an abstention.

## Rules (fixed now, scaled from v1's 15/18 and 12/18)

| Outcome | Condition, for arm N (Super, the model the product ships), using final answers |
|---|---|
| **Pass** | ≥ 10/11 correct **and** 0 false-reassurance cases **and** both abstention cases correct |
| **Fail** | False reassurance in ≥ 2 cases **or** < 8/11 correct |
| **Inconclusive** | Anything else |

- **Comparative claim versus G:** first attempts only, and a margin of ≥ 2 cases. Anything smaller is parity.
- The same rule is reported for U. If U passes and N does not, the product may switch to U only after another fresh set.

## Stop conditions

- One frozen run per arm. No prompt, case or scorer edits after any reply is seen.
- A run stops if its tokens exceed twice the estimate in `inventory.json`.

## What leaves the machine

- The v2 messages in each run's `payloads.jsonl` go to Nebius:
  - public PhysioNet documentation excerpts;
  - split notes written by the evaluation authors;
  - column counts;
  - up to four example record names.
- Arm G runs inside this Claude Code session.
- The Nebius key is loaded by the app's `.env` loader inside the runner process and is never printed.
