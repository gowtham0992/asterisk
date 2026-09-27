| Arm | Grouping match (of 18) | False-reassurance cases | Abstentions correct (of 2) | Verdict agreement | Invalid replies (of 54) | Rule |
|---|---|---|---|---|---|---|
| Nemotron 3 Super | 3 | 0 | 2 | 2 | 40 | fail |
| Nemotron 3 Ultra | 4 | 0 | 2 | 2 | 43 | fail |
| Nemotron 3 Nano | 2 | 0 | 2 | 2 | 37 | fail |
| Claude Sonnet (general model) | 4 | 0 | 2 | 2 | 43 | fail |
| Single-column script | not applicable (proposes no ladder) | 9 (camelyon-center-planted, camelyon-grouped-planted, camelyon-random, ham-lesion, ham-patient, isic2020-patient-planted, nih-hospital, nih-patient-planted, wsivqa-site) | not applicable | 9 | 0 | not applicable |

**Per case.** Each cell shows the verdicts of repeats 1–3, then ✓ if 2 or more repeats grouped samples like the reference. VIOL = violation, held = held out pending confirmation, n/e = not established, abst = abstained.

| Case | Expected | Nemotron 3 Super | Nemotron 3 Ultra | Nemotron 3 Nano | Claude Sonnet (general model) | Script |
|---|---|---|---|---|---|---|
| wsivqa-patient | held | invalid/abst/invalid | invalid/invalid/invalid | abst/invalid/abst | invalid/invalid/invalid | held |
| wsivqa-site | VIOL | abst/abst/abst | invalid/invalid/invalid | invalid/invalid/invalid | invalid/invalid/invalid | held |
| wsivqa-patient-planted | VIOL | invalid/invalid/invalid | invalid/invalid/invalid | abst/abst/abst | invalid/invalid/invalid | VIOL |
| camelyon-center | held | invalid/invalid/invalid | invalid/invalid/invalid | invalid/invalid/invalid | invalid/invalid/invalid | held |
| camelyon-center-planted | VIOL | invalid/invalid/invalid | invalid/invalid/invalid | invalid/invalid/invalid | invalid/invalid/invalid | held |
| camelyon-random | VIOL | abst/abst/abst ✓ | abst/abst/abst ✓ | invalid/invalid/invalid | abst/abst/abst ✓ | held |
| camelyon-grouped-planted | VIOL | invalid/invalid/invalid | abst/abst/invalid ✓ | invalid/invalid/invalid | invalid/abst/abst ✓ | held |
| nih-patient | held | invalid/invalid/invalid | invalid/invalid/invalid | invalid/invalid/invalid | invalid/invalid/invalid | held |
| nih-patient-planted | VIOL | invalid/invalid/invalid | invalid/invalid/invalid | invalid/invalid/invalid | invalid/invalid/invalid | held |
| nih-hospital | abst | abst/abst/abst ✓ | abst/abst/abst ✓ | invalid/abst/abst ✓ | abst/abst/abst ✓ | held |
| ham-lesion | n/e | invalid/abst/invalid | invalid/invalid/invalid | invalid/abst/invalid | invalid/invalid/invalid | held |
| ham-patient | abst | abst/abst/abst ✓ | abst/abst/abst ✓ | abst/abst/abst ✓ | abst/abst/abst ✓ | held |
| isic2020-patient | held | invalid/invalid/invalid | invalid/invalid/invalid | abst/abst/abst | invalid/invalid/invalid | held |
| isic2020-patient-planted | VIOL | invalid/invalid/invalid | invalid/invalid/invalid | abst/invalid/abst | invalid/invalid/invalid | held |
| isic2020-random | VIOL | invalid/invalid/invalid | invalid/invalid/invalid | invalid/invalid/abst | invalid/invalid/invalid | VIOL |
| anuran-random | VIOL | invalid/invalid/invalid | invalid/invalid/invalid | invalid/invalid/invalid | invalid/invalid/invalid | VIOL |
| anuran-grouped | held | invalid/invalid/invalid | invalid/invalid/invalid | invalid/invalid/invalid | invalid/invalid/invalid | held |
| anuran-grouped-planted | VIOL | invalid/invalid/invalid | invalid/invalid/invalid | invalid/invalid/invalid | invalid/invalid/invalid | VIOL |

⚠ marks a false reassurance: at least one repeat said "held out" where the reference does not.
