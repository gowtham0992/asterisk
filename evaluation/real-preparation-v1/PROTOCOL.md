# Fresh real-data preparation test v1

Status: protocol committed before candidate freeze and case selection. No fresh
cases selected or run. This is engineering evaluation, not independent human
validation, researcher demand, or general accuracy evidence.

## Order and selection

1. Freeze application, recursive preparation modules, UI, scripts, tests and
   dependency locks using scripts/freeze_preparation_candidate.py. Record the
   manifest hash before researching or authoring new cases. The historical
   extraction-holdout-v1 freeze remains unchanged and does not cover this candidate.
2. Select three distinct public dataset families with realized train/test
   membership and documented generating-unit identity. Search official dataset
   catalogs and original publisher repositories for subject-disjoint evaluation
   metadata. Archive queries and ordered results. Consider candidates in returned
   order; take the first three eligible families, recording every rejection and
   its reason before invoking the candidate. Eligibility requires an explicit
   license permitting the intended evaluation, downloadable metadata within the
   product's documented size limits, and sufficient documentation for a reference
   calculation. Do not reject based on overlap count or predicted model success.
   Unsupported layouts remain recorded, not silently replaced after an attempt.
3. Exclude all previously inspected families: DermaMNIST/HAM10000, PTB-XL,
   WSI-Bench, UCI Parkinsons (174 and 189), UCI HAR, and any additional family
   found in existing evaluation records. Publish that exposure inventory before
   selection. Shared-origin datasets count as one family.
4. Add an expected-abstention case with an actually absent identity link and one
   sample-ID trap with the documented subject mapping in a separate artifact.
   These are additional cases, not substitutes for the three real families.
   Any omission or transformation is explicitly recorded as authored, not as an
   unmodified public release. Do not label a familiar MedMNIST example fresh.
5. A case author writes standalone reference scripts without calling the product.
   Commit file hashes, claims, licenses, source versions, exact per-occurrence
   subject/partition assignments, count results and missing-evidence rationale
   before model execution. Preserve original reference scripts. Record who saw
   source, labels, implementation and earlier outputs. Agent authorship is never
   described as independent human authorship. If the implementer authors cases,
   disclose design exposure and do not describe the set as blind to that person.

## Data and execution

All workflows start from the same raw files and claim; preparation time starts
at that handover, including projection work. Raw personal fields remain local.
Only selected identifier columns and reviewed documentation may enter inference
payloads; Sandbox inputs must likewise exclude unselected fields. Preserve exact
identifier strings, withheld field names, source hashes and projection lineage.
Record and inspect a concrete upload inventory before execution. This protocol
creates no new spending allowance; use the existing cumulative caps and ledger.

One initial Nemotron proposal per case, no provider-failure retry. At most one
recorded human correction per case; retain original and corrected results side
by side. If no human is available, report only the uncorrected result and any
separate developer-agent diagnostic, never an agent action as human confirmation.
No feedback from expected answers is supplied to the model. Each workflow gets
15 tool calls, ten minutes and 16,000 model tokens per case; unavailable baseline
usage measurements must be reported and preclude an equal-budget claim.

Valid proposals execute through the product preparation, review, measurement and
fresh-Sandbox replay path. Scientific confirmation remains a distinct recorded
act, never inferred from count agreement. Preserve every response, payload hash,
error, intervention, time, cost estimate and replay result. Provider failures are
failures to complete, not scientific abstentions. Do not rerun a failed case to
replace its outcome. No case or reference edits after outputs are visible.

Run a fresh general coding agent and a separate timed script workflow on identical
inputs without reference answers. A script written by an AI is an automated script
baseline, not a human manual baseline. Previously viewed inputs cannot support an
unexposed preparation-time measurement. Missing comparators stay unmeasured.

## Fixed gate

Pass requires all of the following:
- At least two of the three answerable real cases yield exact reference counts
  with at most one actual human correction each (uncorrected success counts).
- The abstention case refuses and names the absent artifact; merely saying
  insufficient without the missing link does not pass.
- The sample-ID trap never reaches an accepted wrong definitive answer.
- No accepted wrong definitive answer anywhere; no unselected personal values
  in any external payload; every completed measurement replay matches.

Independently check occurrence coverage and subject/partition assignments: equal
counts can conceal incorrect bindings. Equivalent sample-label encodings require
an explicitly documented bijection, never a relaxed count-only scoring rule.
Record citation grounding separately. Scientific meaning not supported by the
files remains unresolved, even if a number agrees with the reference.

If required cases, privacy checks or replay results are missing, outcome is
incomplete, never pass. A model failure means ship the supported manual workflow
and keep preparation experimental. Do not tune against failures and reuse this
set as fresh acceptance. Preserve all earlier development failures.

An advantage claim additionally requires strictly fewer accepted wrong answers
or fewer interventions than the matched general agent under measured equal
budgets. Otherwise say only that results are packaged for recomputation. Human
comprehension and second-reader effort remain unmeasured without real screened
people; no agent review substitutes for them. Paid recruitment is a separate
concrete purchase, not authorized by this file.
