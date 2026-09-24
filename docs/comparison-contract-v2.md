# Comparison contract v2

New comparisons report `schema_version: 2` and `identity_membership_comparable`. The latter requires matching claim, evaluation intent, binding, sample universe and identity assignments. It does not require a partition move and does not establish equality of other feature values or source files.

The misleading `partition_only_change` field is no longer emitted. JSON consumers must migrate to the new name and honor its narrower guarantee. The current browser viewer handles older records with an explicit limitation; original archived records are not rewritten. Older third-party consumers of the previous field need an update.

Changed files remain separately listed. A changed feature with unchanged sample identities remains comparable for exact-ID overlap, but does not establish that only the split changed or that any score difference was caused by it.

The comparison's replay indicator now requires a recorded matching replay associated with the selected entity measurement. A replay for another measurement cannot satisfy it. This is a report of the retained record, not new remote execution or proof of authenticity.

The local CLI preserves UTF-8 source line endings when importing and comparing receipts. Previously text-mode reads converted CRLF to LF. This could change exported source bytes and prevent comparison against a byte-preserving prior receipt. Neither fix changes the trusted overlap algorithm.

Verification: 264 Python tests passed, 9 skipped; the standalone comparison UI tests passed. New regressions first failed on the old implementation, then passed after the changes: feature/document edits, unchanged inputs, unrelated replay IDs, and CRLF import/export/recheck. Run UI checks with `node tests/comparison-ui.test.mjs` from the product directory.

Jev was used only as an external development reviewer. Two bounded passes checked wording and six properties of the changed comparison function. Original outputs are retained outside the product under research/jev-code-review. These are model judgments, not independent certification. The actual defects and fixes were verified locally.

This local iteration is not a new frozen release. Existing release snapshots are historical and have not been relabeled as covering these changes.

Browser verification used the existing group-respecting revision: the comparison displayed the new scope notice and the confirmation-aware verdict label. Opening the comparison moves keyboard focus into it; closing restores focus to the originating button. Raw enum labels in the before/after cards are replaced with plain-language verdicts. Unknown values cannot be displayed as a supported verdict.
