# Asterisk

**Clean by slide. Shared by patient.**

For researchers checking whether a train/test split holds out the unit their claim requires. In the pinned public WSI-Bench report-task files, Asterisk measured **0 shared slide IDs, 42 shared patient IDs, and 43 affected evaluation rows out of 208**, under the documented TCGA patient rule. This does not establish the benchmark authors’ intended claim or an effect on accuracy.

[Inspect the saved result](https://asterisk.gowthamsarveswaran.com/public/) · [Run the same files in the workspace](https://asterisk.gowthamsarveswaran.com/static/ladder.html#receipt) (reviewer login required) · [Saved measurement and witnesses](static/ladders/wsibench-report.json)

NVIDIA Nemotron 3 Super on **Nebius Token Factory** proposes an extraction rule with documentation citations. A person reviews it; application code measures overlap; an optional fresh **Nebius Sandbox** reruns the same computation. A receipt retains the rules, witnesses and proposal origin. The model does not write the measurement. Super is the default for responsiveness: Ultra scored one more case on set D but recorded three roughly 270-second connection errors and a stopped 25-minute stall. The [retained comparison](evaluation/ladder-proposal-v5/RESULTS.md) includes these failures.

## First run from a fresh clone

Use Python 3.14 with the locked dependencies:

```sh
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8791
```

Open `http://127.0.0.1:8791/static/ladder.html`. Expand **Advanced**, choose **Load subject-disjoint example**, and select **Measure on server**. Review the partition mapping, identity definition and cited documentation, then confirm and measure again. Save and reopen the receipt. This fictional local example needs no credentials, model call, Sandbox or baked image.

For model proposals or Sandbox replay, copy `.env.example` to `.env` only if you do not already have one, and configure your Nebius API key and project ID. Use **Propose → Try a synthetic example**, inspect the outbound preview, and request the model call. Review the returned rules and measure before requesting replay. The hosted launcher is documented in [release configuration](docs/release.md).

Saved ladder receipts retain owner-scoped proposal provenance when linked to a server-recorded proposal: model, prompt version, request hash, validation-attempt metadata and edit/input-change flags. They do not retain full model reasoning. User-supplied specs are identified separately. HTML and JSON exports contain measurements, definitions and provenance, with raw inputs retained privately in workspace storage.

## Inspect, replay and hand off

After measuring, **Save to workspace** retains the input files, rule, result, witnesses and recorded confirmations for the current browser owner. Reopen it at `/#ladders`. Saving and exporting make no provider calls. **Nebius Sandbox replay** runs the same engine remotely; a match establishes reproducibility, not independent scientific verification or data authenticity.

Download readable HTML or measurement JSON, or explicitly choose **Download evidence + inputs (ZIP)**. The ZIP includes uploaded source files, including fields not shared with the model. Share only with authorized recipients. From a separately obtained, trusted Asterisk checkout:

```sh
.venv/bin/python -m asterisk verify-ladder /absolute/path/to/bundle.zip
```

This recomputes without credentials, network access or executing bundled code. Exit 0 means a matching measurement, including an overlap finding. The receipt is unsigned; confirmation records a person’s assertion, not independent validation.

## What is established

- A verified witness shows an exact identity shared between the selected partitions, under the reviewed rule.
- Zero overlap stays pending until identity meaning is confirmed; incomplete mappings cannot establish “held out.” Per-sample identifiers carry explicit warnings.
- The shipping Super v4 prompt scored **5/10 on retained set D** and failed its preparation gate. No later candidate passed promotion. A later denial control also elicited an unsupported binding. Manual definition and careful review remain necessary.
- Researcher usefulness, time saved and adoption are **unmeasured**. Content similarity, preprocessing leakage and accuracy effects are outside this check.

[Model evaluation](evaluation/ladder-proposal-v5/RESULTS.md) · [Later reliability exception](docs/submission/line-bounds-comparison-2026-10-07.md) · [Current readiness](docs/current-readiness.md)

## Real files and hosted configuration

**Run this check yourself on the same files** loads the pinned WSI-Bench projection with image identifiers only. Loading makes no model or Sandbox call. It supplies no reference rule or answer to the proposer. A fresh clone without the optional cache says it is unavailable; synthetic examples and your own files still work.

To install it, obtain the pinned report-task sources listed in `examples/ladders/sources.json`, retaining their `wsibench/` filenames. Run `.venv/bin/python -m scripts.build_wsibench_demo --data /absolute/path/to/source-data --output .data/benchmarks/wsibench`. Hosted installations set `ASTERISK_BENCHMARK_DIR` to the absolute cache-parent directory. Never commit raw data or the cache.

The hosted ladder uses `ASTERISK_HOSTED_WORKFLOW=ladder`, persistent storage and protected workspace access. It does not require the legacy baked primitive image. Judge access has a finite **$25 estimated reserve**, displayed in the app; request replenishment through the contact supplied with reviewer credentials. Manual measurement, saved results and exports do not use paid calls. [Deployment and rollback](docs/release.md) · [Judge access](docs/submission/judge-access-2026-10-07.md)

## Verification and history

At source commit `c9dc57e`, the recorded checks passed **618 Python tests with 9 existing scientific-trace skips, and 192 JavaScript tests**. These are engineering checks, not model accuracy or researcher evidence. See the [9 October workflow record](docs/submission/hosted-browser-journey-2026-10-09.md). The 23 October restructuring passed **620 Python tests with the same 9 skips and 194 JavaScript tests**; see the [current verification](docs/submission/receipt-first-2026-10-23.md).

Run `.venv/bin/python -m pytest -q tests` and `node --test tests/*.test.mjs`. Provider functions in automated tests are mocked. Some HTTP checks bind localhost; scientific-trace tests cover disabled legacy categories and may skip.

The [complete older single-binding README](docs/history/single-binding-readme-2026-10-23.md) preserves the earlier architecture, receipt format, freezes and experiments. It is historical, not the ladder workflow. [Ladder handover](docs/submission/HANDOVER-ladder.md) · [Architecture](docs/architecture.md)

MIT-licensed application code. Source releases exclude credentials, databases, private model replies and raw research datasets. Dataset licenses remain their own.
