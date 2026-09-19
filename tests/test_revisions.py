import copy
import io
import json
import subprocess
import sys
import zipfile
import pytest
from fastapi.testclient import TestClient
from app import main
from app.examples import example
from tests.test_api import client, create, HEADERS
from tests.test_audit import RULE


def proposed(client, monkeypatch):
    monkeypatch.setattr(main,'propose',lambda *args: ({'status':'ready','rule':copy.deepcopy(RULE),'questions':[]},{'model':'test-stub','tokens':0,'seconds':0}))
    monkeypatch.setenv('NEBIUS_API_KEY','test-key')
    aid=create(client)
    client.post('/api/audits/'+aid+'/propose',json={},headers=HEADERS)
    return aid


def test_rule_revision_preserves_original_and_replays_edited_rule(client,monkeypatch,tmp_path):
    aid=proposed(client,monkeypatch)
    original=client.post('/api/audits/'+aid+'/execute',json={},headers=HEADERS).json()
    # Explicitly change the entity to image IDs: a valid but narrower question.
    revised={**RULE,'unit':'image','mapping_file':None,'entity_column':'capture'}
    saved=client.post('/api/audits/'+aid+'/with-rule',json={'rule':revised,'note':'Check image identity only for this separate comparison.'},headers=HEADERS)
    assert saved.status_code==201
    child=saved.json()
    assert child['id']!=aid and child['state']=='review' and child['result'] is None
    assert child['proposal']==original['proposal'] and child['revision']['parent_id']==aid
    complete=client.post('/api/audits/'+child['id']+'/execute',json={},headers=HEADERS).json()
    assert complete['result']['status']=='clear' and complete['result']['shared_entities']==0
    assert client.get('/api/audits/'+aid).json()==original
    archive=client.get('/api/audits/'+child['id']+'/export')
    with zipfile.ZipFile(io.BytesIO(archive.content)) as z:
        assert json.loads(z.read('rule.json'))['entity_column']=='capture'
        assert json.loads(z.read('report.json'))['proposal']['rule']['entity_column']=='subject'
        z.extractall(tmp_path)
    replay=subprocess.run([sys.executable,str(tmp_path/'verify.py')],capture_output=True,text=True)
    assert replay.returncode==0 and 'reproduced exactly' in replay.stdout


@pytest.mark.parametrize('change',[
    {'entity_column':'invented'},
    {'test_values':['train']},
    {'citations':[{'file':'README.md','quote':'A fabricated source quotation.'}]},
])
def test_bad_revision_is_rejected_without_creating_a_record(client,monkeypatch,change):
    aid=proposed(client,monkeypatch)
    before=client.get('/api/audits').json()
    response=client.post('/api/audits/'+aid+'/with-rule',json={'rule':{**RULE,**change},'note':'Correct the proposed independence rule.'},headers=HEADERS)
    assert response.status_code==422 and client.get('/api/audits').json()==before


def test_revision_and_raw_inputs_remain_owner_scoped(client,monkeypatch):
    aid=proposed(client,monkeypatch)
    with TestClient(main.app) as other:
        other.get('/api/session')
        assert other.get('/api/audits/'+aid+'/inputs').status_code==404
        assert other.post('/api/audits/'+aid+'/with-inputs',json=example(),headers=HEADERS).status_code==404
        assert other.post('/api/audits/'+aid+'/with-rule',json={'rule':RULE,'note':'Try another entity rule.'},headers=HEADERS).status_code==404


def test_missing_evidence_revision_keeps_original_inputs(client,monkeypatch):
    missing=example('missing')
    aid=client.post('/api/audits',json=missing,headers=HEADERS).json()['id']
    monkeypatch.setattr(main,'propose',lambda *args: ({'status':'insufficient','rule':None,'questions':['Add specimens.csv.']},{'model':'test','tokens':0,'seconds':0}))
    monkeypatch.setenv('NEBIUS_API_KEY','test-key')
    original=client.post('/api/audits/'+aid+'/propose',json={},headers=HEADERS).json()
    loaded=client.get('/api/audits/'+aid+'/inputs').json()
    loaded['files'].append(example()['files'][-1])
    child=client.post('/api/audits/'+aid+'/with-inputs',json=loaded,headers=HEADERS).json()
    assert child['state']=='draft' and child['proposal'] is None and child['inference'] is None
    assert child['revision']['parent_id']==aid and len(child['files'])==3
    assert client.get('/api/audits/'+aid+'/inputs').json()==missing
    assert client.get('/api/audits/'+aid).json()==original


def test_draft_cannot_acquire_a_rule_through_revision(client):
    aid=create(client)
    response=client.post('/api/audits/'+aid+'/with-rule',json={'rule':RULE,'note':'Attempt to bypass model review.'},headers=HEADERS)
    assert response.status_code==409
