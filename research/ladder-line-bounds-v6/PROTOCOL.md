# Narrow citation-bound comparison — 7 October 2026

Question: does giving Nemotron exact documentation line counts reduce invalid citation ranges, without changing v4's semantic instructions or weakening abstention?

The previous exposed development comparison had six missed cases, all abstentions about unsupported or incompletely specified subject derivations, and two citation-bound errors. The earlier broader v5 rewrite worsened the exposed-set score from 4/10 to 3/10. This experiment isolates bounds rather than encouraging guessing.

Candidate v6 appends only citation-bound instructions and adds exact document line counts. The v4 documentation lists and every other payload field remain identical. The shipping default remains v4 throughout the comparison.

Eight cases, two trials per arm: 32 proposals, maximum one validator repair each, at most 64 calls. Conservative reservation rates $0.50/M input and $1.50/M output, $2 estimated ceiling; this is not provider billing. No retries after transport errors, no Sandbox calls, no judge reserve use. Secrets come from the existing local loader and are never recorded. Only identifier examples and documentation go to Nebius.

Fresh layouts:

- AT&T ORL archive: list the 400 original relative image filenames without retaining or transmitting image contents. Author a subject-separated split and an image-separated split. A third case withholds the directory meaning and must abstain. Credit AT&T Laboratories Cambridge. These are authored splits over a real filename index, not leakage findings in a published train/test split.
- UCI Pendigits: read the published .tra/.tes row counts, assign local row identifiers, and withhold writer mapping, coordinates and class values. Both variants must abstain despite the published writer-independent split description. Credit Alpaydin and Alimoglu, CC BY 4.0. The per-row uniqueness trap is not a subject mapping.
- Three original fictional spectroscopy fixtures: short join documentation, the same definition late in a long document, and a denied physical-subject binding.

References and requests are frozen in the private packet before model calls. The author also wrote the candidate and scorer. Cases are correlated and are not independently authored acceptance evidence. There are no human participants. Unsupported-case examples do not establish general absence of mapping in all dataset formats; only the supplied projection is in scope.

Promote only if v6 has no unsupported or false-reassuring proposals, gets every supported case correct in both trials, gains at least two correct attempts over v4, and reduces both invalid-first replies and citation-bound errors. Otherwise retain v4. Do not repeat a failed batch to pass.

Correct means the same subject grouping, sample-to-partition mapping and finding status as the reference; citation syntax is independently validated. Abstention controls require abstention, not just a non-clear verdict. A pending clear from a wrong binding counts against the candidate even though no human confirmation has occurred.

Scoring correction caught during trial 1: the provisional runner compared entire population objects, including citations and spec hashes. The corrected offline scorer compares only sample-to-partition mappings alongside grouping and status. Its test accepts equivalent citations and refuses inverted partitions. Original run records and scores are retained, model requests and promotion rules are unchanged, no new inference is required for correction.

Primary provenance:
https://www.cl.cam.ac.uk/research/dtg/attarchive/facedatabase.html
https://www.cl.cam.ac.uk/Research/DTG/attarchive/pub/data/att_faces.zip
https://archive.ics.uci.edu/dataset/81/pen+based+recognition+of+handwritten+digits
https://archive.ics.uci.edu/static/public/81/pen+based+recognition+of+handwritten+digits.zip

Private artifacts: .data/line-bounds-v6-20261007/{packet.json,freeze.json,orl-index.json,pendigits-index.json,budget.json,rescored.json}. Never include these in a public source packet.
