"""Public reproduction must reject changed source bytes and emit no row data."""
import hashlib,importlib.util,json
from pathlib import Path
import pytest
s=importlib.util.spec_from_file_location('reproduce_dermamnist',Path(__file__).resolve().parents[1]/'scripts/reproduce_dermamnist.py');r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
def inputs(tmp_path,monkeypatch,split=None,mapping=None):
 values={'dermamnist_split_info.csv':split or 'image_id,split\na,train\nb,test\nc,val\n','HAM10000_metadata.csv':mapping or 'image_id,lesion_id,private_attribute\na,lesion-X,secret\nb,lesion-X,secret\nc,lesion-Z,secret\n'}
 for n,v in values.items():(tmp_path/n).write_text(v)
 monkeypatch.setattr(r,'SOURCES',{n:hashlib.sha256(v.encode()).hexdigest() for n,v in values.items()})
def test_aggregate_is_computed_and_does_not_include_rows(tmp_path,monkeypatch):
 inputs(tmp_path,monkeypatch);out=r.reproduce(tmp_path)
 assert out['measurement']=={'shared_entities':1,'affected_test_rows':1,'train_rows':1,'test_rows':1}
 assert out['excluded_validation_rows']==1 and out['reference_agrees'] and not out['matches_published_lesion_count']
 assert all(v not in json.dumps(out) for v in ['secret','lesion-X','private_attribute'])
def test_hash_mismatch_refuses_before_parse(tmp_path,monkeypatch):
 inputs(tmp_path,monkeypatch);(tmp_path/'HAM10000_metadata.csv').write_text('not even csv')
 with pytest.raises(ValueError,match='source hash mismatch'):r.reproduce(tmp_path)
def test_duplicate_sample_is_never_overwritten(tmp_path,monkeypatch):
 inputs(tmp_path,monkeypatch,split='image_id,split\na,train\na,test\nc,val\n')
 with pytest.raises(ValueError,match='Duplicate'):r.reproduce(tmp_path)
def test_conflicting_mapping_is_never_overwritten(tmp_path,monkeypatch):
 inputs(tmp_path,monkeypatch,mapping='image_id,lesion_id\na,X\na,Y\nb,Z\nc,W\n')
 with pytest.raises(ValueError,match='Conflicting'):r.reproduce(tmp_path)
