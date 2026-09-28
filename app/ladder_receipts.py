"""Owner-scoped saved ladder measurements. Only server-computed results are stored."""
import hashlib
import json
import secrets
from datetime import datetime, timezone
from html import escape

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, Response

from .ladder import LadderError, measure, render, digest


MAX_RECEIPT_STORAGE_BYTES = 256 * 1024 * 1024


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


class Receipts:
    def __init__(self, connect):
        self.connect = connect

    def db(self):
        db = self.connect()
        db.execute('CREATE TABLE IF NOT EXISTS ladder_receipts '
                   '(id TEXT PRIMARY KEY, owner TEXT NOT NULL, created TEXT NOT NULL, payload TEXT NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS ladder_proposals '
                   '(id TEXT PRIMARY KEY, owner TEXT NOT NULL, payload TEXT NOT NULL)')
        return db

    def record_proposal(self, owner, response, files, prompt_version):
        pid = secrets.token_hex(12)
        record = {key: response[key] for key in ('model', 'model_name', 'provider', 'payload_sha256', 'attempts')}
        record.update({'id': pid, 'created_at': datetime.now(timezone.utc).isoformat(),
                       'prompt_version': prompt_version,
                       'proposed_spec_hash': digest(response['proposal'].get('spec')),
                       'input_hashes': {n: hashlib.sha256(v.encode()).hexdigest() for n, v in files.items()},
                       'proposal_status': response['proposal']['status']})
        with self.db() as db:
            db.execute('INSERT INTO ladder_proposals VALUES (?,?,?)', (pid, owner, canonical(record)))
        return pid

    def binding_origin(self, owner, pid, spec, files):
        if not pid:
            return {'kind': 'user_supplied', 'note': 'Supplied by the user; no server-recorded model proposal is linked. Authorship is not verified.'}
        with self.db() as db:
            row = db.execute('SELECT payload FROM ladder_proposals WHERE id=? AND owner=?', (pid, owner)).fetchone()
        if not row:
            raise HTTPException(404, 'Proposal not found in this workspace.')
        record = json.loads(row['payload'])
        return {**record, 'kind': 'recorded_model_proposal',
                'edited': digest(spec) != record['proposed_spec_hash'],
                'inputs_changed': record['input_hashes'] != {n: hashlib.sha256(v.encode()).hexdigest() for n, v in files.items()},
                'note': 'Provider invocation recorded by this server; subsequent changes are compared by hash. Editor identity is not verified.'}

    def save(self, owner, spec, files, result, provenance=None, proposal_id=None):
        # Caller supplies the actual server measurement, never a client verdict.
        record = {'schema': 'asterisk-saved-ladder/1', 'id': secrets.token_hex(12),
                  'created_at': datetime.now(timezone.utc).isoformat(),
                  'spec': spec, 'files': files, 'result': result,
                  'binding_origin': self.binding_origin(owner, proposal_id, spec, files),
                  'execution': {'kind': 'sandbox_replay' if provenance else 'local',
                                'provenance': provenance},
                  'confirmation': {'levels': result.get('confirmed_levels', []),
                                   'scope': 'Self-reported meaning confirmation; reviewer identity is not verified.'}}
        record['integrity_sha256'] = hashlib.sha256(canonical(record).encode()).hexdigest()
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            count = db.execute('SELECT COUNT(*) FROM ladder_receipts WHERE owner=?', (owner,)).fetchone()[0]
            if count >= 30:
                raise HTTPException(409, 'This workspace has 30 receipts. Export and delete an old receipt before saving another.')
            size = db.execute('SELECT COALESCE(SUM(length(CAST(payload AS BLOB))),0) FROM ladder_receipts').fetchone()[0]
            if size + len(canonical(record).encode()) > MAX_RECEIPT_STORAGE_BYTES:
                raise HTTPException(409, 'Receipt storage is full. Export your result and contact the workspace operator.')
            db.execute('INSERT INTO ladder_receipts VALUES (?,?,?,?)',
                       (record['id'], owner, record['created_at'], canonical(record)))
        return public(record)

    def get(self, owner, rid):
        with self.db() as db:
            row = db.execute('SELECT payload FROM ladder_receipts WHERE id=? AND owner=?', (rid, owner)).fetchone()
        if not row:
            raise HTTPException(404, 'Ladder receipt not found in this workspace.')
        record = json.loads(row['payload'])
        expected = record.pop('integrity_sha256')
        actual = hashlib.sha256(canonical(record).encode()).hexdigest()
        record['integrity_sha256'] = expected
        if actual != expected:
            raise HTTPException(409, 'The saved ladder record changed. Its result cannot be displayed or exported.')
        return record

    def list(self, owner):
        with self.db() as db:
            rows = db.execute('SELECT id FROM ladder_receipts WHERE owner=? ORDER BY created DESC', (owner,)).fetchall()
        return [{'id': record['id'], 'created_at': record['created_at'],
                 'claim': record['result']['claim']['text'], 'finding': record['result']['finding'],
                 'execution': record['execution']['kind']}
                for row in rows for record in [self.get(owner, row['id'])]]

    def delete(self, owner, rid):
        self.get(owner, rid)
        with self.db() as db:
            db.execute('DELETE FROM ladder_receipts WHERE id=? AND owner=?', (rid, owner))


def public(record):
    # The browser can inspect results and the spec without re-downloading inputs.
    return {key: value for key, value in record.items() if key != 'files'}


def receipt_html(record):
    execution = record['execution']
    text = ('Matched a fresh Nebius Sandbox replay, as attested by this Asterisk server.' if execution['kind'] == 'sandbox_replay'
            else 'Measured on the Asterisk server. No Sandbox replay is recorded for this receipt.')
    origin = record.get('binding_origin', {'kind': 'legacy', 'note': 'This older receipt does not record proposal origin.'})
    metadata = '<section aria-label="Receipt record"><h2>Execution and limits</h2>'
    metadata += '<h2>Who proposed the binding</h2>'
    if origin['kind'] == 'recorded_model_proposal':
        metadata += '<p>Proposed by ' + escape(origin['model_name']) + ' (' + escape(origin['model']) + '). Prompt ' + escape(origin['prompt_version']) + '.</p>'
        metadata += '<p>Specification edited since proposal: ' + str(origin['edited']) + '; inputs changed: ' + str(origin['inputs_changed']) + '.</p>'
        metadata += '<p>Request SHA-256: ' + escape(origin['payload_sha256']) + '; attempts: ' + str(len(origin['attempts'])) + '.</p>'
    metadata += '<p>' + escape(origin['note']) + '</p>'
    metadata += '<p>' + escape(text) + '</p><p>Saved ' + escape(record['created_at']) + '</p>'
    metadata += '<p>' + escape(record['confirmation']['scope']) + '</p>'
    metadata += '<p>This unsigned receipt records an interpretation and a measurement. '
    metadata += 'It does not authenticate the source data or prove scientific validity. '
    metadata += 'Raw inputs and model proposal history are not embedded in this HTML.</p>'
    metadata += '<details><summary>Inspect the saved measurement record</summary><pre style="white-space:pre-wrap;overflow-wrap:anywhere">'
    metadata += escape(json.dumps(public(record), indent=2, ensure_ascii=False)) + '</pre></details></section>'
    return render(record['result']).replace('</main>', metadata + '</main>')


def register(app, connect, owner, request_model, parse_files):
    store = Receipts(connect)

    @app.get('/api/ladder/receipts')
    def listing(request: Request):
        return store.list(owner(request))

    @app.post('/api/ladder/receipts', status_code=201)
    def save(body: request_model, request: Request):
        who = owner(request)
        files = parse_files(body.files)
        try:
            result = measure(body.spec, files, body.confirmed)
        except LadderError as exc:
            raise HTTPException(422, str(exc)) from None
        return store.save(who, body.spec, files, result, proposal_id=body.proposal_id)

    @app.get('/api/ladder/receipts/{rid}')
    def read(rid: str, request: Request):
        return public(store.get(owner(request), rid))

    @app.get('/api/ladder/receipts/{rid}/export')
    def export(rid: str, request: Request, format: str = 'html'):
        record = store.get(owner(request), rid)
        headers = {'Content-Disposition': f'attachment; filename="asterisk-ladder-{record["id"]}.{format if format in ("html", "json") else "txt"}"'}
        if format == 'html':
            return HTMLResponse(receipt_html(record), headers=headers)
        if format == 'json':
            return Response(json.dumps(public(record), indent=2), media_type='application/json', headers=headers)
        raise HTTPException(422, 'Choose html or json.')

    @app.delete('/api/ladder/receipts/{rid}')
    def delete(rid: str, request: Request):
        store.delete(owner(request), rid)
        return {'deleted': True}

    return store
