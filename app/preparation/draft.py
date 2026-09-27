"""Unconfirmed preparation drafts; never accepted by the confirmed-record verifier."""
import copy
import json
from .review import executor
from .verify_record import policies_from


def save(session, review_hash):
    if session.review is None or review_hash != session.review['review_hash']:
        raise ValueError('Preview the current policy before saving a draft')
    result={'draft_version':1,'inputs':copy.deepcopy(session.files),
            'original_spec':copy.deepcopy(session.spec),
            'policies':policies_from(session.review)}
    if session.model_proposal is not None:
        from .model_record import verify_model_record
        verify_model_record(session.model_proposal,session.spec,session.files)
        result['model_proposal']=copy.deepcopy(session.model_proposal)
    result['draft_hash']=executor.sha(executor.canonical(result))
    if len(json.dumps(result).encode())>32_000_000:
        raise ValueError('Draft exceeds the 32 MB reopen limit')
    return result


def restore(record):
    required={'draft_version','inputs','original_spec','policies','draft_hash'}
    if not isinstance(record,dict) or record.get('draft_version')!=1 or not required<=record.keys() or set(record)-required-{'model_proposal'}:
        raise ValueError('Invalid preparation draft fields')
    body={key:value for key,value in record.items() if key!='draft_hash'}
    if executor.sha(executor.canonical(body))!=record['draft_hash']:
        raise ValueError('Draft hash mismatch')
    from .intake import open_inputs
    session=open_inputs(executor.canonical(record['original_spec']),record['inputs'])
    if 'model_proposal' in record:
        from .model_record import verify_model_record
        verify_model_record(record['model_proposal'],session.spec,session.files)
        session.model_proposal=copy.deepcopy(record['model_proposal'])
    session.preview(record['policies'])
    return session
