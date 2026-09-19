# Frozen primitive evaluation

**Decision: acceptance failed. Do not present the code-level investigation agent as reliably validated.**

Engine `primitive-v1`; frozen 2026-09-18T05:04:48.689715+00:00. Case authoring: 2026-09-18T05:09:41.776907+00:00. Model: `nvidia/nemotron-3-super-120b-a12b`. The engine, prompts, tools and protocol were unchanged after case authoring. This is a post-freeze authored set, not independently authored or independently reviewed. Original public-source code, explicitly planted defects and controlled identity splits are distinguished in the private manifest. No result is an accusation about a published study outside its scoped source case.

**Automated label agreement with primitive gates and replay: 7/12 and 7/12.** Every `review_requires` item and the blind evidence-validity/corrections rows remain unmeasured. These automated counts are not a complete acceptance pass.

| Case | Expected | Trial 1 | Trial 2 |
|---|---|---|---|
| entity-source | violation | violation | violation |
| entity-control | clear | clear | clear |
| entity-planted | violation | violation | violation |
| entity-unavailable | insufficient | insufficient | insufficient |
| pre-source | violation | incomplete | incomplete |
| pre-planted | violation | violation | violation |
| pre-control | clear | insufficient | clear |
| pre-unavailable | insufficient | insufficient | insufficient |
| checkpoint-control | clear | incomplete | incomplete |
| checkpoint-planted-source | violation | incomplete | incomplete |
| checkpoint-planted | violation | insufficient | insufficient |
| checkpoint-unavailable | insufficient | insufficient | incomplete |

**Defect/repair pairs changing from violation to clear in both trials: 2/6.**

- entity-source: [('violation', 'clear'), ('violation', 'clear')] — passed
- entity-planted: [('violation', 'clear'), ('violation', 'clear')] — passed
- pre-source: [('incomplete', 'insufficient'), ('incomplete', 'insufficient')] — failed
- pre-planted: [('violation', 'clear'), ('violation', 'insufficient')] — failed
- checkpoint-planted-source: [('incomplete', 'incomplete'), ('incomplete', 'incomplete')] — failed
- checkpoint-planted: [('insufficient', 'insufficient'), ('insufficient', 'insufficient')] — failed

Primitive replays matched: 54/54 retained measurements. A matching unavailable result is reproducible abstention, not successful defect detection. Completed result bundles: 36/36. No hidden retries or case corrections were performed.

Estimated batch token usage cost: $0.7902; largest individual run: $0.0591. Cumulative ledger including previous experiments and uncertain reservations: $5.4236 of the authorized $10 estimated cap. Rates are the frozen report estimates, not a provider billing reconciliation.

The Yang source case retains raw notebook-cell syntax in the exported Python input. This exercises an unsupported notebook-export boundary; its failed parsing is not evidence that the underlying leakage is absent. The repair retains that syntax and missing external dependencies. The source-only checkpoint cases also test cross-file selection flow. Inspect the retained errors and requirements before attributing a failure to model reasoning versus primitive coverage.

Historical v3 audit: all twenty previous free-form verdicts lack admissible primitive records. This is a contract audit, not a rerun or new-engine accuracy estimate. Human review must judge whether the selected primitive arguments establish the scientific scope; deterministic gates alone cannot answer that.

Raw private evidence: `.data/primitive-pilot/runs`, `cases-sealed.json`, `acceptance-report.json`. Public release packaging excludes inputs and notebook contents. The private blinded packet is for an independent reviewer; no LLM ratings are substituted for that review.
