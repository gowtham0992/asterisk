"""Consent-bound proposal preparation. No credentials or network transport here."""
import copy
import importlib.util
import threading
import json
from datetime import datetime, timezone
from pathlib import Path
from .intake import validate_files, open_inputs
from .review import executor
from .errors import ProposalRejected
from .prompt_contract import application_prompt

_path = Path(__file__).resolve().parents[2] / 'evaluation/extraction-v3/proposal.py'
_loader = importlib.util.spec_from_file_location('review_proposal', _path)
proposal = importlib.util.module_from_spec(_loader)
_loader.loader.exec_module(proposal)


class ProposalRequest:
    """One reviewed payload, one bounded completion, then explicit local review.

    The caller supplies a budget-enforcing completion adapter. This class never
    initializes a provider, retries, or treats upload consent as binding consent.
    """
    def __init__(self, files, claim, documentation=None, projection=None, evaluation_intent=None):
        validate_files(files)
        if not isinstance(claim, str) or not 10 <= len(claim.strip()) <= 3000:
            raise ValueError('Describe the claim in 10–3000 characters')
        self._files = copy.deepcopy(files)
        self._messages = (proposal.request(self._files, claim.strip()) if documentation is None else
                          [{'role': 'system', 'content': proposal.PROMPT}, {'role': 'user', 'content': ''}])
        if documentation is not None:
            if (not isinstance(documentation, list) or
                not all(isinstance(name, str) and name in files for name in documentation) or
                len(set(documentation)) != len(documentation)):
                raise ValueError('Documentation must list distinct supplied filenames')
            profiles = {}
            for name, text in self._files.items():
                if name in documentation:
                    lines = text.splitlines()
                    profiles[name] = {'bytes': len(text.encode()), 'kind': 'documentation',
                        'lines': [{'line': i, 'text': line} for i, line in enumerate(lines[:100], 1)],
                        'truncated': len(lines) > 100, 'total_lines': len(lines)}
                else:
                    # Profile by the selected role, not a special filename.
                    suffix = Path(name).suffix.lower()
                    alias = 'source' + (suffix if suffix in ('.csv', '.json') else '.txt')
                    profiles[name] = proposal.v2.profile({alias: text})[alias]
            self._messages[1]['content'] = json.dumps({'claim': claim.strip(), 'files': profiles}, ensure_ascii=False)
        # The model needs definitions wherever they occur in the supplied
        # documentation. Historical evaluation profiles cap at 100 lines;
        # leave those frozen experiments intact but do not inherit that cap
        # in the application's consent-bound request.
        data = json.loads(self._messages[1]['content'])
        for name, profile in data['files'].items():
            if profile.get('kind') == 'documentation':
                text = self._files[name]
                if len(text.encode()) > 100_000:
                    raise ValueError('Documentation exceeds the model preview limit; select a smaller complete source or an explicitly scoped excerpt')
                lines = text.splitlines()
                profile.update(lines=[{'line': i, 'text': line} for i, line in enumerate(lines, 1)],
                               truncated=False, total_lines=len(lines))
        self._messages[1]['content'] = json.dumps(data, ensure_ascii=False)
        self._messages[0]['content'] = application_prompt(proposal.PROMPT)
        if len(executor.canonical(self._messages).encode()) > 100_000:
            raise ValueError('Model preview exceeds 100 KB; reduce the selected sources')
        self._payload = {
            'messages': self._messages,
            'documentation_files': copy.deepcopy(documentation),
            'input_hashes': {name: executor.sha(text) for name, text in self._files.items()},
            'maximum_output_tokens': 4000,
            'timeout_seconds': 60,
            'provider': 'Nebius Token Factory',
            'model': 'nvidia/nemotron-3-super-120b-a12b',
            'estimated_reservation_usd': ((len(json.dumps(self._messages, ensure_ascii=False).encode()) + 128) * .3 + 4000 * .9) / 1e6,
            'estimate_scope': 'Retained evaluation token rates; provider billing is not verified. Existing $10 global and $1 cumulative extraction caps apply.',
        }
        if evaluation_intent is not None:
            from ..evaluation_intent import supported
            self._payload['evaluation_intent'] = supported(evaluation_intent)
        if projection is not None:
            from .projection import validate_projection
            self._payload['client_projection'] = validate_projection(projection, self._files)
        if len(executor.canonical(self._payload).encode()) > 150_000:
            raise ValueError('Recorded upload payload exceeds 150 KB')
        self._hash = executor.sha(executor.canonical(self._payload))
        self._lock = threading.Lock()
        self._used = False

    def preview(self):
        return {**copy.deepcopy(self._payload), 'payload_hash': self._hash,
                'notice': 'Documentation and profiles include source values. Review the exact messages before permitting upload. No scientific confirmation is included.'}

    def submit(self, payload_hash, accepted, complete):
        if accepted is not True or payload_hash != self._hash:
            raise ValueError('Approve this exact payload before requesting a proposal')
        with self._lock:
            if self._used:
                raise ValueError('This request was already attempted; review a new request to retry')
            # Consume before the call: a timeout may still have incurred a charge.
            self._used = True
        consent_at = datetime.now(timezone.utc).isoformat()
        result = complete(copy.deepcopy(self._messages), 4000, 60)
        try:
            content = result.get('content') if isinstance(result, dict) else None
            if not isinstance(content, str) or len(content.encode()) > 100_000:
                raise ValueError('Invalid or oversized model proposal')
            spec = proposal.parse(content)
            if spec.get('status') == 'insufficient':
                return {'status': 'insufficient', 'missing': spec['missing'],
                        'payload_hash': self._hash, 'session': None}
            session = open_inputs(executor.canonical(spec), self._files)
        except (ValueError, TypeError, KeyError, IndexError, RecursionError):
            raise ProposalRejected() from None
        session.model_proposal = {
            'schema_version': 1,
            'approved_payload': copy.deepcopy(self._payload),
            'payload_hash': self._hash,
            'consent_recorded_at': consent_at,
            'response_text': content,
            'scope': 'Locally recorded request and response. Not provider-authenticated provenance, verified reviewer identity, or scientific evidence.',
        }
        return {'status': 'review_required', 'payload_hash': self._hash,
                'session': session}
