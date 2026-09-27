"""Short-lived, owner-scoped payload tickets. Claim once before any provider call."""
import json
import secrets
import time
from .proposal import ProposalRequest
from .store import owner_id,MissingDraft,StaleDraft,DraftLimit

TTL_SECONDS=3600
MAX_TICKETS=3


class ProposalStore:
    def __init__(self,connect,clock=time.time):
        self.connect=connect;self.clock=clock
        with connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS preparation_proposals ('
                       'id TEXT PRIMARY KEY, owner TEXT NOT NULL, expires REAL NOT NULL, '
                       'used INTEGER NOT NULL, payload TEXT NOT NULL)')
            db.execute('CREATE INDEX IF NOT EXISTS preparation_proposals_owner ON preparation_proposals(owner)')
            db.execute('CREATE TABLE IF NOT EXISTS preparation_proposal_results ('
                       'id TEXT PRIMARY KEY, outcome TEXT NOT NULL)')

    def create(self,owner,files,claim,documentation,projection=None,evaluation_intent=None):
        owner=owner_id(owner);ticket=ProposalRequest(files,claim,documentation,projection,evaluation_intent)
        payload=json.dumps({'files':files,'claim':claim,'documentation':documentation,'projection':projection,'evaluation_intent':evaluation_intent},allow_nan=False)
        if len(payload.encode())>32_000_000:raise ValueError('Proposal inputs exceed 32 MB')
        now=self.clock();id=secrets.token_hex(16)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('DELETE FROM preparation_proposals WHERE expires<=?',(now,))
            db.execute('DELETE FROM preparation_proposal_results WHERE id NOT IN (SELECT id FROM preparation_proposals)')
            if db.execute('SELECT count(*) FROM preparation_proposals WHERE owner=?',(owner,)).fetchone()[0]>=MAX_TICKETS:
                raise DraftLimit('Three proposal previews are already open. Discard one before creating another.')
            db.execute('INSERT INTO preparation_proposals VALUES (?,?,?,?,?)',(id,owner,now+TTL_SECONDS,0,payload))
        return {'ticket_id':id,'expires_at':now+TTL_SECONDS,**ticket.preview()}

    def claim(self,owner,id,payload_hash,accepted):
        owner=owner_id(owner)
        if accepted is not True:raise ValueError('Approve this exact upload before requesting a proposal')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT * FROM preparation_proposals WHERE id=? AND owner=?',(id,owner)).fetchone()
            if row is None or row['expires']<=self.clock():raise MissingDraft('Proposal preview expired or was not found in this workspace')
            if row['used']:raise StaleDraft('This proposal was already attempted. Preview a new request to retry')
            saved=json.loads(row['payload'])
            ticket=ProposalRequest(saved['files'],saved['claim'],saved['documentation'],saved.get('projection'),saved.get('evaluation_intent'))
            if ticket.preview()['payload_hash']!=payload_hash:raise StaleDraft('The upload preview changed. Review it again')
            # Commit consumption before leaving this transaction. Provider timeouts
            # may incur a charge, so failures never restore the right to retry.
            db.execute('UPDATE preparation_proposals SET used=1 WHERE id=? AND owner=?',(id,owner))
        return ticket

    def finish(self,owner,id,result):
        """Persist once, only while the claimed ticket still exists and is valid.

        Discard or expiry during a provider call must not resurrect uploaded data.
        A process crash before this commit leaves an unknown outcome, never a retry.
        """
        owner=owner_id(owner)
        outcome=json.dumps(result,allow_nan=False)
        if len(outcome.encode())>32_000_000:raise ValueError('Proposal result exceeds 32 MB')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('INSERT OR IGNORE INTO preparation_proposal_results (id,outcome) '
                       'SELECT id,? FROM preparation_proposals WHERE id=? AND owner=? AND used=1 AND expires>?',
                       (outcome,id,owner,self.clock()))

    def recover(self,owner,id):
        owner=owner_id(owner)
        with self.connect() as db:
            row=db.execute('SELECT p.used,p.expires,p.payload,r.outcome FROM preparation_proposals p '
                           'LEFT JOIN preparation_proposal_results r ON r.id=p.id '
                           'WHERE p.id=? AND p.owner=?',(id,owner)).fetchone()
        if row is None or row['expires']<=self.clock():
            raise MissingDraft('Proposal preview expired or was not found in this workspace')
        result=json.loads(row['outcome']) if row['outcome'] else None
        response={'ticket_id':id,'expires_at':row['expires'],
                'state':'completed' if row['outcome'] else 'attempted' if row['used'] else 'ready',
                'result':result}
        # These are already stored, projected inputs, returned only after the same
        # ownership/expiry check as the result. Never derive them from model text.
        if result and result.get('status') in ('rejected','insufficient','failed','blocked'):
            saved=json.loads(row['payload'])
            response['manual_inputs']={'files':saved['files'],'claim':saved['claim'],
                                       'projection':saved.get('projection') or []}
            if saved.get('evaluation_intent') is not None:
                response['manual_inputs']['evaluation_intent']=saved['evaluation_intent']
        return response

    def discard(self,owner,id):
        owner=owner_id(owner)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('DELETE FROM preparation_proposal_results WHERE id IN '
                       '(SELECT id FROM preparation_proposals WHERE id=? AND owner=?)',(id,owner))
            db.execute('DELETE FROM preparation_proposals WHERE id=? AND owner=?',(id,owner))
