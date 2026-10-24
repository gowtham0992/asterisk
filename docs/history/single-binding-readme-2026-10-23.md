# Historical single-binding README — archived 23 October 2026

These are historical instructions and observations, not the current ladder architecture.

## Historical single-binding workflow

The sections below document the earlier single-binding product, its native-preparation experiment and evidence ZIP. They remain for existing users and reproducibility; new ladder users should follow the first-run steps above. The ladder export is a different artifact format and does not contain `verify.py`.

## Single-binding split receipts

A split receipt for a claim about unseen patients, subjects or specimens.

NVIDIA Nemotron Super proposes a cited identity binding. A person reviews the columns, cardinalities and partition labels. A trusted checker in Nebius Token Factory Sandboxes measures exact identity overlap and produces witness rows; a fresh Sandbox repeats the measurement. The export retains the inputs, binding, assumptions, implementation and results.

On a result, choose **Inspect witness** to compare the original training and evaluation rows and their identity mappings. The viewer verifies saved file hashes and checks the witness against both selected partitions before displaying it.

**V4 is entity-only and still a research preview.** V3 acceptance failed (9/12 primary cases per trial; 4/6 defect–repair pairs). V4 does not erase that result. Human evidence review and practitioner comprehension remain unmeasured. A practical general-agent comparison matched all 18 authored variant labels; no correctness advantage is claimed. See [validation](../../evaluation/primitive-v4/protocol.md) and [v4 status](../../docs/reviews/rc7-verification-wording.md).

## Review and revise

- **Offline receipt:** download readable HTML directly, or open `receipt.html` in an evidence ZIP. It contains original source rows and requires no server. `review.html` collects timed notes locally. Keep the ZIP for the existing byte verifier and remote replay tooling.
- **Compare revisions:** revise the inputs and complete the second check. Compare shared identities, evaluation size, partition moves, added/deleted samples, mapping changes and ignored rows. Changes in claim or identity meaning prevent a like-for-like repair statement.
- **Manual setup:** select “Set up columns myself” to skip proposal inference. Both setup modes use the same confirmation and measurement flow. Receipts retain proposal corrections and elapsed review time.
- **Researcher evaluation:** [study protocol](../../docs/validation/researcher-study.md). Human usefulness remains unmeasured.

## Run locally

Use Python 3.14 and the locked dependencies:

```sh
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
```

Copy `.env.example` to `.env` only if you do not already have one. Set `NEBIUS_API_KEY` and `NEBIUS_PROJECT_ID` locally; never commit credentials. Sandbox access must be active for that project.

The application needs a baked image matching its trusted source. On an existing development workspace, `.data/primitive-v4/environment.json` records it. For a fresh installation, follow [the release instructions](../../docs/release.md) to prepare an image or configure `ASTERISK_PROBE_IMAGE` and its matching `ASTERISK_PROBE_DRIVER_SHA256` through the host environment.

```sh
sh scripts/start_preview.sh
```

Open `http://127.0.0.1:8765/`. Choose the synthetic entity example, authorize the proposal, inspect the citations and column counts, check and confirm the binding, then authorize the Sandbox measurement. Export the resulting receipt. The example contains one shared specimen affecting one of two evaluation rows.

One new-workflow entry point is offered. Historical audit URLs and records remain readable; they are not new v4 results. Only Super is offered for new receipts. Checkpoint selection, preprocessing and generated adapters are not product features.

## Bring a split

### Start from native metadata

Open `/#prepare` to inspect CSV/JSON metadata locally and choose the fields that may leave your device. “Try a real public benchmark” downloads pinned DermaMNIST sources directly into the browser, checks their hashes and enters this same review flow. No model call occurs on load. Automatic extraction remains experimental.

Native preparation is disabled by default, even when the general Nebius key is configured. For a **new installation**, initialize its estimated budget once:

```sh
mkdir -p .data
.venv/bin/python -m app.preparation.init_budget --path "$PWD/.data/preparation-budget.json" --limit-usd 1
export ASTERISK_PREPARATION_BUDGET="$PWD/.data/preparation-budget.json"
export ASTERISK_PREPARATION_NEBIUS=1
sh scripts/start_preview.sh
```

Stop an already-running preview before restarting with these variables. Keep `NEBIUS_API_KEY` in your existing local `.env`; never place it in a browser form or commit it. Initialization refuses an existing file. Reuse the existing ledger on later starts; never replace a spent, uncertain, missing or damaged live ledger with a fresh budget. The established development workspace continues using its existing shared ledger and cost baseline unless deliberately migrated without resetting commitments. Configuration performs no inference; each request still needs payload consent. Sandbox setup remains separate.

### Start from a prepared split

Supply a unique sample-ID column, partition labels, a mapping from samples to the generating entity, and documentation defining that identity. Select exact, case-sensitive labels. Rows outside those labels are excluded and counted. Surplus mapping rows do not create overlap; incomplete mapping cannot establish a clear split. A verified overlap can establish a violation even with other unmapped rows.

The file-set intake accepts up to 80 files/16 MB; individual CSVs are bounded to 100,000 data rows, 80 columns and 2,000,000 cells (whichever bound is reached first). It does not execute uploaded repository code. Use only inputs authorized for provider upload; the Sandbox beta is not for personal or sensitive data.

## What the result means

- **Violation:** a verified recorded identity occurs in both selected partitions.
- **Clear:** zero overlap and complete mapping under the human-confirmed binding.
- **Pending confirmation:** zero recorded overlap with complete mapping, but the identity meaning still needs a person’s confirmation. An automated review cannot supply it.
- **Insufficient:** the available evidence does not establish the condition.
- **Incomplete:** execution or replay failed; no definitive verdict.

Human confirmation records an assumption; it is not independent verification. Wrong scientific semantics can still produce an irrelevant check. The result says nothing about duplicate content, missing identity links, model accuracy or the entire experiment. Model prose is retained separately as unverified interpretation. Measurement facts and missing-evidence messages are harness-owned.

## Reproduce and test

The [published DermaMNIST example](../../static/published-example.html) reproduces a known 641-lesion overlap from pinned public metadata. Run `scripts/reproduce_dermamnist.py` with the two upstream CSVs as documented on that page. It runs locally without credentials or uploads, checks source hashes, and emits only aggregate results. This does not measure model accuracy or researcher benefit.

Run `.venv/bin/python -m pytest -q tests` from the project root. The combined suite includes local HTTP tests that need permission to bind `127.0.0.1`; provider calls in those tests are mocked. Scientific trace tests require a separate compatible scientific environment and may skip on the main host; these are retained development tests for disabled categories.

An exported receipt includes `verify.py` for byte consistency against its unsigned manifest, plus measurement source and recorded arguments. A sender can replace the checker, inputs and manifest together; do not treat running that checker as independent verification. Do not execute uploaded research scripts on your own machine. Hashes and repeatability are not proof of scientific truth.

V3's frozen source, original cases and attempts remain in the private development records. Any v4 evaluation uses a new freeze. Exposed cases are regression checks, never newly independent acceptance. Reviewer instructions are in [docs/validation](../../docs/validation/reviewer-a.md).

## Release

MIT-licensed application code. The public source packager excludes keys, databases, evaluation inputs and private transcripts. Dataset and upstream source licenses do not become MIT merely by being used in a test. No third-party research data is included in the default source release.

[Hosted preview and rollback](../../docs/release.md) · [Demo script](../../docs/demo-script.md) · [Draft entry](../../devpost-submission.md)

## Repair and repeat

Download every affected or unmapped row from a completed receipt. Preview a group repair, inspect its partition counts, and approve a separate revision before running another measurement. Original files remain intact. See [the notebook and CLI guide](../../docs/notebook-and-repair.md).

The [controlled score experiment](../../docs/experiments/score-results.md) reports all five prescribed seeds, including the modest observed score difference and its limitations. This is development evidence, not unseen acceptance or researcher validation.

## Frozen fallback and current working tree

RC7 remains the frozen fallback. The working tree has subsequent guided-example and published-reproduction presentation changes; RC7 does not freeze those bytes. Native metadata extraction is an isolated experiment, not a supported feature. See [current readiness](../../docs/current-readiness.md) for evidence and outstanding gates. Current trusted implementation: `d718f875426d0ae9be9358e08c3c3e0a378c1e8dcc6ced0c7d989f3774d110e3`; the full release snapshot and superseded-hash status are documented in [v4 release status](../../docs/reviews/rc7-verification-wording.md). Legacy audit mutations/examples return 404 by default; owner-scoped historical reads and exports remain available. Do not enable `ASTERISK_LEGACY_AUDITS=1` in the release preview.

Obtain and verify a matching Asterisk release separately from the received receipt. From that trusted installation directory—not from inside the received bundle—run `python -m asterisk verify /absolute/path/to/receipt`. This uses original files and installed measurement code without credentials or network access. Exit 0 means measurement and decision consistency; it does not authenticate the author or validate identity semantics.

### Real benchmark and dedicated judge access

The workspace's **Load real benchmark** action loads a pinned WSI-Bench report-task projection containing only image identifiers. It does not load a reference specification, model reply or measurement answer. Preview, proposal, review, measurement and optional replay use the normal workflow. The source's clinical conversations and question IDs are excluded. The projection lives outside Git; a clone without this cache shows an explicit unavailable message and retains the synthetic example and own-file paths.

To install the optional cache, obtain the two report-task files at the pinned URLs in `examples/ladders/sources.json`, retaining their `wsibench/` filenames under a local data directory. `scripts/build_wsibench_demo.py` verifies their hashes and projects identifiers. From the project root, run `.venv/bin/python -m scripts.build_wsibench_demo --data /absolute/path/to/source-data --output .data/benchmarks/wsibench`. Do not commit the source files or generated cache. Set `ASTERISK_BENCHMARK_DIR` to an absolute cache-parent path on hosted deployments.

Dedicated judge login configuration, budget assumptions and remaining compliance limits are in [judge access](../../docs/submission/judge-access-2026-10-07.md). The prepared human comprehension page is `/static/receipt-study.html`; [collection instructions](../../docs/submission/human-review-launch-2026-10-07.md) distinguish real human responses from developer dry runs. No human benefit is claimed.

### Hand off a complete ladder measurement

Choose **Download evidence + inputs (ZIP)** after measuring or from a saved receipt. The ZIP includes all uploaded source files, including fields not sent to the model, plus the full result, witnesses, spec, recorded origin/confirmations, engine hashes and a readable receipt. Download is opt-in, session-scoped and makes no provider call. Share it only with authorized recipients.

From a separately obtained and verified matching Asterisk installation, run `python -m asterisk verify-ladder /absolute/path/to/bundle.zip`. This checks the bounded ZIP in memory and recomputes the whole measurement without extracting or executing bundled code, making a network call, or using credentials. Exit 0 means a matching measurement, even when it reports overlap. Exit 2 means verification failed. Recorded meaning confirmations are reused, not independently endorsed. The bundle is unsigned: matching hashes do not authenticate original data, authorship or Sandbox execution.
