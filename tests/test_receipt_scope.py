"""Portable scope and declared reviewer independence from the RC3 review."""
import json
import pytest
from app.receipt import preview
from app.primitives import measure, gate
from app.receipt_view import render_receipt
from app.receipt_context import review_context
from scripts.summarize_reviewer_notes import summarize

ARGS=dict(split_file='split.csv',sample_column='sample',partition_column='partition',mapping_file='map.csv',mapping_sample_column='sample',entity_column='patient_id',train_values=['train'],test_values=['test'])

def fixture():
    splits=['sample,partition'];mapping=['sample,patient_id']
    for i in range(100):
        label='train' if i<40 else 'test' if i<50 else 'Test'
        entity=f'P{i}' if i<40 else f'Q{i}' if i<50 else f'P{i-50}'
        splits.append(f's{i},{label}');mapping.append(f's{i},{entity}')
    return {'split.csv':'\n'.join(splits)+'\n','map.csv':'\n'.join(mapping)+'\n'}

def receipt(files,args=ARGS):
    m=measure('entity_overlap',files,args)
    return render_receipt({'input_hashes':m['input_hashes'],'primitive_measurements':{'m':m},'verdict':gate('entity_overlap',[m],[])},files)

def test_excluded_rows_labels_cardinality_and_scope_leave_with_receipt():
    page=receipt(fixture())
    assert '50 rows excluded (labels: &quot;Test&quot;)' in page
    assert 'distinct training identities' in page and 'distinct evaluation identities' in page
    assert 'No inference about patient independence, duplicate images, or model accuracy.' in page
    assert '0 rows excluded (labels: none)' in receipt(fixture(),{**ARGS,'test_values':['test','Test']})

def test_injective_warning_uses_selected_samples_not_surplus_mapping():
    files={'split.csv':'sample,partition\na,train\nb,test\nc,unused\n','map.csv':'sample,patient_id\na,P1\nb,P2\nc,P1\nextra,P2\n'}
    p=preview('claim',files,ARGS)
    assert p['selected_identity']['distinct']==2 and p['selected_identity']['samples']==2
    assert 'No overlap is possible under this binding' in p['selected_identity']['warning']
    assert 'No overlap is possible under this binding' in receipt(files)
    for mapping in ['sample,patient_id\na,P1\nb,P1\n','sample,patient_id\na,P1\n']:
        assert not preview('claim',{**files,'map.csv':mapping},ARGS)['selected_identity']['warning']

def test_csv_data_citations_are_not_identity_definitions():
    c=review_context({'verdict':{'citations':[{'file':'map.csv','start_line':2,'end_line':3,'quote':'a,P1'}]}},{})
    assert 'Data rows' in c['citations'][0]['display_scope']
    assert 'do not define' in c['citations'][0]['display_scope']

@pytest.mark.parametrize('independent',[False,None,'true',True])
def test_only_explicit_independence_enters_human_summary(tmp_path,independent):
    row=dict(reviewer_id='person',artifact_label='A',actor_type='human',supported='yes',active_seconds=20,wall_seconds=30,committed_at='2026-09-22',consent=True,labels_unseen=True)
    if independent is not None:row['independent']=independent
    path=tmp_path/'review.json';path.write_text(json.dumps(row))
    report=summarize([path])
    assert report['human_review_count']==int(independent is True)
