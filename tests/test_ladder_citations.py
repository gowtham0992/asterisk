from copy import deepcopy

from app.ladder_citations import review
from app.ladder import measure
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.ladder_api import register


def fixture():
    files={'windows.csv':'window_key,assignment\nw1,fit\nw2,hold\n',
           'calibration.csv':'window_key,asset_tag\nw1,rotor-X\nw2,rotor-X\n',
           'README.txt':'Each window_key names one vibration observation.\n',
           'split.txt':'assignment fit means training; hold means evaluation.\n',
           'lab.txt':'calibration.csv joins on window_key and returns asset_tag.\nasset_tag names a physical rotor.\n'}
    spec={'schema':'asterisk-ladder/1','claim':{'text':'No evaluation rotor appears in training.','level':'rotor'},
          'sources':[{'file':'windows.csv','format':'csv','sample':{'column':'window_key'},'partition':{'column':'assignment','map':{'fit':'train','hold':'test'}}}],
          'levels':[{'name':'window','kind':'observation','expression':{'column':'window_key'}},
                    {'name':'rotor','kind':'unit','expression':{'lookup':{'file':'calibration.csv','format':'csv','key_column':'window_key','value_column':'asset_tag','on':{'column':'window_key'}}}}],
          'citations':[{'file':'lab.txt','start_line':2,'end_line':2},{'file':'split.txt','start_line':1,'end_line':1}]}
    return spec,files


def test_omitted_join_and_observation_lines_are_visible_without_claiming_semantic_proof():
    spec,files=fixture();r=review(spec,files)
    obs=next(x for x in r['requirements'] if x['description'].startswith('Observation'))
    join=next(x for x in r['requirements'] if x['kind']=='join')
    assert 'window_key' in obs['missing_terms']
    assert set(join['missing_terms'])=={'calibration.csv','window_key'}
    assert any(c['file']=='lab.txt' and c['line']==1 for c in join['candidates'])
    assert 'do not verify identity meaning or a join' in r['scope']
    assert all(x['status']!='verified' for x in r['requirements'])


def test_added_exact_citations_close_field_gap_and_leave_measurement_counts_unchanged():
    spec,files=fixture();before=measure(spec,files)
    spec['citations'] += [{'file':'lab.txt','start_line':1,'end_line':1},{'file':'README.txt','start_line':1,'end_line':1}]
    after=measure(spec,files);r=review(spec,files)
    assert all(not x['missing_terms'] for x in r['requirements'])
    assert all(x['status']=='meaning_not_verified' for x in r['requirements'])
    assert before['finding']==after['finding'] and before['levels']==after['levels']
    assert before['spec_hash']!=after['spec_hash']


def test_denial_with_every_term_does_not_become_verified_support():
    spec,files=fixture();files['lab.txt']='Do NOT join calibration.csv window_key to asset_tag; no physical rotor mapping is supplied.\n'
    spec['citations'][0]={'file':'lab.txt','start_line':1,'end_line':1}
    join=next(x for x in review(spec,files)['requirements'] if x['kind']=='join')
    assert join['status']=='meaning_not_verified'
    assert 'Do NOT' in join['candidates'][0]['text']


def test_near_column_names_do_not_satisfy_reference_cues():
    spec,files=fixture();files['lab.txt']='asset_tag_backup is a provisional label.\nasset_tag_backup also repeats.\n'
    join=next(x for x in review(spec,files)['requirements'] if x['kind']=='join')
    assert 'asset_tag' in join['missing_terms']


def test_review_endpoint_uses_declared_docs_and_never_calls_provider():
    spec,files=fixture();app=FastAPI()
    def no_provider(*a):raise AssertionError('Review must not call a provider')
    register(app,lambda r:'owner',completion=no_provider,sandbox=no_provider)
    with TestClient(app) as c:
        body={'spec':spec,'files':[{'name':n,'content':v} for n,v in files.items()],'documentation':['lab.txt','README.txt','split.txt']}
        response=c.post('/api/ladder/review',json=body);assert response.status_code==200,response.text
        assert response.json()['citation_review']['requirements']
        assert c.post('/api/ladder/review',json={**body,'documentation':['absent.txt']}).status_code==422
