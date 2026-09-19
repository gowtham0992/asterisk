# Asterisk

A split receipt for a claim about unseen patients, subjects or specimens.

NVIDIA Nemotron Super proposes a cited identity binding. A person reviews the columns, cardinalities and partition labels. A trusted checker in Nebius Token Factory Sandboxes measures exact identity overlap and produces witness rows; a fresh Sandbox repeats the measurement. The export retains the inputs, binding, assumptions, implementation and results.

On a result, choose **Inspect witness** to compare the original training and evaluation rows and their identity mappings. The viewer verifies saved file hashes and checks the witness against both selected partitions before displaying it.

**V4 is entity-only and still a research preview.** V3 acceptance failed (9/12 primary cases per trial; 4/6 defect–repair pairs). V4 does not erase that result. Human evidence review and practitioner comprehension remain unmeasured. A practical general-agent comparison matched all 18 authored variant labels; no correctness advantage is claimed. See [validation](evaluation/primitive-v4/protocol.md) and [v4 status](docs/reviews/v4-implementation.md).

## Review and revise

- **Offline receipt:** download readable HTML directly, or open `receipt.html` in an evidence ZIP. It contains original source rows and requires no server. `review.html` collects timed notes locally. Keep the ZIP for the existing byte verifier and remote replay tooling.
- **Compare revisions:** revise the inputs and complete the second check. Compare shared identities, evaluation size, partition moves, added/deleted samples, mapping changes and ignored rows. Changes in claim or identity meaning prevent a like-for-like repair statement.
- **Manual setup:** select “Set up columns myself” to skip proposal inference. Both setup modes use the same confirmation and measurement flow. Receipts retain proposal corrections and elapsed review time.
- **Researcher evaluation:** [study protocol](docs/validation/researcher-study.md). Human usefulness remains unmeasured.

## Run locally

Use Python 3.14 and the locked dependencies:

```sh
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
```

Copy `.env.example` to `.env` only if you do not already have one. Set `NEBIUS_API_KEY` and `NEBIUS_PROJECT_ID` locally; never commit credentials. Sandbox access must be active for that project.

The application needs a baked image matching its trusted source. On an existing development workspace, `.data/primitive-v4/environment.json` records it. For a fresh installation, follow [the release instructions](docs/release.md) to prepare an image or configure `ASTERISK_PROBE_IMAGE` through the host environment.

```sh
sh scripts/start_preview.sh
```

Open `http://127.0.0.1:8765/`. Choose the synthetic entity example, authorize the proposal, inspect the citations and column counts, check and confirm the binding, then authorize the Sandbox measurement. Export the resulting receipt. The example contains one shared specimen affecting one of two evaluation rows.

One new-workflow entry point is offered. Historical audit URLs and records remain readable; they are not new v4 results. Only Super is offered for new receipts. Checkpoint selection, preprocessing and generated adapters are not product features.

## Bring a split

Supply a unique sample-ID column, partition labels, a mapping from samples to the generating entity, and documentation defining that identity. Select exact, case-sensitive labels. Rows outside those labels are excluded and counted. Surplus mapping rows do not create overlap; incomplete mapping cannot establish a clear split. A verified overlap can establish a violation even with other unmapped rows.

The file-set intake accepts up to 80 files/16 MB; individual CSVs are bounded to 100,000 data rows, 80 columns and 2,000,000 cells (whichever bound is reached first). It does not execute uploaded repository code. Use only inputs authorized for provider upload; the Sandbox beta is not for personal or sensitive data.

## What the result means

- **Violation:** a verified recorded identity occurs in both selected partitions.
- **Clear:** zero overlap and complete mapping under the human-confirmed binding.
- **Insufficient:** the available evidence does not establish the condition.
- **Incomplete:** execution or replay failed; no definitive verdict.

Human confirmation records an assumption; it is not independent verification. Wrong scientific semantics can still produce an irrelevant check. The result says nothing about image duplicates, missing identity links, model accuracy or the entire experiment. Model prose is retained separately as unverified interpretation. Measurement facts and missing-evidence messages are harness-owned.

## Reproduce and test

Run `.venv/bin/python -m pytest -q`. Scientific trace tests require a separate compatible scientific environment and may skip on the main host; these are retained development tests for disabled categories.

An exported receipt includes `verify.py` for file integrity and the matching trusted primitive source and recorded arguments for isolated replay. Do not execute uploaded research scripts on your own machine. Hashes and repeatability are not proof of scientific truth.

V3's frozen source, original cases and attempts remain in the private development records. Any v4 evaluation uses a new freeze. Exposed cases are regression checks, never newly independent acceptance. Reviewer instructions are in [docs/validation](docs/validation/reviewer-a.md).

## Release

MIT-licensed application code. The public source packager excludes keys, databases, evaluation inputs and private transcripts. Dataset and upstream source licenses do not become MIT merely by being used in a test. No third-party research data is included in the default source release.

[Hosted preview and rollback](docs/release.md) · [Demo script](docs/demo-script.md) · [Draft entry](devpost-submission.md)

## Repair and repeat

Download every affected or unmapped row from a completed receipt. Preview a group repair, inspect its partition counts, and approve a separate revision before running another measurement. Original files remain intact. See [the notebook and CLI guide](docs/notebook-and-repair.md).

The [controlled score experiment](docs/experiments/score-results.md) reports all five prescribed seeds, including the modest observed score difference and its limitations. This is development evidence, not unseen acceptance or researcher validation.

## Feature-frozen release

Feature development is stopped for the human sessions and submission preparation. Current trusted implementation: `d718f875426d0ae9be9358e08c3c3e0a378c1e8dcc6ced0c7d989f3774d110e3`; the full release snapshot and superseded-hash status are documented in [v4 release status](docs/reviews/v4-implementation.md). Legacy audit mutations/examples return 404 by default; owner-scoped historical reads and exports remain available. Do not enable `ASTERISK_LEGACY_AUDITS=1` in the release preview.
