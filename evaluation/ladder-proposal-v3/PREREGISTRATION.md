# Ladder-proposal experiment v3: pre-registration

Written 27 September 2026. The fresh cases and the v3 prompt are both written after this file. No model has seen
either.

## What v2 established (official results in `../ladder-proposal-v2`)

- **v2 fixed the output contract.** Across 66 Nemotron replies on the fresh set there were 0 invalid first attempts,
  apart from one Ultra reply that was repaired.
- **Nemotron failed by over-abstaining.**
  - Super and Ultra each got 5/11 right. They abstained even where the documentation states a file-naming pattern,
    for example Sleep-EDF's "SC4ssNEO-PSG.edf where ss is the subject number".
  - Claude Sonnet got 9/11 right. The pre-registered comparison therefore reads "Nemotron worse than G".
- **On the run-1 cases, the v2 diagnostic produced 3 false reassurances**, all on CAMELYON, and all from ladders that
  made separation true by construction:
  - partitioning by the claim unit's own column;
  - binding the claim to a unique-per-row column;
  - binding it to the observation itself.
- **The engine now refuses these by construction** (`app/ladder.py`, `_by_construction` and the one-unit-per-sample
  rule). Only a person's confirmation can turn a claim into "held out".
- **A post-hoc re-score** of the diagnostic with this guarded engine removed all 3 false reassurances. Correct answers
  stayed at 13/18. This is post-hoc and is confirmed here on unseen data.

## Hypotheses

- **H1 (safety):** with the guarded engine, no model arm produces a false reassurance on fresh data.
- **H2 (usefulness):** the v3 prompt raises Nemotron Super's correct count over the v2 prompt on the same fresh cases.
  v3 changes only the judgement rules:
  - a *stated* naming pattern is a definition, even when the prefix keeps its fixed leading characters;
  - a pattern seen only in example values is not a definition;
  - partition by the recorded assignment, never by the claim unit or a described protocol;
  - bind the claim to the named unit, never the observation;
  - abstain when the documentation says identifiers and units differ for some rows and no supplied table maps them.
- **H3 (comparison):** Nemotron with v3 against Claude Sonnet with v3, on first attempts.

## Cases

The fresh cases come from PhysioNet RECORDS lists and one mapping file, all ODC-By 1.0. They are frozen in
`cases.json` by `build_cases.py`. Reference answers are measured with the guarded engine.

- **INCART.**
  - The patient number is defined in the documentation. The authors converted `files-patients-diagnoses.txt` to
    `mapping.csv`.
  - Cases: random, grouped and grouped-planted splits; a Holter-recording claim; and a no-mapping variant whose
    correct answer is to abstain.
- **MIT-BIH plus NSTDB.** Test records are noise-added copies of MIT-BIH records 118 and 119, so the source-recording
  unit is the first 3 characters, documented by the NSTDB page and its record table.
  - A cross-database split that includes 118 and 119 in training is a violation.
  - A clean variant without them is held out.
- **ECG-ID.** The person folder (`Person_NN`) appears only in the paths, never in the text, so abstaining is also
  accepted. Cases: a random split and a grouped split.
- **Apnea-ECG.** The official learning and test sets. No subject is documented, so a subject claim must be answered by
  abstaining.

## Arms, each one frozen run

| Arm | Model | Prompt | Repeats | Repair turns |
|---|---|---|---|---|
| N3 | Nemotron 3 Super | v3 | 3 | at most 1 |
| U3 | Nemotron 3 Ultra | v3 | 3 | at most 1 |
| N2 | Nemotron 3 Super | v2 | 3 | at most 1 (the ablation for H2) |
| G3 | Claude Sonnet subagents | v3 | 3 | first attempt only |
| S | Single-column script | none | — | — |

## Scoring

Scoring is the mechanical v2 scorer, unchanged. It judges each reply with v1's `judge`, using the guarded engine that
is frozen in `freeze.json`. The abstention cases are those whose reference is an abstention.

## Rules

The thresholds scale v2's 10/11 and 8/11 to the number of cases.

| Outcome | Condition, for arm N3, using final answers |
|---|---|
| Pass | ≥ round(n·10/11) correct, 0 false-reassurance cases, and every abstention case correct |
| Fail | ≥ 2 false-reassurance cases, or < round(n·8/11) correct |
| Inconclusive | anything else |

- **H1 holds** if all of N3, U3, N2 and G3 have 0 false-reassurance cases.
- **H2 holds** if N3 has ≥ 2 more correct cases than N2.
- **H3:** first attempts, with a margin of ≥ 2 cases. Anything smaller is parity.
- **Product decision fixed now.** The product switches its default prompt to v3 only if H2 holds and N3 has no
  false reassurance. Otherwise v2 stays the default.

## Stop conditions

- One frozen run per arm. No prompt, case or scorer edits after any reply is seen.
- A run stops if its tokens exceed twice the inventory estimate.
