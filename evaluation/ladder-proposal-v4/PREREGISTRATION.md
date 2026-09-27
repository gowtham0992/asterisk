# Ladder-proposal experiment v4: replication

Written 27 September 2026, before the cases are built and before any model sees them.

## Why

On fresh set B (`../ladder-proposal-v3`), Nemotron 3 Ultra with the v3 prompt passed (9/10), and Nemotron 3 Super did
not (8/10). The v2 pre-registration says the product switches its proposer model only after another fresh set
confirms the result. This is that set.

The engine is the guarded engine as of this commit. The prompts `SYSTEM_V2` and `SYSTEM_V3` are unchanged since set B.

## Cases

The fresh set comes from PhysioNet (ODC-By 1.0, plus Siena Scalp EEG under CC BY 4.0). Only record names and verbatim
documentation are used. The set is frozen in `cases.json` by `build_cases.py`, and reference answers are measured with
the guarded engine.

| Dataset | Unit and its source | Cases |
|---|---|---|
| **Long-Term ST** | Subject = record name minus its last digit (first 5 characters): "Records obtained from the same subject have names that differ in the last digit only." | random, grouped and grouped-planted splits |
| **European ST-T** | Subject groups are stated only in prose ("Records e0118-e0122 come from the same subject; …"). | A no-mapping variant, where the correct answer is to abstain, and a variant with `mapping.csv`: the authors' mechanical conversion of that sentence, with every other record as its own subject. |
| **Siena Scalp EEG** | Subject = the `PNxx` folder: "Each folder contains … recordings of a specific subject." | random and grouped splits |
| **EEGMAT** | Subject = `SubjectNN`, with `_1` background and `_2` task files. | A condition split (`_1` train, `_2` test) and a subject-grouped split |
| **Fantasia** | 40 records from 40 subjects; subject = record. | A random split. The reference is "not established", because one unit per sample guarantees zero overlap. Abstaining is also accepted. |

## Arms, each one frozen run

| Arm | Model | Prompt | Role |
|---|---|---|---|
| **U** | Nemotron 3 Ultra | v3 | the configuration under replication |
| **N** | Nemotron 3 Super | v2 | the product's current default |
| **G** | Claude Sonnet subagents | v3 | first attempt only |
| **S** | Single-column script | — | baseline |

Nemotron arms use 3 repeats and at most one repair turn.

## Rules

Scoring is the unchanged v2 scorer.

| Outcome | Condition, per arm, using final answers |
|---|---|
| Pass | ≥ round(n·10/11) correct, 0 false-reassurance cases, and every abstention case correct |
| Fail | ≥ 2 false-reassurance cases, or < round(n·8/11) correct |
| Inconclusive | anything else |

**Product decision, fixed now.**
- **If U passes:** the product's default proposer becomes Nemotron 3 Ultra with the v3 prompt.
- **If U does not pass:** the default stays Nemotron 3 Super with v2, and Ultra remains an option.

## Stop conditions

- One frozen run per arm. No prompt, case or scorer edits after any reply is seen.
- A run stops if its tokens exceed twice the inventory estimate.
