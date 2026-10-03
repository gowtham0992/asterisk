# Recovery correctness fixes — 2 October 2026

The manual recovery path now checks the definition shown to the researcher.

- Lookup expressions retain basename, field and character/prefix transformations. Previously the preview applied them but the emitted lookup key did not.
- Observation levels retain each source's own sample expression through `by_source` overrides.
- Duplicate selected filenames are rejected, rather than silently choosing the last file. File selections are validated against the total 16 MB bound before reading and applied atomically.
- A researcher can choose any partition column. Raw label counts are visible; unfamiliar labels require an explicit train/test/excluded assignment. The 12-label bound remains enforced.
- Numbered documentation is readable before selecting a citation, with 40-line pages and no automatic meaning confirmation.
- Input revisions and workflow revisions prevent obsolete provider/measurement/replay responses from replacing the current check.
- Character previews count Unicode code points, matching the Python engine.

## Verification

Three original correctness regressions failed before the fix and passed afterward. A Unicode regression likewise failed before its fix. The final suite passed 590 Python tests (9 existing scientific-trace skips) and 173 JavaScript tests.

A spec emitted by the actual JavaScript builder, with different train/test observation column names and a transformed filename lookup, ran through the actual Python engine and found exactly one shared donor affecting one of two evaluation rows.

A scratch browser journey chose an unfamiliar `arm` column, was refused while A/B labels remained unassigned, then assigned A to train and B to test. It extracted field 2 after basename, joined it to a donor mapping, and measured the same one shared donor. A second browser journey measured and saved the existing fictional patient example. Browser error logs were empty. No inference or Sandbox calls were needed for these regression checks.

These are developer-authored synthetic regression checks, not independent human validation or new held-out preparation accuracy. The shipping Nemotron prompt and historical 5/10 set-D result remain unchanged. Public repository access, final judge-access arrangements, video and submission remain release tasks; the video is on hold at the owner's request.
