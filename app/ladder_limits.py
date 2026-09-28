"""Atomic daily provider reservations, shared by workers and retained across restarts.

A proposal reserves two calls (initial + repair); a replay reserves one. Failed
and unused reservations remain charged to the call cap, not to a dollar ledger.
"""
from contextlib import contextmanager, closing
from datetime import datetime, timezone
import os
import secrets
import time

from fastapi import HTTPException


class Limits:
    def __init__(self, connect, session_cap=None, global_cap=None):
        self.connect = connect
        self.session_cap = int(os.getenv('ASTERISK_LADDER_SESSION_DAILY_CALLS', '10')) if session_cap is None else session_cap
        self.global_cap = int(os.getenv('ASTERISK_LADDER_GLOBAL_DAILY_CALLS', '100')) if global_cap is None else global_cap
        if self.session_cap < 0 or self.global_cap < 0:
            raise ValueError('Ladder call caps must be nonnegative')

    def initialize(self):
        with closing(self.connect()) as db, db:
            db.execute('CREATE TABLE IF NOT EXISTS ladder_call_usage '
                       '(day TEXT NOT NULL, owner TEXT NOT NULL, units INTEGER NOT NULL, PRIMARY KEY(day,owner))')
            db.execute('CREATE TABLE IF NOT EXISTS ladder_inflight '
                       '(owner TEXT PRIMARY KEY, token TEXT NOT NULL, started REAL NOT NULL)')

    @contextmanager
    def operation(self, owner, units):
        self.initialize()
        day = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        token = secrets.token_hex(16)
        with closing(self.connect()) as db, db:
            db.execute('BEGIN IMMEDIATE')
            # Recovery after a crashed worker; well beyond the bounded 120–240s provider calls.
            db.execute('DELETE FROM ladder_inflight WHERE started < ?', (time.time()-1800,))
            if db.execute('SELECT 1 FROM ladder_inflight WHERE owner=?', (owner,)).fetchone():
                raise HTTPException(429, 'A provider operation is already running in this workspace. Wait for it to finish.', headers={'Retry-After': '30'})
            used = db.execute('SELECT units FROM ladder_call_usage WHERE day=? AND owner=?', (day, owner)).fetchone()
            total = db.execute('SELECT COALESCE(SUM(units),0) FROM ladder_call_usage WHERE day=?', (day,)).fetchone()[0]
            if (used[0] if used else 0) + units > self.session_cap or total + units > self.global_cap:
                raise HTTPException(429, 'The daily provider-call allowance is used. It resets at 00:00 UTC. Local measurement and saved receipts remain available.')
            db.execute('INSERT INTO ladder_call_usage VALUES (?,?,?) ON CONFLICT(day,owner) DO UPDATE SET units=units+excluded.units', (day, owner, units))
            db.execute('INSERT INTO ladder_inflight VALUES (?,?,?)', (owner, token, time.time()))
        try:
            yield
        finally:
            with closing(self.connect()) as db, db:
                db.execute('DELETE FROM ladder_inflight WHERE owner=? AND token=?', (owner, token))
