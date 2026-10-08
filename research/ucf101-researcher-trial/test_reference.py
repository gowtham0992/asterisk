import importlib.util,zipfile
from pathlib import Path
import pytest
s=importlib.util.spec_from_file_location('ucf_reference',Path(__file__).with_name('reference.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def archive(tmp_path,train,test):
 p=tmp_path/'splits.zip'
 with zipfile.ZipFile(p,'w') as z:
  z.writestr('ucfTrainTestlist/trainlist01.txt',train);z.writestr('ucfTrainTestlist/testlist01.txt',test)
 return p
def test_group_is_qualified_by_action_and_affected_rows_count_clips(tmp_path):
 r=m.audit(archive(tmp_path,'Jump/v_Jump_g01_c01.avi 1\nRun/v_Run_g02_c01.avi 2\n','Run/v_Run_g01_c01.avi\nJump/v_Jump_g01_c02.avi\nJump/v_Jump_g01_c03.avi\n'))
 assert r['shared_groups']==1 and r['affected_test_rows']==2 and r['test_groups']==2
 assert r['shared_clip_ids']==0
 assert r['numeric_group_ids_shared_ignoring_action']==1
def test_published_case_only_folder_alias_does_not_change_filename_namespace(tmp_path):
 r=m.audit(archive(tmp_path,'HandstandPushups/v_HandStandPushups_g01_c01.avi 1\n','HandstandPushups/v_HandStandPushups_g02_c01.avi\n'))
 assert r['shared_groups']==0 and r['classes']==1
 assert 'HandStandPushups' in r['per_class']
def test_duplicate_sample_and_invalid_filename_are_rejected(tmp_path):
 with pytest.raises(AssertionError):m.audit(archive(tmp_path,'Jump/v_Jump_g01_c01.avi 1\nJump/v_Jump_g01_c01.avi 1\n','Jump/v_Jump_g02_c01.avi\n'))
 with pytest.raises(ValueError):m.audit(archive(tmp_path,'Jump/v_Run_g01_c01.avi 1\n','Jump/v_Jump_g02_c01.avi\n'))
