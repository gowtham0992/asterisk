"""Owner-scoped, versioned storage for validated unconfirmed preparations.

Not an authorization provider: callers must obtain owner IDs from the existing
server session, never from a request body. No routes or provider calls are made.
"""
import json
import hashlib
import re
import time
import secrets
from datetime import datetime,timezone
from .draft import restore,save

MAX_DRAFTS=10


class MissingDraft(ValueError):pass
class StaleDraft(ValueError):pass
class DraftLimit(ValueError):pass


def owner_id(value):
    if not isinstance(value,str) or not value or len(value)>256:
        raise ValueError('A workspace owner is required')
    return value


def title_text(value):
    if not isinstance(value,str) or not 1<=len(value.strip())<=120:
        raise ValueError('Name the preparation using 1–120 characters')
    return value.strip()


def revision_number(value):
    if type(value) is not int or value<1:raise ValueError('A valid draft revision is required')
    return value


def validated_payload(record):
    # Enforce the persisted representation's limit before recomputation.
    text=json.dumps(record,allow_nan=False)
    if len(text.encode())>32_000_000:raise ValueError('Draft exceeds 32 MB')
    session=restore(record)
    return json.dumps(save(session,session.review['review_hash']),allow_nan=False)


class DraftStore:
    def __init__(self,connect):
        self.connect=connect
        with connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS preparation_drafts ('
                       'id TEXT PRIMARY KEY, owner TEXT NOT NULL, title TEXT NOT NULL, '
                       'revision INTEGER NOT NULL, created_at TEXT NOT NULL, '
                       'updated_at TEXT NOT NULL, payload TEXT NOT NULL)')
            db.execute('CREATE INDEX IF NOT EXISTS preparation_drafts_owner ON preparation_drafts(owner)')
            db.execute('CREATE TABLE IF NOT EXISTS preparation_create_requests ('
                       'owner TEXT NOT NULL, request_id TEXT NOT NULL, fingerprint TEXT NOT NULL, '
                       'draft_id TEXT NOT NULL, response TEXT NOT NULL, expires REAL NOT NULL, '
                       'PRIMARY KEY(owner,request_id))')

    def capacity(self,owner):
        owner=owner_id(owner)
        with self.connect() as db:
            used=db.execute('SELECT count(*) FROM preparation_drafts WHERE owner=?',(owner,)).fetchone()[0]
        return {'used':used,'limit':MAX_DRAFTS,'available':used<MAX_DRAFTS}

    def require_capacity(self,owner):
        if not self.capacity(owner)['available']:
            raise DraftLimit('This workspace already has 10 preparation drafts. Download a draft you want to keep, then remove an unneeded draft from Preparation drafts before requesting another model proposal. No model request was made.')

    @staticmethod
    def metadata(row):
        return {key:row[key] for key in ('id','title','revision','created_at','updated_at')}

    def list(self,owner):
        owner=owner_id(owner)
        with self.connect() as db:
            rows=db.execute('SELECT id,title,revision,created_at,updated_at FROM preparation_drafts WHERE owner=? ORDER BY updated_at DESC,id',(owner,)).fetchall()
        return [self.metadata(row) for row in rows]

    def create(self,owner,title,record,request_id=None):
        owner=owner_id(owner);title=title_text(title);payload=validated_payload(record)
        if request_id is not None and (not isinstance(request_id,str) or not re.fullmatch(r'[a-f0-9]{32}',request_id)):
            raise ValueError('Invalid save request identifier')
        fingerprint=hashlib.sha256(json.dumps([title,json.loads(payload)],sort_keys=True,separators=(',',':')).encode()).hexdigest()
        id=secrets.token_hex(16);now=datetime.now(timezone.utc).isoformat()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('DELETE FROM preparation_create_requests WHERE expires<=?',(time.time(),))
            if request_id is not None:
                prior=db.execute('SELECT * FROM preparation_create_requests WHERE owner=? AND request_id=?',(owner,request_id)).fetchone()
                if prior:
                    if prior['fingerprint']!=fingerprint:raise StaleDraft('This save request was already used for different choices')
                    if not db.execute('SELECT 1 FROM preparation_drafts WHERE id=? AND owner=?',(prior['draft_id'],owner)).fetchone():
                        raise StaleDraft('The previously saved preparation was deleted. This retry cannot recreate it')
                    return json.loads(prior['response'])
            if db.execute('SELECT count(*) FROM preparation_drafts WHERE owner=?',(owner,)).fetchone()[0]>=MAX_DRAFTS:
                raise DraftLimit('This workspace already has 10 preparation drafts')
            db.execute('INSERT INTO preparation_drafts VALUES (?,?,?,?,?,?,?)',(id,owner,title,1,now,now,payload))
            if request_id is not None:
                response={'id':id,'title':title,'revision':1,'created_at':now,'updated_at':now}
                db.execute('INSERT INTO preparation_create_requests VALUES (?,?,?,?,?,?)',
                           (owner,request_id,fingerprint,id,json.dumps(response),time.time()+86400))
        return {'id':id,'title':title,'revision':1,'created_at':now,'updated_at':now}

    def load(self,owner,id):
        owner=owner_id(owner)
        with self.connect() as db:
            row=db.execute('SELECT * FROM preparation_drafts WHERE id=? AND owner=?',(id,owner)).fetchone()
        if row is None:raise MissingDraft('Preparation not found in this workspace')
        # Recompute rather than trusting persisted counts or any old confirmation.
        return {**self.metadata(row),'session':restore(json.loads(row['payload']))}

    def update(self,owner,id,revision,title,record):
        owner=owner_id(owner);revision=revision_number(revision);title=title_text(title)
        # Avoid doing extraction work for a nonexistent/foreign/stale draft.
        with self.connect() as db:
            row=db.execute('SELECT revision FROM preparation_drafts WHERE id=? AND owner=?',(id,owner)).fetchone()
        if row is None:raise MissingDraft('Preparation not found in this workspace')
        if row['revision']!=revision:raise StaleDraft('This preparation changed. Reopen it before saving again')
        payload=validated_payload(record);now=datetime.now(timezone.utc).isoformat()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            changed=db.execute('UPDATE preparation_drafts SET title=?,revision=revision+1,updated_at=?,payload=? WHERE id=? AND owner=? AND revision=?',(title,now,payload,id,owner,revision))
            if changed.rowcount!=1:raise StaleDraft('This preparation changed. Reopen it before saving again')
            row=db.execute('SELECT id,title,revision,created_at,updated_at FROM preparation_drafts WHERE id=? AND owner=?',(id,owner)).fetchone()
        return self.metadata(row)

    def delete(self,owner,id,revision):
        owner=owner_id(owner);revision=revision_number(revision)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT revision FROM preparation_drafts WHERE id=? AND owner=?',(id,owner)).fetchone()
            if row is None:raise MissingDraft('Preparation not found in this workspace')
            if row['revision']!=revision:raise StaleDraft('This preparation changed. Reopen it before deleting')
            db.execute('DELETE FROM preparation_drafts WHERE id=? AND owner=? AND revision=?',(id,owner,revision))
