# Primitive-v3 verification

Read protocol.md first. All commands run from the repository root using its virtual environment. Local scripts do not grant permission to upload new datasets.

1. `python evaluation/primitive-v3/bake.py` prints the trusted-source upload inventory. After authorization, add `--execute` to bake a separate immutable image.
2. `python evaluation/primitive-v3/gate_a.py` runs ten adversarial development pairs with fresh Sandbox replay, no inference. It refuses to overwrite its report.
3. Only after A passes, `python evaluation/primitive-v3/gate_b.py` runs the twelve specified known attempts on the shared cumulative $10 ledger. It refuses to reuse its output directory.
4. Only after both pass, `python evaluation/primitive-v3/freeze.py --unseen-not-accessed` snapshots implementation, prompts, tools, policy and evaluation before new case access. Do not make this attestation if new cases were already opened.
5. Have the case author prepare twelve primary cases and six twins following protocol.md. Record authorship constraints and exposure honestly. Keep expected labels outside the engine inputs.
6. `python evaluation/primitive-v3/run.py --mode acceptance --manifest PATH --preflight` validates the frozen code, case dates, source provenance, input hashes, balance, and creates an exact upload inventory. Inspect it before uploading.
7. Supply the printed `--inventory-sha HASH` to execute. Existing failed/partial slots remain failures, never silent retries. Use `--report-only` to summarize without inference. A named independent human review file may be supplied with `--review PATH`; absence can never produce a passing acceptance result.

The cutoff reads `.data/primitive-v3/acceptance-report.json` and matching `snapshot.json`. Gate A/B and development twins are not acceptance. Preprocessing stays disabled regardless of acceptance. Human identity confirmations are recorded separately; a pending result is not a clear.

Public source packages exclude research input files, local database, provider credentials and full private evaluation bundles. Preserve those locally with their original provenance.
