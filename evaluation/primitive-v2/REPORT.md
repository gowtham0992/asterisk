# Primitive v2 repair regression — 18 September 2026

**The implementation repairs are verified, but the reliability gate still fails.** Automated gated correctness improved from 7/12 in each v1 trial to **11/12 in each v2 trial** on the same now-known inputs. **4/6 defect/repair pairs passed both trials**, up from 2/6. This is a development regression, not an unseen benchmark or an acceptance pass. No false definitive verdict was observed against the frozen labels; independent scientific evidence review remains unmeasured.

The v1 failed experiment and source archive are preserved. V2 engine, prompt, schemas, source and scoring were snapshotted at 2026-09-18T15:21:05.736123+00:00. No source changes, case changes or retries occurred during the 36 scheduled attempts. All 36 produced completed reports within 2–8 tool calls. Model: `nvidia/nemotron-3-super-120b-a12b`.

| Case | Expected | Trial 1 | Trial 2 |
|---|---|---|---|
| entity-source | violation | violation | violation |
| entity-control | clear | clear | clear |
| entity-planted | violation | violation | violation |
| entity-unavailable | insufficient | insufficient | insufficient |
| pre-source | violation | violation | insufficient |
| pre-planted | violation | violation | violation |
| pre-control | clear | clear | clear |
| pre-unavailable | insufficient | insufficient | insufficient |
| checkpoint-control | clear | insufficient | clear |
| checkpoint-planted-source | violation | violation | violation |
| checkpoint-planted | violation | violation | violation |
| checkpoint-unavailable | insufficient | insufficient | insufficient |

The passing pairs were entity-source, entity-planted, pre-planted and checkpoint-planted. The two remaining failures are material:

- **Preprocessing source and repair:** one source trial skipped static fit analysis after dynamic execution rejected an unsupported import, so it missed an available static finding. Both repaired-notebook trials remained insufficient. The restricted tracer rejects `seaborn` and the supplied notebook lacks its external dataset; syntax normalization alone cannot establish a clean executed experiment. The original expected-clear twin was preserved and remains failed.
- **Imported checkpoint control and repair:** the failed trials supplied `df` as the final evaluation symbol instead of the actual held-out loader. The checker rejected that disconnected query. Other trials selected the supported scope and completed. Source tracing now works for this fixture; autonomous argument selection remains inconsistent.

## Implemented changes

Display-only notebook normalization preserves original line positions and records original/normalized hashes. Executable magics remain unsupported. Static fitting analysis follows split aliases and row provenance; rebound callables and ambiguous flows remain unresolved. Dynamic tracing accepts an empty transformer list to observe all supported transformers and records actual fit/split source locations.

Checkpoint tracing discovers bounded source paths across imported helpers and compact single-file selection. It binds score parameters, model state, saved artifact, restore and final evaluation. Regression cases reject overwritten scores, wrong models, mutated destinations, disconnected metric slots and dead branches. Static evidence does not establish historical execution.

The report envelope now comes from the harness; model-written values cannot replace trusted measurements. Category-specific tools, numbered file previews and a reserved finalization call prevent malformed prose from discarding retained evidence. Harness finalization preserves every measurement, source citation, loop-exit reason and fresh replay; exploration output remains inadmissible.

## Verification and limits

- **188 local tests passed.** Source archive verification is recorded in `artifacts/primitive-v2-status.json`.
- **6/6 original synthetic development pairs passed** in Nebius with 12/12 fresh matching primitive replays.
- **3/3 additional synthetic remote smoke checks passed** with 3/3 replays: normalized fit execution with all hooks, imported checkpoint control and planted defect.
- **39/39 live regression primitive replays matched**, including reproducible unavailable results.
- **36/36 evidence bundles passed** byte, ZIP, source-provenance and completion-record verification. These checks do not adjudicate scientific meaning.
- Estimated regression token cost: **$0.287313**; largest attempt **$0.036322**. Cumulative settled and reserved estimate **$5.710910 / $10**. No old reservation was discarded; estimates are not provider invoices.

New unseen v2 cases have not been selected or evaluated. Independent blind evidence review and practitioner corrections remain unmeasured. Do not describe this version as reliably validated or the regression as unseen performance. The 8 October entity-only fallback remains enforced when current development-twin proof is absent.

Private evidence: `.data/primitive-v2/regression/regression-01/`. Baked image: `e9711849-7d56-4994-869c-af7c9862ffe6`. Primitive implementation: `94c52ee746118203dca88eba9e85a5b0dab849dd8f3390b243a4476e1e24adb3`. Private research inputs are excluded from the source ZIP.
