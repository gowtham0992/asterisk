# Text-list intake — 7 October 2026

The new-check workflow now suggests data for `.txt` files whose every nonempty line is a filename, optionally followed by a numeric class label. Markdown and reStructuredText remain documentation. Plain identifiers, mixed prose and empty text remain documentation until the person changes the role. This is a convenience suggestion, not scientific interpretation.

Text files show a six-line, 2,400-character local preview and an explanation of their current role. Data lists expose the `value` column; no example-sharing checkbox is selected automatically. A numeric class label remains part of the original line. The model or user still defines the extraction, and confirmation and measurement are unchanged.

Verification: the new regression failed on the old behavior, then all 180 JavaScript tests and 28 focused Python lifecycle/proposal tests passed. In the actual browser, the original UCF101 train and test lists defaulted to data, researcher notes stayed documentation, both example-sharing boxes were unchecked, and the six-line preview preserved the training class labels. Manually changing a list back to documentation updated the form. No model, Sandbox or paid call was made.

This removes the two file-role corrections observed in the prior UCF101 trial. It does not establish human usefulness or improve the retained model acceptance score.
