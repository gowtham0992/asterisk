# A modest measured score difference

A predeclared local experiment on 5,875 Parkinsons Telemonitoring recordings from 42 participants found mean absolute error increased by **0.1169 motor-UPDRS points** after removing planted participant overlap. All five seeds moved in that direction. This does not establish a general effect size or statistical significance.

| Seed | Rows moved | Common evaluation rows | Overlapping MAE | Repaired MAE | Size-control MAE | Repair Δ | Control Δ |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 42 | 155 | 1428 | 7.2700 | 7.3463 | 7.3019 | +0.0763 | +0.0319 |
| 43 | 178 | 1577 | 6.4939 | 6.6542 | 6.5018 | +0.1604 | +0.0079 |
| 44 | 171 | 1490 | 7.3142 | 7.5051 | 7.3006 | +0.1909 | -0.0135 |
| 45 | 171 | 1560 | 7.4292 | 7.4440 | 7.4237 | +0.0149 | -0.0054 |
| 46 | 159 | 1496 | 7.9690 | 8.1108 | 7.9682 | +0.1418 | -0.0008 |

Every overlapping split shared six participant IDs; every repaired split shared zero. The actual product repair implementation generated each candidate split. Ridge regression used 16 voice features, training-only standardization, alpha=1 and an unpenalized intercept. Lower MAE is better. All three fits were scored on precisely the same rows per seed.

This was a deliberately planted split condition on public real data already used in development. It is not a newly discovered published defect, unseen acceptance, or evidence that researchers benefit from Asterisk. The size-matched control removes the same number of training rows from non-evaluation participants, keeping the leaked rows in training. Its mean MAE increase is **0.0040**, versus **0.1169** for repair (a **1.60%** increase relative to mean overlapping MAE). This supports a leakage-related explanation in this constructed setting beyond the number of training rows removed. It does not match all participant or feature characteristics, average repeated control draws, or establish significance, a general effect, or clinical value. Identity separation alone does not guarantee scientific validity.

**Post-review extension:** the control was added after Fable supplied its results. It is not preregistered or unseen. The original protocol and original 47-file experiment remain unchanged; the [control amendment](size-control-protocol.md) records the added procedure.

Source: [Tsanas & Little (2009), Parkinsons Telemonitoring, UCI](https://archive.ics.uci.edu/dataset/189/parkinsons+telemonitoring), DOI 10.24432/C5ZS3N, CC BY 4.0.

## Reproduce

Place the source archive downloaded from UCI at `.data/probe-pilot/resources/parkinsons.zip`, then run:

```sh
.venv/bin/python scripts/run_consequence_experiment.py .data/consequence-experiment-reproduction
```

The new output directory includes the protocol, original/repaired/control split files and selected control removals, configurations, exact proposed moves, fitted coefficients, source hashes and a file manifest. No inference or upload is involved. The original [protocol](score-protocol.md) was saved before execution and its hash is `f64b7c93594891f15448ab48badcd9f107464adc2d311f5566618aa280da0f2d`. The source CSV hash is `f2c7d5025dec4e92e7feae367a5f7ccf58789a10ac6b54bdf15976c599f9dd39`.

Control amendment SHA-256: `bc03f5b9d3b8d2e988f463adb0354b21077780c0c1558d653fd24ee1e16a8d09`. The original and repaired fitted values reproduce the first experiment exactly; all five control MAEs agree with Fable’s independently supplied solver to six decimal places.
