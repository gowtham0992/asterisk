"""Ladder endpoints: local measurement, the exact proposal payload, a Nemotron proposal through Nebius Token
Factory, and a replay in a Nebius Sandbox. Only /propose calls a model and only /replay runs remote code."""
import hashlib
import json
import os
import time
import sqlite3

from fastapi import HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from . import ladder_proposal
from .ladder import LadderError, measure
from .ladder_sandbox import replay
from .preparation.review import executor
from .sandbox import SandboxError

BASE = 'https://api.tokenfactory.nebius.com/v1/'
# Super with the v4 prompt ships by default (evaluation/ladder-proposal-v5). Ultra passed fresh set B but did not replicate
# on set C, so it stays an option.
MODELS = {'nvidia/nemotron-3-super-120b-a12b': 'Nemotron 3 Super', 'nvidia/Nemotron-3-Ultra-550b-a55b': 'Nemotron 3 Ultra'}
DEFAULT_MODEL = 'nvidia/nemotron-3-super-120b-a12b'


class LadderFile(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str = Field(min_length=1, max_length=300)
    content: str = Field(max_length=16_000_000)


class LadderRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    spec: dict
    files: list[LadderFile] = Field(min_length=1, max_length=80)
    confirmed: list[str] = Field(default_factory=list, max_length=8)


class ProposalRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    claim: str = Field(min_length=3, max_length=1000)
    files: list[LadderFile] = Field(min_length=1, max_length=80)
    documentation: list[str] = Field(min_length=1, max_length=20)
    share_examples: list[tuple[str, str]] = Field(default_factory=list, max_length=20)
    model: str = DEFAULT_MODEL


def _files(items):
    files = {}
    for item in items:
        if item.name in files:
            raise HTTPException(422, 'Each file name may appear once.')
        files[item.name] = item.content
    if sum(len(v.encode()) for v in files.values()) > executor.MAX_BYTES:
        raise HTTPException(413, 'Ladder inputs exceed 16 MB total.')
    return files


def _messages(body, files):
    if body.model not in MODELS:
        raise HTTPException(422, 'Choose Nemotron 3 Super or Nemotron 3 Ultra.')
    try:
        return ladder_proposal.request(body.claim, files, body.share_examples, body.documentation)
    except LadderError as exc:
        raise HTTPException(422, str(exc)) from None


def token_factory(model, key):
    """A completion function for ladder_proposal.propose: one bounded Token Factory call per invocation."""
    from openai import OpenAI
    usage = {'calls': 0, 'total_tokens': 0}

    def complete(messages, maximum, timeout):
        with OpenAI(base_url=os.getenv('NEBIUS_BASE_URL', BASE), api_key=key, timeout=timeout, max_retries=0) as client:
            response = client.chat.completions.create(model=model, messages=messages, temperature=0, max_tokens=maximum,
                                                      response_format={'type': 'json_object'})
        usage['calls'] += 1
        usage['total_tokens'] += response.usage.total_tokens if response.usage else 0
        return response.choices[0].message.content or ''
    return complete, usage


def register(app, owner, completion=token_factory, sandbox=replay, connect=None):
    store = None
    if connect is not None:
        from .ladder_receipts import register as register_receipts
        store = register_receipts(app, connect, owner, LadderRequest, _files)
    @app.post('/api/ladder')
    def ladder(body: LadderRequest, request: Request):
        owner(request)
        try:
            return measure(body.spec, _files(body.files), body.confirmed)
        except LadderError as exc:
            raise HTTPException(422, str(exc)) from None

    @app.post('/api/ladder/preview')
    def preview(body: ProposalRequest, request: Request):
        """Exactly what /propose would send, so a person can read it first. No network call."""
        owner(request)
        messages = _messages(body, _files(body.files))
        text = json.dumps(messages, ensure_ascii=False)
        return {'model': body.model, 'model_name': MODELS[body.model], 'provider': 'Nebius Token Factory',
                'messages': messages, 'characters': len(text), 'payload_sha256': hashlib.sha256(text.encode()).hexdigest()}

    @app.post('/api/ladder/propose')
    def propose(body: ProposalRequest, request: Request):
        owner(request)
        files = _files(body.files)
        messages = _messages(body, files)
        key = os.getenv('NEBIUS_API_KEY')
        if not key:
            raise HTTPException(503, 'Add NEBIUS_API_KEY to the local .env file and restart Asterisk.')
        complete, usage = completion(body.model, key)
        start = time.monotonic()
        try:
            proposal, attempts = ladder_proposal.propose(body.claim, files, complete, body.share_examples,
                                                         documentation=body.documentation)
        except LadderError as exc:
            raise HTTPException(422, f'Nemotron did not return a usable ladder after one repair: {exc}') from None
        except Exception:
            raise HTTPException(502, 'Nebius Token Factory did not complete the request. Check credits and model access, then retry.') from None
        return {'proposal': proposal, 'attempts': [{'error': a['error']} for a in attempts], 'model': body.model,
                'model_name': MODELS[body.model], 'provider': 'Nebius Token Factory', 'calls': usage['calls'],
                'total_tokens': usage['total_tokens'], 'seconds': round(time.monotonic() - start, 2),
                'payload_sha256': hashlib.sha256(json.dumps(messages, ensure_ascii=False).encode()).hexdigest()}

    @app.post('/api/ladder/replay')
    def replay_ladder(body: LadderRequest, request: Request):
        who = owner(request)
        project = os.getenv('NEBIUS_PROJECT_ID') or os.getenv('NEBIUS_AI_PROJECT')
        try:
            result, provenance = sandbox(body.spec, _files(body.files), body.confirmed, os.getenv('NEBIUS_API_KEY'), project)
        except LadderError as exc:
            raise HTTPException(422, str(exc)) from None
        except SandboxError as exc:
            raise HTTPException(502, str(exc)) from None
        response = {'result': result, 'provenance': provenance}
        if store is not None:
            try:
                saved = store.save(who, body.spec, _files(body.files), result, provenance)
                response['receipt_id'] = saved['id']
            except (sqlite3.Error, OSError):
                response['receipt_error'] = 'Replay matched, but workspace storage failed. Download the JSON receipt now; another replay is not needed.'
        return response
