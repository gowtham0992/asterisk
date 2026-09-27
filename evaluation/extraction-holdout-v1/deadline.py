"""A process boundary bounds blocking provider operations without background retries."""
import json
import subprocess
import sys
from pathlib import Path


def call_worker(action, payload, timeout, *, worker=None):
    if not isinstance(timeout,(float,int)) or not 0 < timeout <= 60:
        raise ValueError('Invalid provider operation timeout')
    worker = worker or Path(__file__).with_name('worker.py')
    process = subprocess.Popen([sys.executable,str(worker)],stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        stdout, stderr = process.communicate(json.dumps({'action':action,'payload':payload}).encode(),timeout=timeout)
    except BaseException:
        process.kill()
        process.communicate()
        raise
    if process.returncode:
        # Do not promote arbitrary SDK stderr, which could contain request data.
        raise RuntimeError('Provider worker failed with exit code '+str(process.returncode))
    response=json.loads(stdout)
    if not isinstance(response,dict):raise ValueError('Invalid provider worker response')
    return response
