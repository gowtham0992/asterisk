# Repair, reuse and measured consequences — 18 September 2026

Implemented complete affected/unmapped exports; two explicit partition-reassignment policies; deterministic previews tied to original file hashes; owner-scoped, idempotent approval into a separate revision; and retained move/approval records. Missing identity mappings and empty resulting partitions are rejected. Approval of a proposal does not confirm the scientific identity binding or run a measurement.

Notebook arrays export to CSV plus saved configuration. The web form imports those columns for manual review without inference. Local CLI checks export portable receipts; `--compare-to` verifies original inputs and retains a parent result hash and explicit partition/identity changes. Local mode makes no provider request and never claims a Sandbox replay or human confirmation.

The CSV bound is now 100,000 data rows / 2,000,000 cells, still capped at 80 columns and the existing byte limits. A 100,000-row synthetic split and 100,000-row identity mapping agreed locally and in two separate disposable Sandbox measurements. Host measurement took 0.837s; remote execution took 1.389s and 1.369s, excluding network setup. Host peak RSS includes SDK/process overhead. This is one measured workload, not a throughput guarantee for every input shape.

Trusted implementation: `d718f875426d0ae9be9358e08c3c3e0a378c1e8dcc6ced0c7d989f3774d110e3`. Image: `19f2ccbc-efd4-4312-9f53-356ef1ac4f9b`. Prior immutable images and historical evidence remain retained; this does not retroactively pass v3 acceptance.

The controlled public-dataset experiment reports all five prescribed seeds. Removing planted overlap increased MAE by 0.1169 motor-UPDRS points on average; training size also changes. No broad accuracy or clinical claim. A second run reproduced all 47 retained artifact hashes. See [protocol](experiments/score-protocol.md) and [results](experiments/score-results.md).

Verification: 240 passed, 9 skipped; three existing deprecation warnings. New coverage includes unchanged original files, complete exports, incomplete mappings, empty partitions, stale source hashes, ownership, changed proposal hashes, repeated approval, pending confirmation, notebook IDs with leading zeros, traversal, repeat-check tampering, row limits and the numerical solver against a closed-form solution. Browser preview confirmed 692 PTB-XL row moves, evaluation size 3,792 → 3,100 and 623 → 0 shared identities. Preview alone creates no confirmed result. Results and repair views checked at 390px; no document overflow. No paid inference was used for this implementation.

Human reviewer and practitioner evidence remains unmeasured. Automated QA is not a substitute.
