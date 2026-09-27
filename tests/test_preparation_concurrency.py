"""Competing previews must not overlap CPU/memory-heavy preparation work."""
import threading
from app import main
from concurrent.futures import ThreadPoolExecutor
from app.preparation import intake
from app.preparation.review import executor
from tests.test_api import client,HEADERS
from tests.test_preparation_package import prepared


def body():
    session=prepared()
    return {'files':session.files,'spec_text':executor.canonical(session.spec),
            'policies':{'data.csv':{'sample':session.spec['sources'][0]['sample'],
                'repeats':'distinct','evidence':session.spec['citations']}}}


def test_other_preview_rejected_before_work_and_slot_released(client,monkeypatch):
    session=prepared()
    ticket=client.post('/api/preparations/proposal-preview',json={'files':session.files,'claim':'Evaluation subjects must be absent from training.','documentation':['notes.txt'],'store_inputs':True},headers=HEADERS).json()
    provider_calls=[]
    monkeypatch.setattr(main.app.state,'preparation_complete',lambda *args:provider_calls.append(args),raising=False)
    started=threading.Event();release=threading.Event();calls=[]
    original=intake.open_inputs
    def held(*args):
        calls.append(1);started.set()
        assert release.wait(5),'test did not release held preparation'
        return original(*args)
    monkeypatch.setattr(intake,'open_inputs',held)
    request=body()
    with ThreadPoolExecutor(max_workers=1) as pool:
        first=pool.submit(client.post,'/api/preparations/review-proposal',json=request,headers=HEADERS)
        try:
            assert started.wait(5)
            second=client.post('/api/preparations/review-proposal',json=request,headers=HEADERS)
            assert second.status_code==429
            assert second.headers['retry-after']=='2'
            assert second.headers['cache-control']=='no-store'
            assert 'not started' in second.json()['detail']
            assert len(calls)==1
            url='/api/preparations/proposals/'+ticket['ticket_id']
            submit=client.post(url+'/submit',json={'payload_hash':ticket['payload_hash'],'confirm_upload':True},headers=HEADERS)
            assert submit.status_code==429
            assert submit.headers['x-asterisk-rejection']=='preparation-capacity'
            assert provider_calls==[]
            assert client.get(url).json()['state']=='ready'
            assert client.get('/api/preparations').status_code==200
        finally:release.set()
        assert first.result(timeout=5).status_code==200
    assert client.post('/api/preparations/review-proposal',json=request,headers=HEADERS).status_code==200
    assert len(calls)==2


def test_rejected_input_does_not_lock_future_preparations(client):
    invalid=body();invalid['spec_text']='invalid json'
    assert client.post('/api/preparations/review-proposal',json=invalid,headers=HEADERS).status_code==422
    assert client.post('/api/preparations/review-proposal',json=body(),headers=HEADERS).status_code==200
