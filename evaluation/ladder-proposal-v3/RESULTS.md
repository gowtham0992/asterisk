# Ladder-proposal v3: results (27 September 2026)

Fresh set 3 has 10 PhysioNet cases from INCART, MIT-BIH with NSTDB, ECG-ID and Apnea-ECG. All pre-registered
hypotheses and rules are in `PREREGISTRATION.md`. A freeze check before scoring found no changed files.

## Official result

| Proposer | Answer | Correct (of 10) | False reassurance | Abstentions (of 2) | Rule |
|---|---|---|---|---|---|
| Nemotron 3 Super · v3 (ships) | after ≤1 repair | 8 | 0 | 2 | inconclusive |
| Nemotron 3 Ultra · v3 | after ≤1 repair | 9 | 0 | 2 | **pass** |
| Nemotron 3 Super · v2 (ablation) | after ≤1 repair | 8 | 0 | 2 | inconclusive |
| Claude Sonnet · v3 | first attempt | 10 | 0 | 2 | **pass** |
| Single-column script | — | — | **7** | — | — |

Full tables are in `RESULTS-run-3.tables.md`, and the raw score is in `score-run-3.json`.

## Hypotheses

- **H1 (safety): holds.** No model arm produced a false reassurance on fresh data under the guarded engine.
- **H2 (v3 helps Super): does not hold.** Super scored 8 with v3 and 8 with v2. As pre-registered, **the product keeps v2
  as its default prompt**. v3 did reduce invalid first attempts, from 3 to 1.
- **H3 (Nemotron against a general model): Nemotron is worse, by 2 cases, on first attempts.** Super and Ultra each
  scored 8; Sonnet scored 10. This agrees with run C, where the gap was 4 cases.
- **Ultra v3 passes; Super does not.** Under the v2 pre-registration, the product switches to Ultra only after another
  fresh set confirms it. That has not been run.

## The guards did real work on unseen data (counterfactual, labelled)

**The failure.** On `nstdb-cross` (test records are noise-added copies of the training records 118 and 119), Super bound
"recording" to the full record ID instead of its documented first three characters. Every sample then had its own
unit, so zero overlap was guaranteed. The guarded engine answered "not established".

**The counterfactual.** Re-judging the same frozen replies with the guards switched off shows that both Super arms (v2
and v3) would have produced a **false reassurance on a real cross-database leak**. The guards were designed after
diagnostic run D (burned cases), and this is the first time they were exercised on data nobody had seen.

## Where the models differ

| Cases | What happened |
|---|---|
| INCART (lookup through `mapping.csv`), `incart-nomap`, `apnea-subject` | Every arm was right. That includes abstaining when the documented mapping file was not supplied, and when no subject is documented. |
| ECG-ID | Every arm abstained, which the rules accept. The `Person_NN` folder appears only in paths. |
| NSTDB | This is where Nemotron missed: it needs a documented prefix across two databases. Sonnet got all 6 repeats right, Ultra 3 of 6, and Super 0 of 6. Each miss was a safe "not established" or an abstention. |

## Tokens

| Model | Tokens (N3 + N2 combined for Super) |
|---|---|
| Super | 213,279 |
| Ultra | 160,201 |
