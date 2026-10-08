# Later update: messy-file comparison, 7 October 2026

The unchanged bounds-only candidate failed the next paired test: v4 16/16, v6 15/16, with one candidate regression and more structural citation flags. Keep v4. The early interrupted pilot, builder correction and partial exposure are disclosed in [the full report](messy-preparation-comparison-2026-10-07.md). No product or hosted behavior changed.

# Current update: 7 October 2026

The hosted release is 1d55a9a, including citation correction and evidence exports. A fresh paired bounds-only prompt experiment scored 16/16 versus v4's 13/16 attempts on eight correlated cases, but did not pass its precommitted promotion criterion. Shipping v4 stays unchanged. One new denial control elicited an unsupported binding from v4; historical statements below that misses were only abstentions do not describe all future behavior. See [the full report](line-bounds-comparison-2026-10-07.md), including the scorer correction, limitations and retained failures. Historical no-commit/no-push instructions below have been superseded by the owner's later explicit authorization.

# Handover: Asterisk independence ladder (26–27 September 2026)

## Update: workspace integration, 27 September

The user explicitly authorized building further and committing the current product plus this integration, excluding secrets, raw research data and experiment records. That supersedes the historical no-commit instruction below; pushing is not authorized.

Ladders now save into owner-scoped workspace storage. The standalone local check and proposed-ladder journey offer **Save to workspace**; a successful Sandbox replay automatically retains its actual server provenance. Reopen under `/#ladders`, inspect all measured levels and witnesses, download HTML/JSON, or delete the record and its inputs. Local receipts explicitly state that no Sandbox replay is recorded. Exports contain measurements, spec and hashes, not raw inputs or upstream model history; they are separate from the single-binding evidence ZIP.

The workspace and standalone screen share `static/ladder-render.mjs`. New backend: `app/ladder_receipts.py`; new workspace controller: `static/ladder-workspace.js`. Tests cover ownership, HTML escaping, rejected client verdict/provenance injection, confirmation preservation, record integrity and a successful replay surviving a storage failure. The README ladder section and stale v1–v4 submission references are updated. A fresh preview was started on port 8792 with an isolated synthetic-test database; older preview processes were not stopped.

Browser verification used the fictional local-only example, saved and reopened it in the workspace and downloaded its HTML. No paid inference or Sandbox execution was performed. See `docs/submission/ladder-workspace-verification-2026-09-27.md` for final verification and commit scope.

The historical notes below describe the state before this update. Remaining submission requirements still include hosting, public repository visibility, the video and final submission; the workspace as a whole has not been restyled.

This note is for whoever picks up the work next. **Nothing is committed**: Gowtham owns commits. `git status` also
shows many modified files from earlier sessions (receipts, investigations, workspace). Those are not part of this
work. The files this work touched are listed in "Where everything is" below.

## What Asterisk is now

Most leak checkers look at one ID column. That can make a split look clean at the image level while patients or
hospitals are shared. Asterisk measures one train/test split at **every level the data defines** (observation,
recording, patient, site) and marks the level your claim depends on. The flow:

1. **Propose.** NVIDIA Nemotron 3 Super on Nebius Token Factory reads the dataset documentation and proposes the
   ladder, citing documentation lines. It abstains when the documentation doesn't define a unit.
2. **Measure.** The local engine validates the proposal and measures it. It refuses any result that is "held out by
   construction".
3. **Confirm.** The user confirms what the claim level means. Only then can the result read "held out".
4. **Replay.** A fresh Nebius Sandbox recomputes the ladder from the engine's own code. The result is kept only if it
   matches exactly.
5. **Receipt.** The user downloads it.

Pitch line: **the model proposes, the engine decides, you confirm.**

## What was built, and how it's better

### 1. Ladder engine (`app/ladder.py`)
- **Every level at once.** Measures overlap at each level with the existing extraction language and overlap audit,
  and gives source-row witnesses for each overlap.
- **Guards against "held out by construction"** (a false reassurance is a split called "held out" when it isn't):
  - A claim bound to the observation itself gives `not_established`, not a pass.
  - So does a partition read from the claim's own unit column.
  - So does one unit per sample.
- **Human confirmation.** A result is `held_out` only after the user confirms the level.
  - The status before that is `held_out_pending_confirmation`, with an explicit `confirmable` flag.
  - The CLI takes `--confirm LEVEL`.
- **New grammar:**
  - `field` extracts separator-delimited parts, such as `s1_walk` → `s1`.
  - `characters` extracts 1-based positions, such as `b012` → `012`.
  - The order is basename → field → characters or prefix.
- **Honest headline.** Missing levels show as "Unavailable", not "Not established". The naming-family warning only
  fires on identifiers that contain digits.
- **Why it's better:** the old single-binding check could only say whether one ID column overlaps. Now a split that is
  clean by slide but shared by patient is visible and explained. Real finds from pinned public files:

  | Dataset | Finding |
  |---|---|
  | WSI-Bench | 42 test patients in training, with 0 shared slides |
  | PTB-XL | 2,195 of 2,198 test ECGs come from sites seen in training |
  | ESC-50 | 2 recordings break the README's fold promise |
  | MIT-BIH | the de Chazal split separates records 201 and 202, which the documentation says are one subject |

### 2. Nemotron proposal (`app/ladder_proposal.py`)
- **Prompts v1 to v4.** v4 is the default. It has an exact JSON grammar, a worked example, numbered documentation
  lines, `field` and `characters` with two fictional examples, and one repair turn guided by the validator.
- **Nothing leaves without consent.** Only documentation and column counts are sent, plus example values for columns
  the user explicitly approves. Split labels are shared by default.
- **Why it's better:**
  - The v1 prose prompt got 75% invalid replies. v2 got 0 of 33 invalid on a fresh set.
  - v4 raised Super from 3 to 5 of 10 on a fresh set, with no false reassurance.

### 3. Nebius Sandbox replay (`app/ladder_sandbox.py`)
- **How it runs:** the engine source is bundled and run in `python:3.12-slim`.
- **Input:** uploaded as a gzip file, because stdin is capped near 1 MB. A 6.6 MB PTB-XL table uploads as 980 KB.
- **Output:** must match the local result byte-for-byte. Error messages are scrubbed of data.

### 4. API and CLI
- **`app/ladder_api.py` routes:**
  - `POST /api/ladder` measures.
  - `/api/ladder/preview` makes no network call.
  - `/api/ladder/propose` returns 503 without a key, 422 for an unusable reply, and 502 for a provider error.
  - `/api/ladder/replay` runs the Sandbox replay.
- **Models:** `MODELS` lists Super (default) and Ultra.
- **`app/main.py`:** the 18 MB body limit now also covers `/api/ladder*`.
- **`asterisk.py ladder ... --confirm LEVEL`:** exits 1 on a violation, 0 on held out or pending, and 2 otherwise.

### 5. Pre-registered evaluation (`evaluation/ladder-proposal-v1` to `v5`)
- **Protocol:** each experiment has PREREGISTRATION.md, frozen cases with hashes (`freeze.json`), a mechanical
  scorer, and RESULTS.md. Every failed run is reported.
- **Headline across 41 unseen PhysioNet cases:**
  - **No model proposal produced a false "held out"**, with the guards in place.
  - A single-column checker produced 28.
- **Correct ladders out of 41:**

  | Proposer | Correct |
  |---|---|
  | Claude Sonnet | 36 |
  | Nemotron Ultra | 24 |
  | Nemotron Super | 21 |

  Nemotron's misses were abstentions, never confident errors. The comparison with Sonnet is published, not hidden.
- **Full write-up:** `/Users/g/Desktop/hackathon/research/reports/asterisk-ladder-experiments-2026-09-27.md`.

### 6. Guided builder (for when Nemotron abstains)
- The user defines a unit with basename, field, characters or prefix, and sees a live preview on their own values.
- A contract test proves the JavaScript `buildSpec` output measures identically in Python.

### 7. UI polish (`static/ladder.html`, `ladder.css`, `ladder.js`, `ladder-figure.mjs`, `product.html`)
- **Direction:** "a calm scientific instrument: a Nature figure page crossed with Linear's precision." It uses only the
  existing tokens: paper background, Georgia headings, mono data and one green accent.
- **Hero.** A live "Figure 1" drawn from real WSI-Bench data: **141** shared sites, **42** shared patients (the claim
  level) and **0** shared slides. It has one primary call to action and a four-item nav.
- **Benchmark rows.** Large numerals ("42 of 207 evaluation patients") with a thin bar. The verdict panel uses a
  coloured edge instead of a heavy block.
- **Propose.**
  - A real drag-and-drop area and a "Try a synthetic example" button.
  - NVIDIA and Nebius marks on the steps that use them.
  - The claim's level is highlighted.
- **Evidence.** A stats strip (0 against 28, and Super 3 → 5) plus a model-by-set table. The model names are pinned so
  they stay visible on phones.
- **Advanced.** The hand-written JSON spec tool is collapsed.
- **Landing page (`product.html`).** A new section, "Clean by slide. Shared by patient.", with the same live figure and
  the Nemotron → Asterisk → Nebius chain.
- **Checked:**
  - 1440, 768 and 375 px widths: no horizontal scroll and no console errors.
  - Every colour pair passes WCAG AA; the lowest ratio is 4.60.
  - Keyboard focus is visible.

## Where everything is
- **Engine:** `app/ladder.py`, `app/ladder_proposal.py`, `app/ladder_sandbox.py`, `app/ladder_api.py`, plus the ladder
  command in `asterisk.py`.
- **Page:**
  - `static/ladder.html`, `static/ladder.css`, `static/ladder.js`
  - `static/ladder-view.mjs`, `static/ladder-figure.mjs`
  - `static/product.html`, whose ladder section and asset links were added
  - `static/index.html`, which has only a sidebar link
- **Data:**
  - `static/ladders/*.json`: the gallery plus `experiment.json` for the scoreboard
  - `static/ladder-example/` and `static/ladder-example-propose/`
- **Tests:**
  - `tests/test_ladder.py`, `test_ladder_proposal.py`, `test_ladder_sandbox.py`, `test_ladder_chain_api.py`,
    `test_ladder_builder_contract.py`
  - `tests/ladder-view.test.mjs`
- **Submission drafts:** `docs/submission/devpost-ladder-draft.md`, `feedback-nebius-nvidia.md`,
  `video-script-ladder.md`.
- **Third-party data** stays outside the repo, in
  `/Users/g/Desktop/hackathon/research/research_notes/Asterisk independence unit direction/data/`.

## Run and test
```bash
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8791
.venv/bin/python -m pytest -q
node --test tests/*.test.mjs
```

- **Test results:** at last check, 548 Python tests passed (9 skipped) and 164 JavaScript tests passed.
- **Live calls:** propose and replay need the Nebius key in `.env`. It is loaded by the app's own loader; never print
  it. Without a key, propose returns 503 and everything else still works.
- **Pages:** `/static/ladder.html` (the demo) and `/static/product.html`.
- **Server:** the old server on port 8782 predates the ladder routes, so restart it.

## Open items, in priority order
1. **Hackathon requirements still missing.** Deadline: 30 October 2026, 10:00 PDT.
   - Hosted demo URL.
   - Public repo. The OSI `LICENSE` file already exists.
   - YouTube video under 3 minutes (script: `video-script-ladder.md`).
   - README section for the ladder.
   - Feedback submission.
2. **Stale document references.** `devpost-ladder-draft.md` and `feedback-nebius-nvidia.md` say "v1 to v4". They
   should cite `evaluation/ladder-proposal-v5` too, since set D and the v4 prompt results live there.
3. **"Citation beyond file".** Nemotron sometimes cites a line past the end of the documentation. A likely fix is to
   state each file's line count in the payload. Test it with a pre-registered run: 4 of Gowtham's approved paid runs
   remain, and he must approve spending.
4. **Nemotron over-abstains** on documented naming rules. It is safe but limits usefulness. The guided builder covers
   the gap for now.
5. **The workspace (`static/index.html`) was not restyled** to the new standard, and the ladder is not yet wired into
   the main workspace receipt.

## Rules to keep
- **Don't commit or push**, and add no AI attribution. Gowtham owns commits.
- **No paid model or Sandbox runs** without Gowtham's explicit approval. For benchmarks on his key, use only cheap
  models.
- **Don't read or print `.env`**, tokens or credentials. Keep raw third-party data out of the repo.
- **Keep claims honest:**
  - Don't call the receipt tamper-proof.
  - Don't present it as an autonomous agent.
  - Keep publishing the Sonnet comparison.
