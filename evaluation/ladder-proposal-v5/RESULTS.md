# Ladder-proposal v5: the field and characters grammar (27 September 2026)

Fresh set D has 10 PhysioNet cases: CEBSDB, Wrist PPG and Non-EEG. A freeze check before scoring found no changed
files.

## Official result: H1 holds, so the product default becomes v4

| Proposer | Correct (of 10) | False reassurance | Abstention (of 1) | Rule |
|---|---|---|---|---|
| Nemotron 3 Super · **v4** (field and characters) | **5** | 0 | 1 | fail |
| Nemotron 3 Super · v2 (previous default) | 3 | 0 | 1 | fail |
| Nemotron 3 Ultra · v4 | 6 | 0 | 1 | fail |
| Claude Sonnet · v4 (first attempt) | 9 | 0 | 1 | **pass** |
| Single-column script | — | **6** | — | — |

- **H1 (the grammar helps): holds, at exactly the pre-registered margin.** Super v4 scored 5 against v2's 3.
- **H2 (still safe): holds.** No model arm produced a false reassurance.
- **Decision, as pre-registered:** `SYSTEM_V4` is now the default prompt.

## What changed, case by case

- **Units at fixed positions.** Across the four CEBSDB subject cases (12 replies per arm), where the subject is
  characters 2–4 of b001/m001/p001, a ladder was proposed in:

  | Arm | Replies with a ladder (of 12) |
  |---|---|
  | Super v4 | 5 |
  | Ultra v4 | 4 |
  | Super v2 | 0 (it abstained on every one) |
- **Where Super still abstains.** Super and Ultra still mostly abstain on Wrist PPG ("record names reflecting the
  subject number and the activity"), where the separator is not stated in the documentation.
- **What Sonnet did.** Sonnet used `field` there and was right.

## Caveats, stated plainly

- **Super v4 still fails the pass rule (5/10).** The new grammar narrows the gap to the general model; it does not
  close it.
- **More invalid first attempts, and why.** Super v4 had 7 of 30 invalid first attempts against 3 for v2. Six of the
  seven were "Citation beyond file", which is unrelated to the grammar, and the repair turn fixed six.
- **Ultra hit provider connection errors on 3 attempts** ("APIConnectionError", about 270 s each). As pre-registered,
  they count as invalid attempts. One of them led to a repair turn that then succeeded. Ultra's first run also stalled
  on a single request for about 25 minutes; that process was stopped and resumed with the identical frozen
  configuration.
- **The `cebs-state-claim` reference is contestable.** It expects "state" (basal, music or post-music) to be a unit.
  Sonnet abstained in 2 of 3 replies, calling state an attribute, which is a reasonable reading.

## Across all four fresh sets (A–D, 41 cases)

The model false-reassurance counts are with the guards on.

| Proposer | Correct | False reassurance |
|---|---|---|
| Nemotron 3 Super (as tested) | 5 + 8 + 3 + 5 = 21 | 0 |
| Nemotron 3 Ultra | 5 + 9 + 4 + 6 = 24 | 0 |
| Claude Sonnet | 9 + 10 + 8 + 9 = 36 | 0 |
| Single-column script | — | 8 + 7 + 7 + 6 = 28 |

## Tokens

Super 201,234 (two arms) and Ultra 114,339.
