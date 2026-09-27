# Ladder-proposal experiment v5: does the richer grammar help?

Written 27 September 2026, before the cases are built and before any model sees the v4 prompt.

## Why

On fresh sets A–C, Nemotron's misses were almost all abstentions on units that the documentation defines inside
an identifier. The general model sometimes did the same. Several of those abstentions said the expression grammar
could not express the unit: it had only prefixes.

The engine now supports two more steps, `field` (separator-delimited parts) and `characters` (1-based positions). The
v4 prompt (`SYSTEM_V4`) is **v2 with only the expression grammar extended and two fictional examples**. Its judgement
rules are unchanged.

## Cases

The fresh set D comes from PhysioNet (ODC-By 1.0), using record names and verbatim documentation only. It is frozen
in `cases.json` by `build_cases.py`.

| Dataset | Unit and its source | Cases |
|---|---|---|
| **CEBSDB** | "records b001 to b020 … m001 to m020 … p001 to p020" (basal, music, post-music). Subject = characters 2–4; state = character 1. | A state split (b and m train, p test; violation); a subject-grouped split and a planted variant; a random split; a state claim (held out) |
| **Wrist PPG** | "record names reflecting the subject number and the activity" (`s1_walk`). Subject = field 1 split on `_`. | An activity split (walk and bike train, run test; violation); a subject-grouped split; a claim about recording days, which are not documented, so the answer must be to abstain |
| **Non-EEG** | "two records per subject", with names such as `Subject10_SpO2HR`. Subject = field 1 split on `_`; a prefix would merge Subject1 with Subject10–19. The naming is visible only in record names, so abstaining is also accepted. | A random split and a subject-grouped split |

## Arms, each one frozen run

All arms use 3 repeats; the Nemotron arms have at most one repair turn.

| Arm | Model | Prompt |
|---|---|---|
| **N4** | Nemotron 3 Super | v4 |
| **N2** | Nemotron 3 Super | v2 (the current default, as the ablation) |
| **U4** | Nemotron 3 Ultra | v4 |
| **G4** | Claude Sonnet subagents | v4, first attempt only |
| **S** | Single-column script | — |

## Hypotheses and rules

Scoring is the unchanged v2 scorer, with the pass, fail and inconclusive thresholds scaled to n.

- **H1 (the grammar helps):** N4 is correct on at least 2 more cases than N2.
- **H2 (still safe):** N4, N2, U4 and G4 each have 0 false-reassurance cases.
- **Product decision, fixed now:** the default prompt becomes v4 **only if H1 holds and N4 has 0 false-reassurance
  cases**. Otherwise v2 stays the default. The engine keeps the new operators either way, because people can use them
  in the guided builder.

## Stop conditions

- One frozen run per arm. No prompt, case or scorer edits after any reply is seen.
- A run stops if its tokens exceed twice the inventory estimate.
