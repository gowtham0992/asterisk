# Asterisk

Draft only. Track: Best Apps and Agents. Do not submit before the testing URL, public repository and video exist and the owner verifies eligibility and rights.

## Tagline

A split receipt for a claim about unseen subjects.

## Inspiration

Different samples can come from the same patient, speaker or specimen. A claim about unseen subjects needs evidence that the underlying identities are separated. A reviewer should be able to inspect that evidence without accepting an AI-generated explanation on trust.

## What it does

Asterisk helps a researcher document one condition: exact recorded entity identities do not overlap between selected training and evaluation partitions. Upload a split, identity mapping and documentation. Review the columns and partition labels proposed by NVIDIA Nemotron Super, including cardinalities computed from every row. Confirm the binding, run the check, inspect a witness and export a replayable receipt. Inspect all affected rows and a proposed partition repair, then approve and check a separate revision without overwriting the original. Similar-looking IDs are flagged without silently merging them.

## How we built it

A Python/FastAPI application serves the review interface and retains receipts in SQLite. Nemotron Super runs through Nebius Token Factory to propose a cited binding. Application-owned Python computes the measurement in an immutable Nebius Sandbox; a fresh Sandbox repeats it with the same inputs and arguments. The result and confirmed assumption are retained with file hashes and implementation source. Any model prose is labeled unverified. The shipped workflow does not generate checker code.

## What we learned

A deterministic checker does not make an incorrectly chosen question correct. In v3, the model used a partition label as the sample identifier and then blamed the data. V4 requires binding review before execution and reports errors using the actual column and cardinality. We also disabled checkpoint selection after acceptance failures rather than expanding claims beyond observed support.

## Evidence and limitations

V3 acceptance failed: 9/12 primary cases matched per trial and 4/6 defect–repair pairs passed, although all 44 measurements replayed. V4 is a new development iteration. A known PTB-XL development check measured 623 shared patient IDs affecting 692 evaluation rows with matching replay; it is not a newly independent evaluation. A separate general-agent practical comparison matched all 18 authored variant labels, so we claim no correctness advantage over coding agents. The value hypothesis is easier human verification; independent evidence review and practitioner comprehension remain unmeasured.

A five-seed development experiment on public repeated recordings found a 0.117-point mean MAE increase after removing planted participant overlap (1.60% of mean original MAE), versus 0.004 for a size-matched row-removal control. The control is a disclosed post-review extension. This is a modest descriptive result in one constructed setting, not a general effect or a discovered published defect.

This checks recorded IDs under a human-confirmed binding. It does not certify an experiment, infer missing identities, detect image duplicates, quantify accuracy inflation or prove scientific independence. Confirmation records an assumption. Byte hashes and repeatability do not prove semantic correctness.

## Platform feedback

Nebius inference and Sandboxes let us separate model interpretation from isolated, repeatable measurements. Matching the baked image to the trusted source is essential; failed provenance or replay suppresses a verdict. Sandbox beta access was required and was exercised. We would value clearer SDK/version alignment and consistent model/tool-schema support documentation. These are development observations, not a benchmark across providers.

## Before submitting

- Add the real public repository URL with detectable MIT license and verified setup.
- Add a working HTTPS test URL and judge credentials through the testing field.
- Add a public YouTube video under three minutes showing the actual workflow.
- Replace unmeasured study status only with real committed records.
- Verify participant eligibility, third-party rights, event dates and final track requirements.
