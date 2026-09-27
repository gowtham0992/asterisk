# Ladder-proposal v2: results (27 September 2026)

v2 fixed the output contract (`SYSTEM_V2`: exact grammar, a worked example, numbered documentation lines and one
repair turn) and tested it twice.

## Confirmatory run C: 11 fresh PhysioNet cases. Official result.

| Proposer | Answer scored | Correct (of 11) | False reassurance | Abstentions (of 2) | Invalid | Rule |
|---|---|---|---|---|---|---|
| Nemotron 3 Super (ships) | after ≤1 repair | 5 | 0 | 2 | 0 | **fail** |
| Nemotron 3 Ultra | after ≤1 repair | 5 | 0 | 2 | 0 (1 repaired) | fail |
| Claude Sonnet | first attempt | 9 | 0 | 2 | 0 | inconclusive |
| Single-column script | — | — | 8 | — | — | — |

- **Pre-registered comparison.** On first attempts, Nemotron (Super and Ultra alike) is **worse than the general
  model by 4 cases**. The claim that "Nemotron reads the documentation better" is refuted on this set.
- **How Nemotron failed.** It abstained on 30 of 33 Super replies, including where the documentation defines the unit.
  The Sleep-EDF page says "Files are named in the form SC4ssNEO-PSG.edf where ss is the subject number", and Super still
  abstained.
- **What every model got right.**
  - Every model abstained on both cases where the documentation says, in prose only, that identifiers and people
    differ: MIT-BIH records 201 and 202 share a subject, and CHB-MIT case chb21 is chb01.
  - The script cannot see either one.
- **What the de Chazal split shows.** The widely used "inter-patient" DS1/DS2 split puts record 201 in training and
  record 202 in test, and MIT-BIH's own directory says both "came from the same male subject". This is stated from
  the documentation; I do not claim it is a new discovery.
- **Reference caveat (post hoc).** In the three CHB-MIT case-level cases, the excerpt says "Each case (chb01, chb02,
  etc.) contains … .edf files" but never states that the file names begin with the case. Abstaining there is
  defensible. Accepting it would raise Super to 8/11, which is still not a pass.

## Diagnostic run D: v2 on the 18 burned v1 cases. No pass or fail by design.

- **Nemotron 3 Super: 13 of 18 correct** after at most one repair, up from 3 of 18 under v1. One reply was still
  invalid.
- **3 false reassurances, all on CAMELYON.** In each, the proposed ladder made separation true by construction:
  - partitioning by the claim unit's own column;
  - binding "patient" to a unique-per-row file name;
  - binding the claim to the observation itself.
- **Product change.** The engine now refuses these cases (`app/ladder.py`: `_by_construction`, and the
  one-unit-per-sample rule). Only a person's confirmation turns a claim into "held out", and confirmation cannot rescue
  a structural tautology.
- **Post-hoc re-score** with the guarded engine: 0 false reassurances, and still 13 of 18 correct. This is confirmed
  on unseen data in `../ladder-proposal-v3`.

The official tables are `RESULTS-confirmatory-C.tables.md` and `RESULTS-diagnostic-D.tables.md`, with the matching
`score-run-*.json`.

**Tokens.**

| Run | Model | Tokens |
|---|---|---|
| C | Super | 89,722 |
| C | Ultra | 151,604 |
| D | Super | 222,908 |
