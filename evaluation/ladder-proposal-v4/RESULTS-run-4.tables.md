| Proposer | Answer | Correct (of 10) | False reassurance | Abstentions (of 1) | Invalid | Repaired | Rule |
|---|---|---|---|---|---|---|---|
| Nemotron 3 Ultra · v3 | after ≤1 repair | 4 | 0 | 1/1 | 0 | 0 | fail |
| Nemotron 3 Ultra · v3 | first attempt | 4 | 0 | 1/1 | 0 | 0 | fail |
| Nemotron 3 Super · v2 (product default) | after ≤1 repair | 3 | 0 | 1/1 | 0 | 2 | fail |
| Nemotron 3 Super · v2 (product default) | first attempt | 3 | 0 | 1/1 | 2 | 0 | fail |
| Claude Sonnet · v3 | first attempt | 8 | 0 | 1/1 | 0 | 0 | inconclusive |
| Single-column script | — | — | 7 | — | — | — | — |

| Case | Expected | Nemotron 3 Ultra · v3 | Nemotron 3 Super · v2 (product default) | Claude Sonnet · v3 |
|---|---|---|---|---|
| ltst-random | VIOL | VIOL/VIOL/VIOL ✓ | abst/abst/abst | VIOL/VIOL/VIOL ✓ |
| ltst-grouped | held | abst/abst/abst | abst/abst/abst | held/held/held ✓ |
| ltst-grouped-planted | VIOL | abst/abst/abst | abst/abst/abst | VIOL/VIOL/VIOL ✓ |
| edb-subject-nomap | abst | abst/abst/abst ✓ | abst/abst/abst ✓ | abst/abst/abst ✓ |
| edb-subject-map | VIOL | VIOL/VIOL/VIOL ✓ | VIOL/VIOL/VIOL ✓ | VIOL/VIOL/VIOL ✓ |
| siena-random | VIOL | abst/abst/abst | abst/abst/abst | abst/abst/abst |
| siena-grouped | held | abst/abst/abst | abst/abst/abst | abst/held/abst |
| eegmat-condition | VIOL | abst/abst/abst | abst/abst/abst | abst/VIOL/VIOL ✓ |
| eegmat-grouped | held | abst/abst/abst | abst/abst/abst | held/held/held ✓ |
| fantasia-random | n/e | abst/abst/abst ✓ | abst/abst/abst ✓ | n/e/abst/n/e ✓ |
