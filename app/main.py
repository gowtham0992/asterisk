import io
import csv
import hashlib
import json
import os
import secrets
import sqlite3
import threading
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .release import ReleaseSettings
from .models import AuditInput, RuleRevision, Proposal, ExecutionRequest
from .audit import execute, table, AuditError
from .agent import propose, AgentError, canonicalize_citations
from .examples import example
from .evidence import VERIFIER
from .comparison import compare
from .sandbox import execute_sandbox, SandboxError

ROOT = Path(__file__).resolve().parent.parent
# Captured with the process's imported engine; later disk edits cannot change exports.
ENGINE_SOURCE = (ROOT / 'app/audit.py').read_text()
ENGINE_SHA256 = hashlib.sha256(ENGINE_SOURCE.encode()).hexdigest()
for line in (ROOT / '.env').read_text().splitlines() if (ROOT / '.env').exists() else []:
    if '=' in line and not line.lstrip().startswith('#'):
        k, v = line.split('=', 1)
        if k.strip() in ('NEBIUS_API_KEY', 'NEBIUS_MODEL', 'NEBIUS_BASE_URL', 'NEBIUS_PROJECT_ID', 'NEBIUS_AI_PROJECT'):
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
MODEL = os.getenv('NEBIUS_MODEL', 'nvidia/nemotron-3-super-120b-a12b')
BASE = os.getenv('NEBIUS_BASE_URL', 'https://api.tokenfactory.nebius.com/v1/')
DB = Path(os.getenv('ASTERISK_DB', str(ROOT / '.data' / 'asterisk.sqlite')))
from .storage import prepare_database_path
prepare_database_path(DB)


def connect():
    c = sqlite3.connect(DB, timeout=10)
    c.row_factory = sqlite3.Row
    return c


with connect() as db:
    db.executescript('CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY); '
                    'CREATE TABLE IF NOT EXISTS audits (id TEXT PRIMARY KEY, owner TEXT NOT NULL, payload TEXT NOT NULL);')
DB.chmod(0o600)
app = FastAPI(title='Asterisk', docs_url=None, redoc_url=None, openapi_url=None)
RELEASE = ReleaseSettings.from_env()
app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(RELEASE.hosts))
model_lock = threading.Lock()
execution_lock = threading.Lock()
EXECUTOR = 'local'


@app.middleware('http')
async def boundaries(request: Request, call_next):
    if request.url.path != '/healthz' and not RELEASE.authorized(request.headers.get('authorization','')):
        return Response(status_code=401, headers={'WWW-Authenticate':'Basic realm="Asterisk research preview", charset="UTF-8"','Cache-Control':'no-store'})
    request.state.judge = RELEASE.is_judge(request.headers.get('authorization',''))
    if request.state.judge and request.url.path.startswith('/api/') and not (
            request.url.path == '/api/session' or request.url.path == '/api/ladder'
            or request.url.path.startswith('/api/ladder/')):
        return JSONResponse({'detail':'Judge access is limited to the independence ladder workflow.'},status_code=403)
    legacy_path = request.url.path == '/api/audits' or request.url.path.startswith('/api/audits/')
    if os.getenv('ASTERISK_LEGACY_AUDITS') != '1' and ((legacy_path and request.method not in ('GET','HEAD')) or request.url.path.startswith('/api/examples/')):
        return JSONResponse({'detail':'Legacy audit creation and execution are disabled. Saved records remain read-only.'},status_code=404,headers={'Cache-Control':'no-store'})
    if request.method not in ('GET', 'HEAD'):
        origin = request.headers.get('origin')
        if origin and origin != str(request.base_url).rstrip('/'):
            return JSONResponse({'detail': 'Cross-origin requests are not allowed.'}, status_code=403)
        if request.headers.get('x-asterisk-request') != '1':
            return JSONResponse({'detail': 'Missing request header.'}, status_code=403)
        data = bytearray()
        async for chunk in request.stream():
            data.extend(chunk)
            preparation_path = request.url.path == '/api/preparations' or request.url.path.startswith('/api/preparations/')
            if preparation_path:
                from .preparation.api import REQUEST_LIMIT
                limit = REQUEST_LIMIT
            else:
                limit = 18_000_000 if request.url.path.startswith('/api/investigations') or request.url.path.startswith('/api/ladder') else 4_200_000
            if len(data) > limit:
                message = 'Preparation request exceeds 32.1 MB.' if preparation_path else ('Request exceeds the investigation upload limit.' if limit == 18_000_000 else 'Upload exceeds the 4 MB limit.')
                return JSONResponse({'detail': message}, status_code=413)
        request._body = bytes(data)
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self' https://raw.githubusercontent.com/kakumarabhishek/Corrected-Skin-Image-Datasets/ac655ac5a5b93264c57d69d6d520778d915bfc89/DermaMNIST/DermaMNIST_Analysis/; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
    if request.url.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store'
    elif request.url.path == '/' or request.url.path.startswith('/static/'):
        # Static filenames are mutable across releases (including module imports).
        # Revalidate cached bytes rather than heuristically serving an older UI.
        # ETags still allow an unchanged resource to return a bodyless 304.
        response.headers['Cache-Control'] = 'no-cache'
    return response


@app.exception_handler(csv.Error)
async def csv_input_error(request, exc):
    return JSONResponse({'detail': 'Malformed CSV. Check quotation marks, headers and row lengths.'}, status_code=422)


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    return JSONResponse({'detail': 'Check input names, sizes, and required fields. Use CSV plus Markdown or text documentation.'}, status_code=422)


def owner(request):
    token = request.cookies.get('asterisk_session', '')
    with connect() as db:
        valid = db.execute('SELECT id FROM sessions WHERE id=?', (token,)).fetchone()
    if not valid:
        raise HTTPException(401, 'Session expired. Reload the page to continue.')
    return token


def get_audit(aid, request):
    uid = owner(request)
    with connect() as db:
        row = db.execute('SELECT payload FROM audits WHERE id=? AND owner=?', (aid, uid)).fetchone()
    if not row:
        raise HTTPException(404, 'Audit not found in this browser session.')
    return json.loads(row['payload'])


def save(audit, uid):
    with connect() as db:
        db.execute('INSERT INTO audits VALUES (?, ?, ?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload WHERE audits.owner=excluded.owner',
                   (audit['id'], uid, json.dumps(audit)))


def public(audit):
    result = {k:v for k,v in audit.items() if k not in ('input', 'engine_source', 'sandbox_program')}
    result['execution_target'] = EXECUTOR
    result['claim'] = audit['input']['claim']
    result['title'] = audit['input']['title']
    result['files'] = []
    for f in audit['input']['files']:
        item = {'name':f['name'], 'bytes':len(f['content'].encode())}
        if f['name'].endswith('.csv'):
            cols, rows = table(f['content'])
            item.update({'columns':cols, 'rows':len(rows)})
        else:
            item['text'] = f['content']
        result['files'].append(item)
    return result


@app.get('/healthz')
def health():
    try:
        with connect() as db:db.execute('SELECT 1 FROM sessions LIMIT 1').fetchone()
        return {'status':'ok'}
    except sqlite3.Error:
        return JSONResponse({'status':'unavailable'},status_code=503)


@app.get('/api/session')
def session(request: Request):
    token = request.cookies.get('asterisk_session', '')
    with connect() as db:
        if not db.execute('SELECT id FROM sessions WHERE id=?', (token,)).fetchone():
            token = secrets.token_urlsafe(32)
            db.execute('INSERT INTO sessions VALUES (?)', (token,))
    response = JSONResponse({'model':MODEL if os.getenv('ASTERISK_LEGACY_AUDITS')=='1' else 'nvidia/nemotron-3-super-120b-a12b', 'legacy_audits_enabled':os.getenv('ASTERISK_LEGACY_AUDITS')=='1', 'judge_access':getattr(request.state,'judge',False), 'configured':bool(os.getenv('NEBIUS_API_KEY')), 'mode':'local', 'executor':EXECUTOR, 'sandbox_available':bool(os.getenv('NEBIUS_API_KEY') and (os.getenv('NEBIUS_PROJECT_ID') or os.getenv('NEBIUS_AI_PROJECT')))})
    response.set_cookie('asterisk_session', token, httponly=True, samesite='strict', secure=RELEASE.public, max_age=604800)
    return response


@app.get('/api/examples/{kind}')
def examples(kind: str, request: Request):
    owner(request)
    if kind not in ('overlap', 'clean', 'missing'):
        raise HTTPException(404)
    return example(kind)


@app.get('/api/audits')
def list_audits(request: Request):
    uid = owner(request)
    with connect() as db:
        records = db.execute('SELECT payload FROM audits WHERE owner=? ORDER BY rowid DESC LIMIT 30', (uid,)).fetchall()
    return [{'id':a['id'], 'title':a['input']['title'], 'state':a['state'], 'created_at':a['created_at'], 'revision_kind':a.get('revision',{}).get('kind')} for a in (json.loads(r['payload']) for r in records)]


def new_audit(body):
    try:
        for f in body.files:
            if f.name.endswith('.csv'):
                table(f.content)
            elif len(f.content) > 16000:
                raise AuditError('Documentation is limited to 16,000 characters per file.')
    except AuditError as exc:
        raise HTTPException(422, str(exc))
    return {'id':secrets.token_hex(12), 'created_at':datetime.now(timezone.utc).isoformat(),
             'state':'draft', 'input':body.model_dump(), 'proposal':None, 'result':None, 'inference':None}


def insert_audit(audit, uid):
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        if db.execute('SELECT count(*) FROM audits WHERE owner=?', (uid,)).fetchone()[0] >= 30:
            raise HTTPException(409, 'This browser has 30 audits. Delete one before creating another.')
        db.execute('INSERT INTO audits VALUES (?, ?, ?)', (audit['id'], uid, json.dumps(audit)))


def effective_rule(audit):
    return audit.get('reviewed_rule') or audit['proposal']['rule']


@app.post('/api/audits', status_code=201)
def create_audit(body: AuditInput, request: Request):
    uid = owner(request)
    audit = new_audit(body)
    insert_audit(audit, uid)
    return public(audit)


@app.get('/api/audits/{aid}/inputs')
def read_inputs(aid: str, request: Request):
    return get_audit(aid, request)['input']


@app.get('/api/audits/{aid}/comparison')
def compare_revision(aid: str, request: Request):
    child = get_audit(aid, request)
    if not child.get('revision'):
        raise HTTPException(409, 'This audit has no original to compare with.')
    parent = get_audit(child['revision']['parent_id'], request)
    return compare(parent, child)


@app.post('/api/audits/{aid}/with-inputs', status_code=201)
def revise_inputs(aid: str, body: AuditInput, request: Request):
    parent = get_audit(aid, request)
    audit = new_audit(body)
    audit['revision'] = {'parent_id':parent['id'], 'kind':'inputs', 'note':'Researcher revised the input set or claim.'}
    insert_audit(audit, owner(request))
    return public(audit)


@app.post('/api/audits/{aid}/with-rule', status_code=201)
def revise_rule(aid: str, body: RuleRevision, request: Request):
    parent = get_audit(aid, request)
    if parent['state'] not in ('review', 'complete'):
        raise HTTPException(409, 'A proposed rule is required. Revise the inputs first.')
    proposal = Proposal(status='ready', rule=body.rule)
    try:
        files = {f['name']:f['content'] for f in parent['input']['files']}
        canonicalize_citations(proposal, files)
        execute(proposal.rule.model_dump(), files)
    except (AgentError, AuditError) as exc:
        raise HTTPException(422, str(exc))
    audit = new_audit(AuditInput.model_validate(parent['input']))
    audit.update(state='review', proposal=parent['proposal'], inference=parent['inference'],
                 reviewed_rule=proposal.rule.model_dump(),
                 revision={'parent_id':parent['id'], 'kind':'rule', 'note':body.note})
    insert_audit(audit, owner(request))
    return public(audit)


@app.post('/api/audits/{aid}/propose')
def propose_rule(aid: str, request: Request):
    audit = get_audit(aid, request)
    if audit['state'] != 'draft':
        return public(audit)
    if not os.getenv('NEBIUS_API_KEY'):
        raise HTTPException(503, 'Add NEBIUS_API_KEY to the local .env file and restart Asterisk.')
    if not model_lock.acquire(blocking=False):
        raise HTTPException(409, 'Another proposal is running. Wait a moment and retry.')
    try:
        proposal, inference = propose(AuditInput.model_validate(audit['input']), os.environ['NEBIUS_API_KEY'], MODEL, BASE)
        audit.update(proposal=proposal, inference=inference, state='review' if proposal['status']=='ready' else 'insufficient')
        save(audit, owner(request))
    except (AgentError, AuditError) as exc:
        raise HTTPException(502, str(exc))
    finally:
        model_lock.release()
    return public(audit)


@app.post('/api/audits/{aid}/execute')
def run_audit(aid: str, body: ExecutionRequest, request: Request):
    audit = get_audit(aid, request)
    if audit['state'] == 'complete':
        return public(audit)
    if audit['state'] != 'review':
        raise HTTPException(409, 'A supported rule must be reviewed before execution.')
    if body.remote and not body.confirm_upload:
        raise HTTPException(422, 'Confirm sending this audit’s full input files to Nebius Sandbox.')
    if not execution_lock.acquire(blocking=False):
        raise HTTPException(409, 'Another check is running. Wait a moment and retry.')
    try:
        # Re-read after acquiring the lock to avoid duplicate completed executions.
        audit = get_audit(aid, request)
        if audit['state'] == 'complete':
            return public(audit)
        rule = effective_rule(audit)
        files = {f['name']:f['content'] for f in audit['input']['files']}
        result = execute(rule, files)
        provenance = {'engine_sha256':ENGINE_SHA256, 'capture':'at_execution', 'runtime':'local'}
        if body.remote:
            result, remote, program = execute_sandbox(rule, files, ENGINE_SOURCE, result,
                os.getenv('NEBIUS_API_KEY'), os.getenv('NEBIUS_PROJECT_ID') or os.getenv('NEBIUS_AI_PROJECT'))
            provenance.update(remote)
            audit['sandbox_program'] = program
        audit.update(result=result, state='complete', engine_source=ENGINE_SOURCE,
                     execution_provenance=provenance, accepted_at=datetime.now(timezone.utc).isoformat())
        with connect() as db:
            updated = db.execute('UPDATE audits SET payload=? WHERE id=? AND owner=?',
                                 (json.dumps(audit), aid, owner(request))).rowcount
        if not updated:
            raise HTTPException(404, 'Audit was removed while the check was running.')
        return public(audit)
    except AuditError as exc:
        raise HTTPException(422, str(exc))
    except SandboxError as exc:
        raise HTTPException(502, str(exc))
    finally:
        execution_lock.release()


@app.get('/api/audits/{aid}')
def read_audit(aid: str, request: Request):
    return public(get_audit(aid, request))


@app.delete('/api/audits/{aid}')
def delete_audit(aid: str, request: Request):
    get_audit(aid, request)
    with connect() as db:
        db.execute('DELETE FROM audits WHERE id=? AND owner=?', (aid, owner(request)))
    return {'deleted':True}


@app.get('/api/audits/{aid}/export')
def export_audit(aid: str, request: Request):
    audit = get_audit(aid, request)
    if audit['state'] != 'complete':
        raise HTTPException(409, 'Run the check before exporting evidence.')
    source = audit.get('engine_source')
    report = public(audit)
    if source is None:
        # Legacy records did not retain code. Verify compatibility without rewriting history.
        try:
            replay = execute(effective_rule(audit), {f['name']:f['content'] for f in audit['input']['files']})
        except AuditError:
            raise HTTPException(409, 'The historical checker was not retained. Create a new revision to run the current checker.')
        if replay != audit['result']:
            raise HTTPException(409, 'The current checker does not reproduce this historical result. Create a new revision.')
        source = ENGINE_SOURCE
        report['execution_provenance'] = {'engine_sha256':ENGINE_SHA256, 'capture':'legacy_revalidated_at_export'}
    elif hashlib.sha256(source.encode()).hexdigest() != audit['execution_provenance']['engine_sha256']:
        raise HTTPException(409, 'Stored checker integrity verification failed.')
    contents = {
        'report.json':json.dumps(report, indent=2),
        'rule.json':json.dumps(effective_rule(audit), indent=2),
        'audit.py':source,
        'verify.py':VERIFIER,
        'README.txt':'Asterisk evidence bundle\nRun: python3 verify.py\nRequires Python 3.10+, standard library only.\nThe accepted rule is a human-reviewed interpretation, not proof the interpretation is correct.\nThis check only establishes exact entity overlap under that rule.\nThe manifest detects changes to bundled files; it is not signed and does not establish authenticity against deliberate rewriting of the whole bundle.\nFor old audits, legacy_revalidated_at_export means the included checker reproduced the result at export; its code was not captured at original execution.\n'
    }
    if audit.get('sandbox_program'):
        if hashlib.sha256(audit['sandbox_program'].encode()).hexdigest() != audit['execution_provenance'].get('program_sha256'):
            raise HTTPException(409, 'Stored sandbox program integrity verification failed.')
        contents['sandbox_program.py'] = audit['sandbox_program']
    contents.update({'inputs/'+f['name']:f['content'] for f in audit['input']['files']})
    manifest = {'format':'asterisk-evidence-v2', 'files':{name:hashlib.sha256(value.encode()).hexdigest() for name,value in contents.items()}}
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as z:
        for name,value in contents.items(): z.writestr(name, value)
        z.writestr('manifest.json', json.dumps(manifest, indent=2))
    return Response(buffer.getvalue(), media_type='application/zip', headers={'Content-Disposition':f'attachment; filename="asterisk-{aid}.zip"'})


@app.get('/')
def index():
    return FileResponse(ROOT/'static/index.html')


from .investigations import register as register_investigations
register_investigations(app, connect, owner, ROOT)
from .preparation.api import register as register_preparations
register_preparations(app, connect, owner)
from .ladder_api import register as register_ladder
register_ladder(app, owner, connect=connect)
app.mount('/static', StaticFiles(directory=ROOT/'static'), name='static')
