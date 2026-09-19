# Primitive v2: regression and unseen acceptance

The v1 experiment stays intact. `primitive-v2` fixes evaluation mechanics without reclassifying its already exposed cases as unseen. No command here chooses or authors a new case set.

Run these commands from the Asterisk project root using `.venv/bin/python`. No network call occurs for inventory, preflight, freeze, report-only, or the unit tests.

1. Inspect the exact new trusted source upload with `evaluation/primitive-v2/inventory.py source --output .data/primitive-v2/source-upload-inventory.json`. The printed inventory hash binds the payload. After the payload is authorized, `evaluation/primitive-v2/bake.py --inventory-sha HASH` writes a new immutable Sandbox image and `.data/primitive-v2/environment.json`; v1 is untouched.
2. Execute the six existing development defect/repair pairs with `evaluation/primitive-v2/twins.py`. This uploads only the original synthetic development fixtures, invokes primitives and replays them, and does not use model inference. Every run has a timestamped report; `twins.json` points to the latest report. These are development tests, never unseen cases.
3. After implementation work is complete, prepare the known-case regression with `evaluation/primitive-v2/run.py --mode regression --experiment regression-01 --manifest .data/primitive-pilot/cases/manifest.json --preflight`. It snapshots the implementation and writes a private exact case upload inventory under `.data/primitive-v2/regression/regression-01/`. Inspect the inventory; its SHA is printed. To run, repeat the command without `--preflight` and add `--inventory-sha HASH`. This has 36 scheduled attempts, at most three concurrent workers, and the same cumulative $10 ledger as v1. Add `--workers 1` or `2` to lower concurrency. Completed and crashed attempts are never retried. Changing code requires a new experiment name.
4. Only after the fixes and development tests are settled, run `evaluation/primitive-v2/freeze.py --unseen-not-accessed`. This requires an explicit truthful attestation that no new unseen case has been selected, opened or authored. It requires a matching image and all six development twins. `.data/primitive-v2/acceptance/snapshot.json` and `frozen-source/` are created exclusively and cannot be overwritten. All application modules, including new helper modules, are archived and hashed.
5. Author a genuinely new twelve-case set **after that timestamp**. Use the manifest shape below and the exact protocol. Do not reuse the old pilot inputs, its v1 twelve cases or development twins. New source inputs may need new payload authorization; preserve their original rights restrictions. Do not redistribute Yang notebooks, labels or other private-evaluation-only sources.
6. Preflight with `evaluation/primitive-v2/run.py --mode acceptance --manifest PATH --preflight`. This checks the frozen code before opening the new manifest, validates timestamps, source attestations, hashes, category balance and six defect-removed twins, seals the manifest and writes its exact upload inventory. After authorized inventory review, run the same command without `--preflight`, adding `--inventory-sha HASH`.
7. To report existing work without network/inference, add `--report-only` (omit `--inventory-sha`). An optional `--review PATH` accepts genuine independent human ratings; absent ratings remain unmeasured. Both modes write `report.json` under their separate experiment directories.

Every scheduled slot appears in the report. The runner writes an attempt marker before doing work, keeps transcripts, original inputs, bundles and errors, and treats any interrupted attempt as incorrect. It uses one shared in-process `Budget` with at most three threads while holding the existing cross-process lock. Reservations for unknown charges remain in the original ledger. Starting another process while the lock is held fails before spending. Estimated cost is not a provider invoice.

`automated_correct_each_trial` is an **upper bound**, not a substitute for independent evidence review. A result below 8/12 already fails even if review is missing. A 10/12 or higher result cannot pass acceptance without human evidence adjudication, blind ratings and observed correction counts. Historical v1 7/12 outcomes remain reported as v1 failure.

Minimal manifest structure, using placeholders only:

```json
{
  "freeze_hash": "SHA256 of json.dumps(snapshot, sort_keys=True)",
  "cases": [{
    "id": "unique-id", "category": "preprocessing", "claim": "scoped research claim",
    "author": "actual author", "authored_at": "timestamp after freeze with UTC offset",
    "source": {
      "family": "yang or drug_response or planted", "url": "original source URL",
      "revision": "immutable revision", "license": "verified rights and restrictions",
      "transformations": "every extraction or change", "previously_used": false
    },
    "directory": "relative input directory", "input_hashes": {"entry.py": "SHA256"},
    "expected": {"verdict": "violation", "metrics": {}, "review_requires": ["explicit evidence obligation"]},
    "twin": {
      "directory": "relative repaired input directory", "input_hashes": {"entry.py": "different SHA256"},
      "expected": {"verdict": "clear", "review_requires": ["explicit repair obligation"]}
    }
  }]
}
```

There must be exactly four cases per category: two violations, one clear, one insufficient. Only violations have twins. Each category includes a planted variant. Source family coverage includes Yang and unused permissive drug-response sources. `previously_used: false` is an auditable assertion from the author, not a fact proven by the harness.

Human review structure:

```json
{
  "reviewer": "name", "independent_human": true,
  "blind_ratings_committed_at": "ISO8601 timestamp with UTC offset",
  "runs": {"CASE-trial1": {"requirements": {"exact frozen obligation": true}}},
  "unsupported_definitives": null,
  "corrections": null
}
```

Use `false` for obligations not established and leave unmeasured fields absent or null. Commit blind ratings before revealing ground truth or frozen requirements. Correction counts must come from observed use, not inferred tool errors. This tool does not manufacture a reviewer or practitioner sessions.
