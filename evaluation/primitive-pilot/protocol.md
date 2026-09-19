# Frozen acceptance protocol — harness measurements

Freeze engine hash, prompt hash, trusted primitive source hashes and versions, Sandbox image ID, tool schemas, and this protocol before revealing or authoring any acceptance case. Development twins under tests/ are not unseen acceptance cases. Preserve every attempt, including failures, and never replace it with an unreported retry. A changed engine requires a new freeze and a new unseen case set.

Twelve unseen cases: four per category, each containing two violations, one clean and one insufficient case. Draw from unused drug-response audit repositories with permissive licenses, Yang et al.'s ASE 2022 labeled notebooks (malusamayo/GitHubAPI-Crawler, evaluation_materials; private evaluation only, no redistribution), and one planted-defect variant per category. Each violation receives a defect-removed twin: six pairs. Case authors must be independent of prompt/primitive authors, or author only after the freeze with timestamps. Record source URLs, commits, licenses, transformations, ground truth, required evidence, and hashes before inference.

Run Nemotron 3 Super twice per case. Preserve the existing 15-tool-call and 400K-token limits. No case-specific hints or prompt changes. Twin runs are separate and use the same engine. Record all token costs and retain uncertain reservations. The existing cumulative $10 estimate remains the spending limit unless the user changes it.

| Metric | Pass | Fail |
|---|---|---|
| Gated correct verdicts, each trial | >=10/12 | <8/12 |
| False verdicts on clean/insufficient cases | 0 | Any |
| False clear on a violation twin | 0 | Any |
| Twin pairs with different verdicts | 6/6 | <6/6 |
| Primitive replay match | 100% | Any mismatch |
| Blind reviewer: definitive verdicts whose evidence fails to establish them | <=1 | >=3 |
| Cost per case | <$2 | >$5 |
| Corrections before submission | Median <=1 | Median >=3 |

Intermediate results are inconclusive. Label agreement with a failed evidence gate is incorrect. Every frozen `review_requires` item must be adjudicated explicitly; absent adjudication is unmeasured, not passed. Report automated gates separately from blind semantic review. Without a reviewer, the evidence-validity and corrections rows remain unmeasured. Do not simulate the reviewer or the two practitioner comprehension sessions with an LLM.

Replay must invoke the baked primitive with the recorded arguments on original inputs in a fresh Sandbox and compare its measurements. Free-form probes are exploratory; their output cannot stand in for primitive execution. Run defect/repair twin sensitivity before release; unchanged output on a truth-changing twin fails the measurement's sensitivity check.

Fallback: if primitive twin sensitivity has not passed by 8 October 2026, ship only entity overlap and label the code-level categories unsupported. README and demo must say verdicts are gated by trusted measurements the model cannot fabricate; never say the model verified anything. This describes evidence origin, not immunity to an incorrectly scoped model-selected argument or source-analysis limitation.
