"""Main-app native inference wiring, always with synthetic data and fake workers."""
import json
from types import SimpleNamespace
import pytest
from app.preparation.runtime import configure
from app.preparation.provider import LocalProvider
from tests.test_api import client, HEADERS
from tests.test_preparation_proposals import inputs
from tests.test_preparation_package import prepared
from app import main


def test_disabled_startup_does_not_construct_a_provider():
    app=SimpleNamespace(state=SimpleNamespace())
    def forbidden():pytest.fail('disabled startup touched provider configuration')
    configure(app,environ={},factory=forbidden)
    assert not hasattr(app.state,'preparation_complete')
    with pytest.raises(RuntimeError,match='must be 0 or 1'):
        configure(app,environ={'ASTERISK_PREPARATION_NEBIUS':'yes'},factory=forbidden)


def test_enabled_startup_fails_closed_without_exposing_credentials():
    app=SimpleNamespace(state=SimpleNamespace())
    def fail():raise ValueError('private key or source text')
    with pytest.raises(RuntimeError) as error:
        configure(app,environ={'ASTERISK_PREPARATION_NEBIUS':'1'},factory=fail)
    assert 'private key' not in str(error.value)
    assert not hasattr(app.state,'preparation_complete')


def test_main_submission_reserves_settles_and_recovers_with_shared_adapter(client,monkeypatch,tmp_path):
    ledger=tmp_path/'budget.json'
    ledger.write_text(json.dumps({'limit_usd':10,'settled_usd':6,'reservations':{},'uncertain':[]}))
    calls=[]
    def worker(action,payload,timeout):
        # Reservation must already be durable before the transport runs.
        assert len(json.loads(ledger.read_text())['reservations'])==1
        assert action=='complete' and timeout==60 and payload['maximum']==4000
        calls.append(payload['messages'])
        return {'usage':{'prompt_tokens':10,'completion_tokens':20},
                'choices':[{'message':{'content':json.dumps(prepared().spec)}}]}
    adapter=LocalProvider(ledger,6,'synthetic-key',worker=worker)
    monkeypatch.setattr(main.app.state,'preparation_complete',None,raising=False)
    configure(main.app,environ={'ASTERISK_PREPARATION_NEBIUS':'1'},factory=lambda:adapter)
    assert not calls
    p=client.post('/api/preparations/proposal-preview',json=inputs(),headers=HEADERS).json()
    assert p['provider_available'] and not calls
    url='/api/preparations/proposals/'+p['ticket_id']
    result=client.post(url+'/submit',json={'payload_hash':p['payload_hash'],'confirm_upload':True},headers=HEADERS)
    assert result.status_code==200,result.text
    assert calls==[p['messages']]
    state=json.loads(ledger.read_text())
    assert state['settled_usd']==pytest.approx(6.000021) and not state['reservations']
    assert client.get(url).json()['result']==result.json() and len(calls)==1


def test_main_submission_cannot_exceed_existing_extraction_cap(client,monkeypatch,tmp_path):
    ledger=tmp_path/'budget.json'
    ledger.write_text(json.dumps({'limit_usd':10,'settled_usd':6.9999,'reservations':{},'uncertain':[]}))
    def forbidden(*args):pytest.fail('exhausted budget reached transport')
    adapter=LocalProvider(ledger,6,'synthetic-key',worker=forbidden)
    monkeypatch.setattr(main.app.state,'preparation_complete',adapter,raising=False)
    p=client.post('/api/preparations/proposal-preview',json=inputs(),headers=HEADERS).json()
    result=client.post('/api/preparations/proposals/'+p['ticket_id']+'/submit',
                       json={'payload_hash':p['payload_hash'],'confirm_upload':True},headers=HEADERS)
    assert result.status_code==409
    assert 'No model call was made' in result.text
    recovered=client.get('/api/preparations/proposals/'+p['ticket_id']).json()
    assert recovered['result']=={'status':'blocked','provider_contacted':False}
    assert json.loads(ledger.read_text())['settled_usd']==6.9999


def test_dispatched_timeout_keeps_uncertain_charge_and_does_not_claim_no_call(client,monkeypatch,tmp_path):
    ledger=tmp_path/'budget.json'
    ledger.write_text(json.dumps({'limit_usd':10,'settled_usd':6,'reservations':{},'uncertain':[]}))
    calls=[]
    def timeout(*args):calls.append(1);raise TimeoutError('private provider detail')
    adapter=LocalProvider(ledger,6,'synthetic-key',worker=timeout)
    monkeypatch.setattr(main.app.state,'preparation_complete',adapter,raising=False)
    p=client.post('/api/preparations/proposal-preview',json=inputs(),headers=HEADERS).json()
    url='/api/preparations/proposals/'+p['ticket_id']
    result=client.post(url+'/submit',json={'payload_hash':p['payload_hash'],'confirm_upload':True},headers=HEADERS)
    assert result.status_code==502
    assert 'remote charge may still have occurred' in result.text
    assert 'No model call was made' not in result.text and 'private provider detail' not in result.text
    assert client.get(url).json()['result']=={'status':'failed'}
    state=json.loads(ledger.read_text())
    assert len(state['reservations'])==len(state['uncertain'])==1 and calls==[1]


def test_capabilities_reports_configuration_without_provider_call(client,monkeypatch):
    monkeypatch.setattr(main.app.state,'preparation_complete',None,raising=False)
    response=client.get('/api/preparations/capabilities')
    assert response.status_code==200
    assert response.json()=={'proposal_configured':False,'draft_capacity':{'used':0,'limit':10,'available':True}}
    assert response.headers['cache-control']=='no-store'
    def forbidden(*args,**kwargs):
        pytest.fail('capability check must never invoke provider')
    monkeypatch.setattr(main.app.state,'preparation_complete',forbidden)
    assert client.get('/api/preparations/capabilities').json()=={'proposal_configured':True,'draft_capacity':{'used':0,'limit':10,'available':True}}
