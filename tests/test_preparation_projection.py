"""Projection is client-reported provenance, never original-data authentication."""
import copy
import hashlib
import json
import pytest
from app.preparation.projection import validate_projection
from app.preparation.proposal import ProposalRequest
from app.preparation.draft import save, restore
from app.preparation.handoff import files_for
from tests.test_preparation_package import prepared
from tests.test_api import client, HEADERS
from tests.test_preparation_proposals import tickets


def projection(files):
    return [{'file':'data.csv','original_sha256':'0'*64,
             'projected_sha256':hashlib.sha256(files['data.csv'].encode()).hexdigest(),
             'included':['sample','subject','split'],'withheld':['age','sex'],'records':2}]


def test_record_survives_ticket_draft_and_export_without_entering_model_messages(tickets):
    source=prepared();manifest=projection(source.files)
    store,_=tickets
    p=store.create('alice',source.files,'Evaluation subjects must be absent from training.',['notes.txt'],manifest)
    assert p['client_projection']==manifest
    assert 'original_sha256' not in json.dumps(p['messages'])
    request=store.claim('alice',p['ticket_id'],p['payload_hash'],True)
    session=request.submit(p['payload_hash'],True,lambda *args:{'content':json.dumps(source.spec)})['session']
    session.preview({'data.csv':{'sample':{'column':'sample'},'repeats':'distinct','evidence':source.spec['citations']}})
    restored=restore(save(session,session.review['review_hash']))
    record=restored.confirm(restored.review['review_hash'],True)
    output=files_for(record)
    exported=json.loads(output['preparation-review.json'])
    assert exported['model_proposal']['approved_payload']['client_projection']==manifest
    assert exported['inputs']==source.files
    assert all('PRIVATE_SENTINEL' not in text for text in output.values())


@pytest.mark.parametrize('change',[
 {'projected_sha256':'f'*64}, {'included':['subject','sample','split']},
 {'records':True},{'records':3},{'withheld':['sample']},{'original_sha256':'not a hash'},
 {'withheld':['age','age']},{'extra':'unsupported'},
])
def test_inconsistent_projection_rejected(change):
    files=prepared().files;manifest=projection(files);manifest[0].update(change)
    with pytest.raises(ValueError):validate_projection(manifest,files)


def test_original_hash_is_explicitly_unverified_but_projected_hash_is_checked():
    files=prepared().files;manifest=projection(files)
    assert validate_projection(manifest,files)==manifest
    # No original bytes are available. A syntactically valid original hash is
    # accepted as a report, not evidence that those original bytes existed.
    manifest[0]['original_sha256']='1'*64
    assert validate_projection(manifest,files)==manifest


def test_api_validates_projection_before_creating_preview(client):
    files=prepared().files;manifest=projection(files)
    body={'files':files,'claim':'Evaluation subjects must be absent from training.',
          'documentation':['notes.txt'],'store_inputs':True,'projection':manifest}
    good=client.post('/api/preparations/proposal-preview',json=body,headers=HEADERS)
    assert good.status_code==201,good.text
    assert good.json()['client_projection']==manifest
    manifest[0]['projected_sha256']='f'*64
    bad=client.post('/api/preparations/proposal-preview',json=body,headers=HEADERS)
    assert bad.status_code==422


def test_manual_companion_is_visible_in_offline_receipt_and_invalid_metadata_is_not():
    from app.receipt_view import render_receipt
    from app.preparation.projection import receipt_projection
    source=prepared();manifest=projection(source.files)
    files={**source.files,'asterisk-projection-record.json':json.dumps({'format':'asterisk-client-projection','version':1,'files':manifest})}
    result={'input_hashes':{n:hashlib.sha256(t.encode()).hexdigest() for n,t in files.items()}}
    page=render_receipt(result,files)
    assert 'Files before the check' in page
    assert 'age, sex' in page and 'Original files were not received or authenticated' in page
    assert 'projection can change physical line numbers' in page
    manifest[0]['projected_sha256']='f'*64
    files['asterisk-projection-record.json']=json.dumps({'format':'asterisk-client-projection','version':1,'files':manifest})
    records,issues=receipt_projection(files)
    assert not records and issues


def test_projection_html_cannot_execute_withheld_field_names():
    from app.receipt_view import render_receipt
    source=prepared();manifest=projection(source.files);manifest[0]['withheld']=['<script>alert(1)</script>']
    files={**source.files,'asterisk-projection-record.json':json.dumps({'format':'asterisk-client-projection','version':1,'files':manifest})}
    page=render_receipt({'input_hashes':{n:hashlib.sha256(t.encode()).hexdigest() for n,t in files.items()}},files)
    assert '<script>alert(1)</script>' not in page
    assert '&lt;script&gt;alert(1)&lt;/script&gt;' in page


def test_json_projection_preserves_large_integer_and_rejects_nested_or_duplicate_fields():
    content='[{"image":"slide","id":9007199254740993}]'
    record={'file':'data.json','original_sha256':'0'*64,'projected_sha256':hashlib.sha256(content.encode()).hexdigest(),'included':['image','id'],'withheld':['conversations'],'records':1}
    assert validate_projection([record],{'data.json':content})==[record]
    for bad in ['[{"image":"slide","id":1,"id":2}]','[{"image":"slide","id":{"nested":1}}]','[{"image":"slide","id":NaN}]']:
        record['projected_sha256']=hashlib.sha256(bad.encode()).hexdigest()
        with pytest.raises(ValueError):validate_projection([record],{'data.json':bad})


def test_manual_projection_survives_preparation_export_and_checks_derived_tables():
    from app.preparation.projection import receipt_projection
    from app.preparation.intake import open_inputs
    source=prepared();manifest=projection(source.files)
    files={**source.files,'asterisk-projection-record.json':json.dumps({'format':'asterisk-client-projection','version':1,'files':manifest})}
    session=open_inputs(json.dumps(source.spec),files)
    session.preview({'data.csv':{'sample':{'column':'sample'},'repeats':'distinct','evidence':source.spec['citations']}})
    output=files_for(session.confirm(session.review['review_hash'],True))
    records,issues=receipt_projection(output)
    assert records==manifest and not issues
    output['splits.csv']+='other,test\n'
    records,issues=receipt_projection(output)
    assert not records and issues
