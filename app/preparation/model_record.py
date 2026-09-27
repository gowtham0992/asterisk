"""Internal consistency checks for recorded model proposals, not attestation."""
import importlib.util
from pathlib import Path
from .review import executor

_loader = importlib.util.spec_from_file_location('record_proposal',
    Path(__file__).resolve().parents[2] / 'evaluation/extraction-v3/proposal.py')
proposal = importlib.util.module_from_spec(_loader)
_loader.loader.exec_module(proposal)


def verify_model_record(record, spec, files):
    if not isinstance(record, dict) or record.get('schema_version') != 1:
        raise ValueError('Invalid model proposal record')
    payload = record.get('approved_payload')
    if not isinstance(payload, dict) or len(executor.canonical(payload).encode()) > 150_000:
        raise ValueError('Invalid recorded upload payload')
    if executor.sha(executor.canonical(payload)) != record.get('payload_hash'):
        raise ValueError('Recorded upload payload hash mismatch')
    if 'evaluation_intent' in payload:
        from ..evaluation_intent import supported
        supported(payload['evaluation_intent'])
    if 'client_projection' in payload:
        from .projection import validate_projection
        validate_projection(payload['client_projection'], files)
    if payload.get('input_hashes') != {name: executor.sha(text) for name, text in files.items()}:
        raise ValueError('Model proposal refers to different source inputs')
    if not isinstance(record.get('consent_recorded_at'), str) or not record['consent_recorded_at']:
        raise ValueError('Missing model upload consent timestamp')
    response = record.get('response_text')
    if not isinstance(response, str) or len(response.encode()) > 100_000:
        raise ValueError('Invalid recorded model response')
    if executor.canonical(proposal.parse(response)) != executor.canonical(spec):
        raise ValueError('Model response differs from the original extraction proposal')
