# Ladder-proposal v4: replication results (27 September 2026)

The fresh set C has 10 PhysioNet cases: Long-Term ST, European ST-T, Siena Scalp EEG, EEGMAT and Fantasia. A
freeze check before scoring found no changed files.

## Official result: Ultra did not replicate

| Proposer | Correct (of 10) | False reassurance | Abstention (of 1) | Rule |
|---|---|---|---|---|
| Nemotron 3 Ultra · v3 (under replication) | 4 | 0 | 1 | **fail** |
| Nemotron 3 Super · v2 (product default) | 3 | 0 | 1 | fail |
| Claude Sonnet · v3 (first attempt) | 8 | 0 | 1 | inconclusive |
| Single-column script | — | **7** | — | — |

**Pre-registered decision.** Ultra failed, so **the product's default stays Nemotron 3 Super with the v2 prompt**, and
Ultra remains an option. Ultra's pass on set B (9/10) did not replicate.

## What went wrong, and what did not

- **Every miss by both Nemotron models was an abstention.** They produced no invalid answers after repair and **no
  false reassurance**.
- **The misses all involve a documented naming rule.** For example: "Records obtained from the same subject have names
  that differ in the last digit only." Super abstained on all three Long-Term ST cases; Ultra answered one of the three.
- **The misses are not model-specific everywhere.** On Siena, where the documentation says each folder holds "a
  specific subject", Claude Sonnet also abstained in 5 of 6 replies. The reference there, subject = the `PNxx` folder
  prefix, is arguably stricter than the text supports, which is the same caveat as for CHB-MIT in v2.
- **Every arm handled the lookup and the prose-only exception.** With `mapping.csv` supplied, all arms found the
  violation. Without it, all arms abstained.

## Across the three fresh sets (A, B, C: 31 cases)

| Proposer (as tested) | Correct | False reassurance with the guards |
|---|---|---|
| Nemotron 3 Super · v2 or v3 | 5 + 8 + 3 = 16 | 0 |
| Nemotron 3 Ultra · v2 or v3 | 5 + 9 + 4 = 18 | 0 |
| Claude Sonnet | 9 + 10 + 8 = 27 | 0 |
| Single-column script | — | 8 + 7 + 7 = 22 |

## Tokens

| Model | Tokens |
|---|---|
| Super | 88,049 |
| Ultra | 155,148 |
