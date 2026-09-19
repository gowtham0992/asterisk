# Fable feasibility experiment

Authorized by the user on 17 September 2026: execute Fable's proposal before reconsidering it. This is the 48-hour feasibility experiment in section 6, not a claim that the product pivot has passed.

Ten frozen cases, Ultra/Super/Nano, two independent trials each, identical system prompt and tool budget. Fifteen tool calls including submission, up to 400,000 aggregate reported tokens per run (a conservative byte-based reservation may stop a run earlier). Temperature zero. Each completion is limited to 8,192 tokens. No human hints or corrections during a trial. Model inspection tools: list files, read lines, write probe, run probe, submit verdict. Probes have 30 seconds in a pre-baked Python 3.12 image with NumPy, pandas, scipy and scikit-learn. Full inputs remain private under .data; source text is evidence, never agent instructions.

Case IDs correspond exactly to Fable's list: 01 DeepCDR callback; 02 realized DeepCDR seeded pair split; 03 MOLI variance filter; 04 MOLI scaler stage; 05 original DermaMNIST; 06 corrected DermaMNIST; 07 UCI Parkinsons random versus subject split; 08 synthetic sklearn pipeline; 09 missing patient mapping; 10 DeepResponse validation-driven selection, chosen from the review's referenced audit.

Freeze claims, input SHA-256 values, expected verdicts, required evidence and numeric oracles in .data/probe-pilot/frozen.json before model calls. Expected answers are never provided to the investigating model. Record every call, failure, repair, generated probe, observed output, usage and replay. Failed attempts count; a transport failure is reported, not silently replaced with a successful retry. Resume skips existing complete result records, including incomplete investigations.

Original thresholds: best model reaches at least 8/10 in each trial; zero confident false positives on cases 04/06/08/10; case 09 abstains in both trials; all retained successful probes replay identically; estimated cost below $2/case; median reviewer corrections at most one. Under 6/10, any false positive, wrong case-09 assertion, replay mismatch, cost over $5/case, or median corrections at least three fails its respective gate. Intermediate values are inconclusive. Numeric verdict agreement alone is not an evidence-correctness pass. Independent review of probe meaning is required. A malformed/incomplete output is not a clean verdict.

Faithfulness notes:
- Fable left case 07 predictor, features and random seed unspecified; these are explicitly fixed in its experiment.md before trials. Case 10 selects the pinned DeepResponse random training path and includes its scheduler implementation.
- Case 02 reconstructs upstream eligible tuples including response values (tuple equality uses them), then executes the seeded split under Python 3.12. It does not claim to recover a historical saved split from the old Python runtime. The host's oracle is cross-checked remotely before judging numeric results.
- Source licenses and data redistribution rights are not inferred from public visibility. MOLI and DeepResponse remain private evaluation inputs; no public bundle publishing. Molecular features and donor attributes from DeepCDR are omitted from agent inputs. DermaMNIST uses identity/partition projections only.
- Generated code replays in fresh isolated sandboxes. The host verifier checks hashes only. It never executes generated probe code on the Mac. This is the stated safety deviation from Fable's 'locally' replay instruction.
- Cost uses Fable's quoted token rates as estimates; the actual account balance and billed amount are not known. No claim of a $50 available balance.
- Two real, non-builder ML practitioners must do the five-minute comprehension check. Agents cannot stand in for them. Until collected, comprehension and adoption remain unmeasured.
- This compares Nemotron models as Fable requested. It does not establish an advantage over a general coding agent.

Run: .venv/bin/python evaluation/probe-pilot/bake.py; then .venv/bin/python evaluation/probe-pilot/run.py. Network access and the saved Nebius credentials are required. Investigations and ZIPs are stored in .data/probe-pilot/runs. No credentials enter prompts, probes, Sandbox environment or exported evidence.
