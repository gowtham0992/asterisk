| Proposer | Answer | Correct (of 10) | False reassurance | Abstention (of 1) | Invalid | Repaired | Rule |
|---|---|---|---|---|---|---|---|
| Nemotron 3 Super · v4 | after ≤1 repair | 5 | 0 | 1/1 | 1 | 7 | fail |
| Nemotron 3 Super · v4 | first attempt | 3 | 0 | 1/1 | 7 | 0 | fail |
| Nemotron 3 Super · v2 | after ≤1 repair | 3 | 0 | 1/1 | 2 | 3 | fail |
| Nemotron 3 Super · v2 | first attempt | 3 | 0 | 1/1 | 3 | 0 | fail |
| Nemotron 3 Ultra · v4 | after ≤1 repair | 6 | 0 | 1/1 | 2 | 4 | fail |
| Nemotron 3 Ultra · v4 | first attempt | 5 | 0 | 1/1 | 5 | 0 | fail |
| Claude Sonnet · v4 | first attempt | 9 | 0 | 1/1 | 0 | 0 | pass |
| Single-column script | — | — | 6 | — | — | — | — |

| Case | Expected | Nemotron 3 Super · v4 | Nemotron 3 Super · v2 | Nemotron 3 Ultra · v4 | Claude Sonnet · v4 |
|---|---|---|---|---|---|
| cebs-state-split | VIOL | VIOL/VIOL/VIOL ✓ | abst/abst/abst | invalid/abst/abst | VIOL/VIOL/VIOL ✓ |
| cebs-grouped | held | held/abst/abst | abst/abst/abst | abst/held/held ✓ | held/held/held ✓ |
| cebs-grouped-planted | VIOL | abst/abst/abst | abst/abst/abst | VIOL/VIOL/abst ✓ | VIOL/VIOL/VIOL ✓ |
| cebs-random | VIOL | abst/abst/VIOL | abst/abst/abst | abst/abst/abst | VIOL/VIOL/VIOL ✓ |
| cebs-state-claim | held | held/held/invalid ✓ | held/invalid/invalid | held/held/held ✓ | abst/abst/held |
| wrist-activity-split | VIOL | VIOL/abst/abst | abst/abst/abst | abst/abst/abst | VIOL/VIOL/abst ✓ |
| wrist-grouped | held | abst/abst/abst | abst/abst/abst | abst/abst/abst | held/held/held ✓ |
| wrist-days | abst | abst/abst/abst ✓ | abst/abst/abst ✓ | abst/abst/abst ✓ | abst/abst/abst ✓ |
| noneeg-random | VIOL | abst/abst/abst ✓ | abst/abst/abst ✓ | abst/abst/abst ✓ | VIOL/abst/abst ✓ |
| noneeg-grouped | held | abst/abst/abst ✓ | abst/abst/abst ✓ | abst/abst/invalid ✓ | held/abst/abst ✓ |
