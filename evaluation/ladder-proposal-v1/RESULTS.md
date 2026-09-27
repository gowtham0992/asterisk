# Ladder-proposal v1: results (run 1, 26–27 September 2026)

**Outcome under the pre-registered rule: fail, for every model arm.**

| Proposer | Grouping match (of 18) | False reassurance | Abstentions (of 2) | Invalid replies (of 54) |
|---|---|---|---|---|
| Nemotron 3 Super | 3 | 0 | 2 | 40 |
| Nemotron 3 Ultra | 4 | 0 | 2 | 43 |
| Nemotron 3 Nano | 2 | 0 | 2 | 37 |
| Claude Sonnet | 4 | 0 | 2 | 43 |
| Single-column script | — | 9 | — | — |

Per-case tables are in `RESULTS-run-01.md`. The raw score is `score-run-01.json`.

**What it measured.** Mostly whether a model can guess an unstated JSON grammar. The v1 prompt, written by the
evaluation author, described the spec in prose, and each model invented its own shape. Three shapes recurred:
- `sample` given as an example value;
- `partition` given as a label;
- levels with no expression.

The validator rejected every one of those replies before anyone could see it. So no invalid reply produced a false
reassurance.

**What it did not measure.** Whether a model can read documentation to find the unit. That question moved to v2.

**Tokens.** Super 144,670; Ultra 212,073; Nano 177,305. Token Factory prices were not verified in this session.
