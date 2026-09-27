"""Explain a blocked review without changing its policy or accepting an extraction."""
import copy

DUPLICATE_ERROR = 'Duplicate sample or conflicting cross-partition sample'


def annotate_repetition_error(exc, spec, files, executor):
    """Use the same executor on a throwaway policy; retain the original exception.

    This is structural diagnostics, not evidence that records are retransmissions.
    The diagnostic extraction is discarded and never becomes a saved preparation.
    A different blocking error leaves the original, less-specific guidance intact.
    """
    if str(exc) != DUPLICATE_ERROR:
        return exc
    diagnostic = copy.deepcopy(spec)
    for source in diagnostic['sources']:
        source['deduplicate'] = True
    try:
        executor.extract(diagnostic, files)
    except (ValueError, TypeError, KeyError) as diagnostic_error:
        if isinstance(diagnostic_error, executor.ExtractionError) and str(diagnostic_error) == DUPLICATE_ERROR:
            exc.review_issue = 'Repeated observations have conflicting assignments'
    else:
        exc.review_issue = 'Repeated observations agree under current binding'
    return exc
