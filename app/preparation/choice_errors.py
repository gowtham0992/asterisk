"""Allowlisted repair guidance. Never reflect exception text or source values."""
MESSAGES = {
    'Repeated observations agree under current binding':
        'The selected observation IDs repeat. Combining them passes the structural checks with the current subject and partition choices. This does not establish that they are retransmissions. Review the documentation before explicitly choosing to combine; no policy has been changed.',
    'Repeated observations have conflicting assignments':
        'At least one repeated observation ID resolves to different subjects or partitions under these choices. Combining repeats cannot resolve that conflict. Inspect the original records and review the binding or obtain corrected source data; do not replace documented observation IDs with row numbers to hide it.',

    'Unique row identity cannot collapse retransmissions':
        'Each source record has a unique row identity, so retransmissions cannot be combined. Choose the documented observation-ID column or lookup before selecting the combine policy.',
    'Duplicate sample or conflicting cross-partition sample':
        'An observation ID repeats, or repeated records disagree on subject or partition. Inspect the repeated IDs. Combine them only if the documentation establishes retransmissions and their subject and partition agree; otherwise correct the identity or source data.',
    'Unmapped sample; coverage incomplete':
        'The lookup does not cover every source key. Check the source key, mapping key and mapping table. Supply the missing mappings before continuing; unmatched records cannot be silently dropped.',
    'Conflicting duplicate lookup identity':
        'A mapping key points to more than one identity. Inspect and correct the mapping table or choose the documented key. Asterisk cannot choose one conflicting identity for you.',
    'Both partitions must be nonempty':
        'These choices leave training or evaluation empty. Check the partition labels and exclusions. Both groups need at least one observation.',
    'Unlisted partition value; explicit exclusion required':
        'At least one source partition label has no assigned role. Assign every exact label to training, evaluation or exclusion, including differences in spaces and capitalization.',
    'Invalid or short prefix':
        'The identity prefix is invalid or longer than at least one source value. Use 1–128 characters and inspect short IDs; remove the prefix if the full identifier is intended.',
    'Column missing':
        'A selected identity column is absent from at least one source record. Check the selected column and complete the source records before previewing again.',
    'Lookup column missing':
        'The lookup key or identity column is absent from at least one mapping record. Check both selected columns and complete the mapping table.',
    'Identifier must be a nonempty bounded string; numeric coercion is forbidden':
        'At least one selected identifier is missing, empty, numeric, contains a null character or exceeds 4,096 characters. Check the identity counts and source values. Identifiers must be explicit text; Asterisk does not silently convert numbers.',
    'Policy citation too large':
        'A supporting passage exceeds 8,000 characters. Select a shorter passage that still supports the interpretation.',
    'Invalid policy citation range':
        'A supporting passage falls outside its source or spans more than 40 lines. Check every passage’s first and last line.',
}


def choice_error(exc):
    return MESSAGES.get(getattr(exc, 'review_issue', None)) or MESSAGES.get(str(exc))


UPLOAD_MESSAGES = {
    'Repeated observations agree under current binding':
        'The selected observation IDs repeat. Combining them passes the structural checks with the current subject and partition choices. This does not establish that they are retransmissions. Review the documentation before explicitly choosing to combine; no policy has been changed.',
    'Repeated observations have conflicting assignments':
        'At least one repeated observation ID resolves to different subjects or partitions under these choices. Combining repeats cannot resolve that conflict. Inspect the original records and review the binding or obtain corrected source data; do not replace documented observation IDs with row numbers to hide it.',

    'Use flat CSV, JSON, Markdown or text filenames; no hidden paths':
        'Rename files using English letters, numbers, spaces, dots, underscores or hyphens, starting with a letter or number. Use a .csv, .json, .md or .txt extension and keep the filename stem to 160 characters. Parentheses and directory paths are not supported.',
    'Model preview exceeds 100 KB; reduce the selected sources':
        'The model payload exceeds 100 KB. Reduce the selected sources or use shorter documentation excerpts, keeping the definitions needed for the claim. Review the new payload before continuing.',
    'Sources exceed 10 MB per file or 16 MB total':
        'Choose files no larger than 10 MB each and 16 MB combined. Do not remove observations merely to make a scientific check fit; prepare a documented projection of the needed columns instead.',
}


def upload_error(exc):
    return UPLOAD_MESSAGES.get(str(exc))
