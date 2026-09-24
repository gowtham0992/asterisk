import copy,json,io,zipfile
import pytest
from app.primitives import measure
from app.receipt import preview,execute_receipt
from app.receipt_view import render_receipt,render_worksheet
from app.receipt_comparison import compare_receipts
from app.probe_evidence import bundle
from tests.test_primitives import FILES,ARGS,Trusted
from tests.test_investigations import setup,create,PLAN
from tests.test_api import HEADERS,client
from app import main
from fastapi.testclient import TestClient


def investigation(files=FILES):
    claim='Evaluation specimens must be absent from training.'
    checked=preview(claim,files,ARGS)
    confirmation={**checked,'confirmed':True,'confirmed_at':'2026-09-18T00:00:00+00:00','origin':'automated_development_fixture'}
    result=execute_receipt(claim,files,PLAN,confirmation,'test',Trusted())
    return {'input':{'claim':claim,'files':[{'name':n,'content':v} for n,v in files.items()]},'result':result}


def test_portable_bundle_works_without_external_assets_and_escapes_sources(tmp_path):
    files={**FILES,'evil.md':'</pre><script>alert(1)</script><img src="https://evil.example/">'}
    a=investigation(files);path=bundle(a['result'],files,tmp_path/'receipt')
    page=(path/'receipt.html').read_text()
    assert '&lt;script&gt;alert(1)&lt;/script&gt;' in page
    assert '<script>' not in page and '<img' not in page and '<link' not in page
    assert 'CSV row 4' in page and 'automated_development_fixture' in page
    assert 'default-src &#x27;none&#x27;' in page
    manifest=json.loads((path/'manifest.json').read_text())
    assert 'receipt.html' in manifest['files'] and 'review.html' in manifest['files']
    worksheet=(path/'review.html').read_text()
    assert 'src="review.js"' not in worksheet and 'sha256-' in worksheet
    assert 'data-receipt-reference=' in worksheet


def test_portable_input_tamper_suppresses_verdict():
    a=investigation();page=render_receipt(a['result'],{**FILES,'map.csv':'bad'})
    assert 'inputs do not match' in page
    assert 'Recorded identities appear on both sides.' not in page


def test_partition_repair_has_all_identity_and_row_deltas():
    revised={**FILES,'split.csv':'image,part\na,train\nb,train\nc,train\nd,test\n','map.csv':FILES['map.csv']+'v,d\n'}
    c=compare_receipts(investigation(),investigation(revised))
    assert c['available'] and c['after']['shared_identities']==0
    assert not c['identity_membership_comparable'] and c['samples_added']==['d']
    assert len(c['partition_moves'])==2
    assert c['evaluation_rows_added']==['d'] and c['evaluation_rows_removed']==['b','c']
    assert c['resolved_identities'] is None  # new identity/sample universe is explicit


def test_like_for_like_partition_repair():
    files={**FILES,'split.csv':'image,part\na,train\nb,test\nc,test\nd,train\n','map.csv':FILES['map.csv']+'v,d\n'}
    revised={**files,'split.csv':'image,part\na,train\nb,train\nc,train\nd,test\n'}
    c=compare_receipts(investigation(files),investigation(revised))
    assert c['identity_membership_comparable'] and c['resolved_identities']==['u']
    assert c['after']['evaluation_rows']==1 and len(c['partition_moves'])==3


def test_comparison_never_treats_remapping_or_claim_changes_as_repair():
    first=investigation();second=investigation({**FILES,'map.csv':'subject_id,image\nx,b\ny,c\nu,a\n'})
    c=compare_receipts(first,second)
    assert not c['shared_identity_comparison_available'] and len(c['identity_changes'])==2
    second=copy.deepcopy(first);second['input']['claim']='Different scientific claim'
    assert not compare_receipts(first,second)['shared_identity_comparison_available']
    second=copy.deepcopy(first);second['input']['files'][0]['content']+='d,test\n'
    assert not compare_receipts(first,second)['available']


def test_comparison_uses_all_shared_entities_not_capped_witnesses():
    split='image,part\n';mapping='subject_id,image\n'
    for i in range(40):
        split+=f'a{i},train\nb{i},test\n';mapping+=f'u{i},a{i}\nu{i},b{i}\n'
    files={**FILES,'split.csv':split,'map.csv':mapping}
    a=investigation(files);c=compare_receipts(a,a)
    assert len(c['persisting_identities'])==40
    assert len(a['result']['primitive_measurements']['measurement-1']['output']['witnesses'])==30


def test_manual_setup_has_no_remote_job_and_records_mode(setup):
    c,jobs=setup;id=create(c);url=f'/api/investigations/{id}'
    r=c.post(url+'/manual-plan',headers=HEADERS)
    assert r.status_code==200 and not jobs
    assert r.json()['plan']['binding'] is None
    assert c.post(url+'/manual-plan',headers=HEADERS).status_code==409
    checked=c.post(url+'/binding-preview',json={'arguments':ARGS},headers=HEADERS).json()
    r=c.post(url+'/accept-binding',json={'arguments':ARGS,'binding_hash':checked['binding_hash'],'confirm':True},headers=HEADERS)
    observation=r.json()['setup_observation']
    assert observation['mode']=='manual' and observation['initial_proposal'] is None
    assert observation['elapsed_review_seconds']>=0


def test_receipt_and_manual_setup_are_owner_scoped(setup):
    c,_=setup;id=create(c);url=f'/api/investigations/{id}'
    assert c.get(url+'/receipt').status_code==409
    with main.connect() as db:
        a=json.loads(db.execute('SELECT payload FROM investigations WHERE id=?',(id,)).fetchone()['payload'])
        a['result']=investigation()['result']
        db.execute('UPDATE investigations SET payload=? WHERE id=?',(json.dumps(a),id))
    r=c.get(url+'/receipt');assert r.status_code==200 and 'attachment' in r.headers['content-disposition']
    with TestClient(main.app) as other:
        other.get('/api/session')
        assert other.get(url+'/receipt').status_code==404
        assert other.post(url+'/manual-plan',headers=HEADERS).status_code==404


def test_blocked_receipt_distinguishes_unavailable_measurement_from_zero_overlap():
    a=investigation();r=a['result'];m=r['primitive_measurements']['measurement-1']
    m['arguments']['sample_column']=m['arguments']['partition_column']
    m['output']={'available':False,'error':'Duplicate sample IDs make membership ambiguous.'}
    r['verdict']={'verdict':'insufficient','limitations':[],'missing_evidence':[]}
    page=render_receipt(r,FILES)
    assert 'No overlap measurement is available because the check was blocked.' in page
    assert 'Duplicate sample IDs make membership ambiguous.' in page
    assert 'The sample identifier and partition label use the same column.' in page
    assert 'Repeatability of an error does not establish separation.' in page
    assert 'Zero observed overlap' not in page
    assert 'Inspect a witness if one is available' in page


def test_portable_coverage_names_both_partitions_and_hidden_overlap():
    files={**FILES,'map.csv':'subject_id,image\nu,a\n'}
    a=investigation(files);page=render_receipt(a['result'],files)
    assert 'Coverage by partition' in page
    assert 'Training: 1 of 1 rows mapped; 0 missing.' in page
    assert 'Evaluation: 0 of 2 rows mapped; 2 missing.' in page
    assert 'including among mapped evaluation rows' in page


def test_invalid_binding_offers_structural_candidates_without_selecting_them():
    args={**ARGS,'sample_column':'part'}
    with pytest.raises(ValueError,match='Structural sample-ID candidates: image'):
        preview('Specimens',FILES,args)
    assert args['sample_column']=='part'


def test_receipt_context_quotes_dictionary_without_claiming_semantic_verification():
    from app.receipt_context import review_context
    a=investigation();files={**FILES,'dictionary.md':'Dataset license\nsubject_id is NOT the patient identity.\nNo patient mapping supplied.\n'}
    c=review_context(a['result'],files)
    excerpt=next(x for x in c['documentation'] if x['file']=='dictionary.md')
    assert excerpt['start_line']==1
    assert 'NOT the patient identity' in excerpt['quote']
    assert excerpt['basis']=='Column-name mention; meaning requires review'
    assert c['partition_labels']=={'train':['train'],'test':['test']}


def test_blocked_receipt_separates_historical_requests_from_current_guidance():
    a=investigation();r=a['result'];r['primitive_measurements']['measurement-1']['output']={'available':False,'error':'blocked'}
    r['verdict']={'verdict':'insufficient','missing_evidence':['Invented missing ecg_id'], 'citations':[{'file':'split.csv','quote':'image,part','start_line':1,'end_line':1}]}
    page=render_receipt(r,FILES)
    assert 'Original interpretation · may be incorrect' in page
    assert 'Column names only; this passage does not define identity meaning.' in page
    assert 'Training labels: train' in page
    assert 'Selected columns and their meaning' in page

@pytest.mark.parametrize('change',['feature','documentation','none'])
def test_comparison_names_identity_scope_without_claiming_partition_only(change):
    files={**FILES,'split.csv':'image,part,feature\na,train,10\nb,test,20\nc,test,30\n'}
    revised=dict(files)
    if change=='feature':revised['split.csv']=files['split.csv'].replace('b,test,20','b,test,999')
    if change=='documentation':revised['notes.md']='A new acquisition procedure was used.'
    c=compare_receipts(investigation(files),investigation(revised))
    assert 'partition_only_change' not in c
    assert c['schema_version']==2
    assert c['identity_membership_comparable'] is True
    assert c['partition_moves']==[]
    assert c['changed_files']==({'feature':['split.csv'],'documentation':['notes.md'],'none':[]}[change])
    assert 'Other input fields may differ' in c['scope']

def test_comparison_replay_badge_requires_the_compared_measurement():
    a=investigation()
    a['result']['primitive_replays']=[{'measurement_id':'unrelated-measurement','matches':True}]
    c=compare_receipts(a,a)
    assert not c['before']['replay_recorded']
    assert not c['after']['replay_recorded']
