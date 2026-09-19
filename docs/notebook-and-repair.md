# Repair a split, then check it again

A repair proposal changes partition labels only. It does not change identity mappings, delete rows, retrain a model, or certify that the new experiment design is suitable.

1. Open a completed entity-overlap receipt. Download **All affected and unmapped rows** for the complete inventory, including both sides of each shared identity. CSV row numbers count the header as row 1. Import identifier columns as text; rows.json preserves exact identifiers too.
2. Choose which side should keep overlapping identities. Moving evaluation rows into training shrinks evaluation. Moving training rows into evaluation shrinks training. Inspect the before/after counts and proposed moves. Missing mappings and empty resulting partitions block proposals.
3. Approve the proposed changes to create a separate revision. The parent receipt remains unchanged. Review the identity meaning and run the revised check; compare its receipt with the parent. A preview's zero overlap is not a confirmed receipt.

## Export actual notebook arrays

Run from the Asterisk source directory using its installed environment, or put that directory on your Python import path. No automatic notebook execution or provider upload occurs.

```python
from asterisk import export_split

config = export_split(
    "experiment-export",  # must be a new directory
    sample_ids=["001", "002", "003", "004"],
    entity_ids=["patient-A", "patient-A", "patient-B", "patient-C"],
    partitions=["train", "test", "test", "train"],
    claim="Evaluation patients must be absent from training.",
    identity_definition="entity identifies the patient who generated each recording.",
)
```

Use the realized sample, participant and partition arrays from your experiment in place of these four illustrative rows. Export writes splits.csv, identities.csv, identity.md and asterisk.json. Choose the whole folder in the workspace to reuse the proposed columns without inference. Human confirmation is never transferred.

## Local repeatable checks

```sh
.venv/bin/python -m asterisk check experiment-export/asterisk.json --output receipts/first
.venv/bin/python -m asterisk check revised-export/asterisk.json --output receipts/second --compare-to receipts/first
```

Each output directory must be new. Keep the same configuration and column names when updating data. The optional comparison verifies the earlier file hashes and records partition moves, changed identity mappings, coverage and sample-universe changes; it does not treat remapping identities as a repaired split.

Exit status 1 means recorded overlap; 0 means no overlap found but scientific identity confirmation remains pending; 2 means incomplete evidence or an error. Zero is not experiment certification. Local receipts include input hashes, trusted source, an offline viewer and verifier. They explicitly record local execution and no fresh Sandbox replay. The web workflow adds reviewed binding and remote measurement/replay.

Limits: 80 files / 16 MB total, 10 MB per uploaded file; each CSV has at most 100,000 data rows, 80 columns and 2,000,000 cells. Wider tables reach the cell limit earlier.

### Exact identifiers and CSV formatting

Similar-looking identities are reported separately when case folding, Unicode normalization or surrounding-space removal would collapse distinct exact values. This is a display warning, not a merge or verdict change. Review the scientific meaning before confirming a binding. Only mapped identities from selected partitions contribute to this warning.

Open `rows.json` first when inspecting exported identifiers. CSV copies retain exact values, including identifiers beginning with spreadsheet formula characters. Import those columns as text; no formula-escaping prefix is silently added to the evidence. Repair preserves the header's record line-ending convention and every parsed field value, but normalizes CSV quoting. A text diff can therefore contain formatting changes beyond partition assignments.
