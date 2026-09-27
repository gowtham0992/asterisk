| Proposer | Answer | Correct (of 18) | False-reassurance cases | Abstentions correct | Invalid replies | Repaired | Rule |
|---|---|---|---|---|---|---|---|
| Nemotron 3 Super | after ≤1 repair | 13 | 3 (camelyon-center-planted, camelyon-grouped-planted, camelyon-random) | 2/2 | 1 | 6 | fail |
| Nemotron 3 Super | first attempt | 13 | 2 (camelyon-center-planted, camelyon-grouped-planted) | 2/2 | 6 | 0 | fail |

Each case cell lists the verdicts of repeats 1–3. ✓ means at least 2 of 3 repeats grouped samples like the reference; ⚠ means at least one repeat said "held out" wrongly.

| Case | Expected | Nemotron 3 Super (final) | Nemotron 3 Super (first) |
|---|---|---|---|
| wsivqa-patient | held | abst/abst/abst | abst/abst/abst |
| wsivqa-site | VIOL | abst/abst/abst | abst/abst/abst |
| wsivqa-patient-planted | VIOL | abst/abst/abst | abst/abst/abst |
| camelyon-center | held | invalid/held/held | invalid/held/held |
| camelyon-center-planted | VIOL | held/VIOL/VIOL ⚠ | held/VIOL/invalid ⚠ |
| camelyon-random | VIOL | abst/abst/held ✓ ⚠ | abst/abst/invalid ✓ |
| camelyon-grouped-planted | VIOL | abst/abst/held ✓ ⚠ | abst/abst/held ✓ ⚠ |
| nih-patient | held | held/held/held ✓ | held/held/invalid ✓ |
| nih-patient-planted | VIOL | VIOL/VIOL/VIOL ✓ | VIOL/VIOL/VIOL ✓ |
| nih-hospital | abst | abst/abst/abst ✓ | abst/abst/abst ✓ |
| ham-lesion | n/e | n/e/abst/n/e ✓ | n/e/abst/n/e ✓ |
| ham-patient | abst | abst/abst/abst ✓ | abst/abst/abst ✓ |
| isic2020-patient | held | held/held/held ✓ | held/held/invalid ✓ |
| isic2020-patient-planted | VIOL | VIOL/VIOL/VIOL ✓ | VIOL/VIOL/VIOL ✓ |
| isic2020-random | VIOL | VIOL/VIOL/VIOL ✓ | VIOL/VIOL/VIOL ✓ |
| anuran-random | VIOL | VIOL/VIOL/VIOL ✓ | VIOL/VIOL/VIOL ✓ |
| anuran-grouped | held | held/held/held ✓ | held/held/held ✓ |
| anuran-grouped-planted | VIOL | VIOL/VIOL/VIOL ✓ | invalid/VIOL/VIOL ✓ |
