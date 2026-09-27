# RC5: exported programs and runtime provenance

22 September 2026. This closes the remaining implementation follow-ups from Fable's RC3 review without adding detector categories. RC4's receipt scope and reviewer-independence changes remain in place.

## Changes and boundaries

- New receipts retain the exact bootstrap and primitive driver used by their runner. The exporter checks their hashes against execution metadata before writing them. Historical v4 receipts lacking those source bytes explicitly say they were not retained; they no longer get an unrelated exploration bootstrap substituted.
- Both configured-image paths require the current driver hash. Environment overrides require `ASTERISK_PROBE_DRIVER_SHA256`. The launcher hashes the actual `/opt/asterisk/primitive_main.py` inside the Sandbox and exits before execution if it differs. Existing per-measurement implementation/input/argument checks remain. The baked driver itself is unchanged, so a new image was unnecessary.
- The standalone remote replay command recomputes the permitted verdict from replayed measurements. A clear verdict also requires a consistent recorded binding confirmation tied to the replayed files, arguments and claim. A forged verdict fails even if its unsigned manifest is regenerated. This checks consistency, not the identity of the person who confirmed it.
- The receipt and bundle explicitly state that the primitive hash covers five measurement modules, not the host renderer. Neither an unsigned manifest nor replay authenticates the receipt's author. A person who rewrites every artifact and its confirmation can still create an internally consistent unsigned record; no signature or attestation is claimed.
- Identity diagnostics now flag invisible format characters and mixed Latin/Greek/Cyrillic scripts. They remain warnings, not normalization or comprehensive homoglyph detection. Exact inputs and measured verdicts are unchanged.
- README and historical reports point to this release status. The v4 bake script records the driver hash needed by the runtime.

## Observed verification

294 Python tests passed, 9 skipped (optional sklearn-dependent tests). New provenance tests were observed failing before implementation; five invisible/mixed-script cases also failed before the diagnostic fix. The suite includes a replay test that changes the recorded verdict and regenerates the manifest: measurement replay matches, but verdict verification fails with exit code 1.

Live Nebius Sandbox checks used only original two-row synthetic CSVs, no inference and no research datasets. Both LF and CRLF runs completed with a separate matching replay, correct witness counts, and matching exported bootstrap/driver hashes. The standalone replay CLI then remotely replayed the CRLF receipt and returned both measurement and verdict matches. These are development checks, not an acceptance or human-utility result. One initial fixture omitted the required citation and failed at submission; after supplying the CSV header citation, the complete workflow passed. The initial restricted-network attempt also failed closed.

The first extracted-suite attempt caught two replay fixtures depending on local image metadata. The fixtures now supply explicit synthetic image/driver configuration and work without local runtime state. The earlier RC5 candidate snapshot is retained as superseded.

The release packet builder verifies allowlisted source hashes and runs tests in a disposable extracted copy using installed dependencies. It does not certify a fresh dependency installation or hosted operation. No new visual browser check was performed in this follow-up.

## Frozen configuration

- Snapshot: `.data/primitive-v4/freeze-rc5-verified-2026-09-22/snapshot.json`; hash recorded in `current-freeze.json`.
- Primitive implementation: `d718f875426d0ae9be9358e08c3c3e0a378c1e8dcc6ced0c7d989f3774d110e3` (unchanged).
- Driver SHA-256: `cf87ab3ec129a16c6f5836c14ba0e3d3683bc72e98c47fdb48fe0ab65f6fc64a` (unchanged).
- Existing image: `80519d96-3de8-4f48-95ed-2de62a8351d4`.
- Launcher/bootstrap changed and is retained per new receipt; it is covered by the full source snapshot, not the primitive hash.

Earlier archives and snapshots are unchanged. Live RC3 proposals remain known-case development results; V3 acceptance remains failed. Independent human usefulness, deployment, public repository publication, video and submission remain outstanding. Hosting stays paused. No AWS resources were created by this work.
