# Native-layout preflight: preparation remains experimental

## Observed outcome

No fresh live acceptance result exists. Local intake and text-parser probes on
three candidate families reveal a native-format coverage limit before inference:

- Vowel recognition: `.data` filename rejected. Renaming alone leaves each
  whitespace row as one string; the language has no whitespace-field operation.
- UJI v2: text filename accepted, but 47,719 source lines are treated as records,
  rather than 11,640 documented WORD-header observations. There is no record
  selector or stateful text-block parser in the frozen extraction language.
- Japanese Vowels: `.train` filename rejected; the line parser also refuses its
  blank-separated utterance blocks. Speaker counts require block accounting.

These are reproduced intake/parser observations, not model failures. The study
is incomplete, not passed. No model calls or Sandbox uploads occurred. Do not
silently convert these sources to ready-made CSV tables and count that as model
preparation from native files. Do not expand the grammar against these cases and
then call the same cases fresh. Retain the manual supported path and label model
preparation experimental. A future parser extension would need a separately
justified scope, new freeze and new evaluation; it is not implemented here.

Reference authoring now covers three families: 990 vowel observations (0 shared
speakers), 11,640 UJI observations (0 shared writers), and 640 Japanese vowel
utterances (9 shared speakers, all 370 test utterances affected under a hypothetical
unseen-speaker claim). The last is deliberately not a scientific misconduct or
benchmark leakage allegation: speaker identification uses known speakers.

## Freeze correction

The first manifest b8fcff6a… omitted the three historical files dynamically loaded
by preparation: extraction-v1/executor.py, extraction-v2/proposal.py and
extraction-v3/proposal.py. Its source hashes were accurate but its coverage was
incomplete. The original manifest and snapshot are preserved, not rewritten.

The corrected candidate is 87219eee0e4b79c4514888ff3235983aaebd86a8dc219b03450b100310b5c142,
228 files. A regression test now imports proposal, model_record and review from
an isolated copied snapshot using Python isolated mode, then parses a synthetic
CSV. All three freeze tests pass. This tests actual runtime dependency presence,
not merely manifest arithmetic. The correction changes the freezer/tests only;
no application or prompt was tuned against the new datasets.

Nevertheless the corrected freeze happened after this agent inspected sources
and reference answers. The strict original ordering cannot be claimed retroactively.
Any future report must disclose that limitation. These are prospectively selected
coverage probes against unchanged application code, not an independent blind
acceptance study. The reference scripts use no Asterisk code; their author is the
same implementation agent, so calculations are separate but authorship is not
independent. The prior chat phrase "independent calculations" means code separation
only, not independent evaluation.

## Remaining work

No complete five-case packet, negative/trap cases, live matched comparison,
privacy-approved external inventory, or human comprehension study exists for
this protocol. These remain unmeasured. First decide whether the supported
CSV/JSON/one-record-per-line scope is acceptable; do not spend inference to prove
a documented parser lacks a different grammar. This finding rules out a universal
raw-research-file preparation claim, not the supported receipt product.
