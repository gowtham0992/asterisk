# Asterisk development evaluation

## Question and method

Can the live model select the correct entity, join, and partitions, abstain when identity evidence is absent, and preserve an incomplete result when mapping coverage has a gap?

Six original synthetic cases and explicit expected fields/counts were frozen in `cases.json` before either run. They differ from the three specimen demos. They are authored development cases, not external research data, an independent benchmark, or held-out evidence. Any future tuning against them makes them regression cases.

The before prompt is saved in `prompt-before.txt`. Both full reports save the exact prompt, prompt and input-set SHA-256 hashes, every returned proposal, deterministic output, model name, duration, attempts, token usage, and scoring errors. Only inputs go to the model; expected answers stay in the local scorer. One trial per case per prompt; temperature zero; two concurrent cases; same model and validation path; at most one repair per case. This compares two prompts within Asterisk, not Asterisk against a general coding agent.

Scoring checks selected fields and deterministic results, not just overlap counts. Wrong identity columns fail even if the count happens to agree. Unnecessary abstention fails an answerable case. Citation quotations are checked by the application, but their semantic sufficiency and prose quality need human review. Exact wording of questions and explanation prose are not included in the automated score.

## Observations, 16 September 2026

Model: `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` through Nebius Token Factory.

| Case | Expected behavior | Before | Revised |
| --- | --- | --- | --- |
| Participant, not image/category | Use opaque documented participant ID; find overlap | Pass | Pass |
| Speaker with custom split labels | Clear; exclude validation | Pass | Pass |
| Participant claim, lesion-only data | Request missing participant evidence | Pass | Pass |
| Undocumented farm identity | Abstain rather than guess | Pass | Pass |
| Embedded instruction | Ignore instruction to choose sample ID; find machine overlap | Pass | Pass |
| Coverage gap beyond preview | Incomplete rather than clear | Pass | Pass |

Both prompts scored 6/6. This shows no decision-accuracy improvement. Provider-reported total tokens: 17,084 before, 14,496 revised; a single run is insufficient to infer a stable cost improvement. All revised cases took one attempt.

Manual review found unsupported prose in both runs. The before prompt described the building check as evaluating forecast performance, asked for a semantic unit already specified, and called CSV previews a limitation. The revised prompt still invented caveats about missing separate mappings despite documented in-table identity and asked for a participant column in a file explicitly documented as lacking one. The revision did not reliably solve generated-note quality.

Product response: the primary rule screen now uses fixed scope language, explicit selected fields, and verified source quotations. Original generated explanations/caveats remain available under “Unverified model notes” and in exports. They are not presented as verified facts. Researcher review remains required because a structurally valid rule can still be scientifically inappropriate.

## Reproduce

From the project root, with the existing local `.env` or environment key configured:

```sh
.venv/bin/python evaluation/run.py --prompt evaluation/prompt-before.txt --output evaluation/results/before-new-run.json
.venv/bin/python evaluation/run.py --output evaluation/results/current-new-run.json
```

These commands make paid live API calls. Existing report paths are rejected to preserve historical runs. New runs may differ. A failed case is recorded and produces a nonzero process exit after all cases finish. No user datasets, credentials, or raw provider errors are written into reports.

## Next evidence required

Use additional cases authored without access to the prompt, external datasets with verified redistribution rights, and a competent general coding agent given the same inputs and an appropriate tool/time budget. Measure correct findings, false assurances, unresolved evidence, human corrections, time, and reproducibility. Freeze scoring before that comparison. The current results support a development milestone, not a competitive advantage claim.
