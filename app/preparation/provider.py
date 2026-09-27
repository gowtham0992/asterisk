"""Explicit, bounded local launcher adapter using the retained provider worker.

No provider call occurs at construction. Do not run legacy evaluation batches
concurrently: those older runners do not participate in this process lock.
"""
import fcntl
import os
import json
import math
import threading
from pathlib import Path
from .errors import BeforeDispatchBlocked

ROOT = Path(__file__).resolve().parents[2]
MODEL = 'nvidia/nemotron-3-super-120b-a12b'
RATES = (.3, .9)  # Retained evaluation estimates; not verified provider billing.


from . import completion, budget as ledger, deadline


def number(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


class LocalProvider:
    def __init__(self, ledger_path, starting_committed, key, *, worker=deadline.call_worker):
        if not number(starting_committed) or not isinstance(key, str) or not key.strip():
            raise ValueError('Valid budget baseline and Nebius credential required')
        self.path = Path(ledger_path)
        self.start = starting_committed
        self._key = key
        self._worker = worker
        self._lock = threading.Lock()
        self._exhausted = False
        self._state()  # Fail closed on missing/corrupt ledger; never create a new budget.

    def _state(self):
        state = json.loads(self.path.read_text())
        if not isinstance(state, dict) or not number(state.get('limit_usd')) or not 0 < state['limit_usd'] <= 10:
            raise ValueError('Existing global budget must not exceed $10')
        if not number(state.get('settled_usd')) or not isinstance(state.get('reservations'), dict) or not isinstance(state.get('uncertain'), list):
            raise ValueError('Invalid existing budget ledger')
        for reservation in state['reservations'].values():
            if not isinstance(reservation, dict) or not number(reservation.get('amount')):
                raise ValueError('Invalid outstanding budget reservation')
        return state

    def __call__(self, messages, maximum, timeout):
        dispatched=[False]
        try:
            return self._complete(messages,maximum,timeout,dispatched)
        except Exception:
            if not dispatched[0]:raise BeforeDispatchBlocked() from None
            raise

    def _complete(self, messages, maximum, timeout, dispatched):
        # Reload under the lock: reservations from another editor must be counted.
        with self._lock, self.path.with_suffix('.review.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            if self._exhausted:
                raise RuntimeError('Provider exceeded reserved usage; restart requires budget review')
            self._state()
            budget = ledger.Budget(self.path, {MODEL: RATES})
            def request(**kwargs):
                dispatched[0]=True
                return self._worker('complete', {'key': self._key, 'model': MODEL, **kwargs}, kwargs['timeout'])
            bounded = completion.BudgetedCompletion(budget, MODEL, self.start, request, incremental_cap=1.0)
            try:
                return bounded(messages, maximum, timeout)
            finally:
                self._exhausted = bounded.exhausted


def configured(*, environ=None, worker=deadline.call_worker):
    environ = os.environ if environ is None else environ
    configured_path = environ.get("ASTERISK_PREPARATION_BUDGET")
    if configured_path is not None:
        if not configured_path.strip():
            raise ValueError("Explicit preparation budget path is empty")
        path = Path(configured_path)
        if not path.is_absolute():
            raise ValueError("Preparation budget path must be absolute")
        state = json.loads(path.read_text())
        if state.get("purpose") != "asterisk-preparation-v1":
            raise ValueError("Use an initialized preparation budget")
        return LocalProvider(path, 0, environ.get("NEBIUS_API_KEY"), worker=worker)
    # Compatibility for the existing research workspace; never initialize here.
    values = {}
    env_file = ROOT / '.env'
    for line in env_file.read_text().splitlines() if env_file.exists() else []:
        if '=' in line and not line.lstrip().startswith('#'):
            name, value = line.split('=', 1)
            values[name.strip()] = value.strip().strip(chr(34)).strip(chr(39))
    values.update(environ)
    key = values.get('NEBIUS_API_KEY')
    baseline = json.loads((ROOT / '.data/extraction-v1/cost-start.json').read_text())
    return LocalProvider(ROOT / '.data/probe-pilot/budget.json', baseline['starting_committed_usd'], key, worker=worker)
