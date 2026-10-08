# Asterisk: Devpost draft (Best Apps and Agents)

*Draft for Gowtham to edit. Numbers link to `evaluation/ladder-proposal-v1` to `evaluation/ladder-proposal-v5` (including set D and the v4 prompt).*

## Tagline

Your test set can hold out images and still share patients. Asterisk shows which unit your split really holds out,
with inspectable measurements.

## Inspiration

Published results keep being overturned because the split was clean at the wrong level: images separated but
patients shared, patients separated but hospitals shared. Our retained WSI-Bench measurement shows zero shared slides
and 42 shared patient identifiers. An intersection at only the slide level does not answer a patient-level claim.

## What it does

Asterisk measures one train/test split at **the declared levels supported by its extraction rules**: observation, recording, patient, site. It
marks the level your claim needs.

1. **You state the claim** ("No test patient appears in training") and add the split files and the dataset's
   documentation.
2. **Preview.** Your selected files are uploaded to the Asterisk server. Before any model call, you see the exact
   subset it would send to Nebius: documentation and column counts, plus example values only for the columns you approve.
3. **NVIDIA Nemotron on Nebius Token Factory proposes the ladder.** It reads the documentation, derives units such as
   "patient = first 12 characters of the barcode", cites the lines, and can abstain when it cannot establish the unit. Proposals still require review.
4. **The engine validates and measures on the Asterisk server.** It rejects two structural sources of misleading separation:
   partitioning by the claim's own unit or binding the claim to the observation itself. Per-sample and near-per-sample identities instead receive explicit warnings and require meaning review. It shows
   witnesses from the source rows.
5. **You confirm the claim-level meaning and evaluation partition.** Only then does a result read "held out". If Nemotron abstained, you
   define the unit in a guided form with a live preview.
6. **A fresh Nebius Sandbox recomputes the ladder** from the engine's own code. The result is kept only if it matches
   exactly.
7. **Save and reopen the receipt in your workspace.** Download readable HTML or JSON with partition mappings, derivations, citations, witnesses and recorded proposal origin. Edits to a recorded proposal are identified. Local execution is distinguished from a matching, server-attested Sandbox replay.

**Retained measurements on public data (reproducible from pinned files):**
- PTB-XL: 2,195 of 2,198 test ECGs come from recording sites seen in training. This is a site-overlap measurement, not a violation of its patient-disjoint split promise.
- WSI-Bench: 42 test patients are in training, with no shared slide.
- ESC-50: 2 recordings break the README's same-fold promise.

## How we built it

- **Stack:** FastAPI, SQLite and vanilla JS.
- **Engine:** the ladder engine reuses our frozen extraction language and overlap audit for every level.
- **NVIDIA Nemotron 3 Super on Token Factory** proposes the ladder, with a strict JSON grammar, a worked example,
  numbered documentation lines and one validator-guided repair turn. Nemotron 3 Ultra is available as an option.
- **Nebius Sandboxes** (`python:3.12-slim`) replay the measurement. Inputs are uploaded gzip-compressed, which fits
  multi-megabyte benchmark metadata.
- **Tests:** the clean source package passed 590 Python tests (9 scientific-trace skips) and 173 JavaScript tests. Hosted checks covered confirmation, save/export, secure sessions, CSRF, ownership isolation and restart persistence. The final deployed 439-file manifest matches the source archive.

## What the recorded evaluation supports

- **The protocol:** four frozen experiments with the hypotheses, thresholds and product decisions written before the
  first call.
- **The data:** 41 cases across four fresh PhysioNet case sets, including planted leaks. These are bounded development evaluations, not evidence that the models had never encountered the public datasets during training.
- **Recorded safety result:** no guarded run produced a false "held out" in these retained cases. A single-column comparison produced 28. This is a bounded observation, not a guarantee on new inputs.
- **The guard earned its place:** in a retained case it stopped Nemotron Super from calling a cross-database leak "held out". The exposed cases do not establish fresh held-out performance for the current implementation.
- **Grammar matters.** Letting proposals say "characters 2–4" or "field 1 split on _" raised Nemotron Super from 3 to 5 of
  10 on a fresh set, with no false reassurance, so it is now the default.
- **Zero false reassurance does not mean every proposal was correct.** Nemotron Super scored 21/41 and Ultra 24/41 across the tested configurations; Claude Sonnet scored 36/41. Abstentions, invalid replies and provider failures are reported separately in the protocols and results. Super with the shipping v4 prompt still failed the set-D pass rule at 5/10. The guided definition step keeps the user involved when preparation is incomplete. A later small development comparison also elicited one unsupported binding when documentation denied its meaning; historical zero-false-reassurance counts are not a guarantee that model interpretations are correct. [Latest comparison](line-bounds-comparison-2026-10-07.md).

## Challenges

- Our first prompt described the output in prose, and 75% of model replies were malformed. We rebuilt the contract and
  report the failed run.
- Sandbox stdin is capped near 1 MB. We moved inputs to the file upload.
- We had to tell the difference between "zero overlap" and "zero overlap by construction".

## What we learned

Separating model proposals from computed measurements makes mistakes inspectable; the observed zero-false-reassurance result is limited to the tested cases. Pre-registering the evaluation changed
our pitch twice, and made it honest.

## What's next

- Record the end-to-end demo from the deployed workspace.
- Measure whether researchers can understand and use the receipt without its author present.
- Improve preparation on a new, frozen case set before claiming broader reliability.

## Deployed demonstration

Workspace: https://asterisk.gowthamsarveswaran.com/static/ladder.html#propose (reviewer credentials supplied separately).

The 28 September hosted smoke completed in 10.29 seconds: one Nemotron 3 Super call (3,162 tokens), deterministic measurement, one fresh Nebius Sandbox replay with exact match, saved receipt and HTML export. It used the shipped fictional example and found one shared patient affecting one of four evaluation rows. The saved record retained the actual proposal origin and unchanged-binding flags. This verifies integration on one example, not general accuracy or researcher benefit.

Public introduction, public source URL and the under-three-minute video remain to be published. This document is a draft, not a submitted entry.
