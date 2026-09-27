"""Bounded local intake for the experimental review editor; no inference."""
import json
import re
import copy
from .review import executor,CORRECTABLE_ERRORS
from .session import ReviewSession
from .verify_record import verify,policies_from
from .choice_errors import choice_error
from .repetition_diagnostic import annotate_repetition_error


def reopen(record_text):
    if not isinstance(record_text,str) or len(record_text.encode())>32_000_000:
        raise ValueError('Saved review exceeds 32 MB')
    try:record=json.loads(record_text,object_pairs_hook=executor.unique)
    except (ValueError,RecursionError) as exc:raise ValueError('Invalid saved review JSON') from exc
    if isinstance(record,dict) and 'draft_version' in record:
        from .draft import restore
        return restore(record)
    verify(record)
    session=open_inputs(executor.canonical(record['review']['original_spec']),record['inputs'])
    session.model_proposal=copy.deepcopy(record.get('model_proposal'))
    session.preview(policies_from(record['review']))
    return session


def validate_files(files):
    if not isinstance(files,dict) or not 1<=len(files)<=80:
        raise ValueError('Choose 1–80 source files')
    total=0
    for name,content in files.items():
        if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_. -]{0,159}\.(csv|json|md|txt)',name,re.I):
            raise ValueError('Use flat CSV, JSON, Markdown or text filenames; no hidden paths')
        if not isinstance(content,str):raise ValueError('Source contents must be UTF-8 text')
        size=len(content.encode());total+=size
        if size>10_000_000 or total>16_000_000:raise ValueError('Sources exceed 10 MB per file or 16 MB total')


def open_inputs(spec_text,files):
    if not isinstance(spec_text,str) or len(spec_text.encode())>100_000:
        raise ValueError('Use an extraction proposal below 100 KB')
    validate_files(files)
    try:spec=json.loads(spec_text,object_pairs_hook=executor.unique)
    except (ValueError,RecursionError) as exc:raise ValueError('Invalid or duplicate-key proposal JSON') from exc
    issue=None
    rejection=None
    try:executor.extract(spec,files)
    except executor.ExtractionError as exc:
        if str(exc) not in CORRECTABLE_ERRORS:raise
        rejection=str(exc)
    if rejection is not None:
        # Leave the exception handler first: its traceback retains the original
        # parsed tables. The diagnostic must not hold two full parses at once.
        issue=choice_error(annotate_repetition_error(executor.ExtractionError(rejection),spec,files,executor))
    session=ReviewSession(spec,files)
    session.proposal_issue=issue
    return session
