"""Bounded preparation provenance for display; never grants a verdict."""
import json
from .verify_record import verify


def retained_preparation(files):
    text = files.get('preparation-review.json')
    if text is None:
        return None
    try:
        if not isinstance(text, str) or len(text.encode()) > 10_000_000:
            raise ValueError('Preparation context exceeds bounds')
        record = json.loads(text)
        verify(record)
        derived = record['review']['extraction']['files']
        if not derived or any(files.get(name) != content for name, content in derived.items()):
            raise ValueError('Prepared tables differ from supplied tables')
        passages = []
        for decision in record['review']['decisions']:
            for citation in decision['evidence']:
                # Re-read originals; a saved quote is never display authority.
                name = citation['file']
                first, last = citation['start_line'], citation['end_line']
                quote = '\n'.join(record['inputs'][name].splitlines()[first-1:last])
                item = {'file': name, 'first': first, 'last': last, 'quote': quote}
                if item not in passages:
                    passages.append(item)
        model = record.get('model_proposal')
        proposal = None
        if model:
            payload = model['approved_payload']
            def label(key, fallback):
                value = payload.get(key)
                return value[:200] if isinstance(value, str) and value.strip() else fallback
            proposal = {'model': label('model', 'Model unspecified'),
                        'provider': label('provider', 'Provider unspecified'),
                        'payload_hash': model['payload_hash'],
                        'consent_recorded_at': model['consent_recorded_at']}
        return {'model_proposal': proposal, 'actor': record['confirmation'].get('actor', 'Unrecorded reviewer'),
                'spec': record['review']['extraction']['spec'],
                'passages': passages[:12], 'passage_count': len(passages)}
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RecursionError):
        return {'error': 'The retained preparation could not be recomputed against these tables. Its interpretation is not displayed.'}
