import copy
import pytest
from scripts.score_benchmark_preparation import compare_rows,csv_rows

def rows():
    return [{'sample':'s1','entity':'p1','partition':'train','occurrences':[{'file':'x.csv','line_start':2,'line_end':2}]},
            {'sample':'s2','entity':'p1','partition':'test','occurrences':[{'file':'x.csv','line_start':3,'line_end':3}]}]

def test_same_overlap_counts_do_not_hide_wrong_entities():
    expected=rows();actual=copy.deepcopy(expected)
    for row in actual:row['entity']='wrong-unit'
    result=compare_rows(expected,actual)
    assert not result['exact_reference_rows_match']
    assert result['different_fields']['entity']==2

def test_missing_excluded_rows_and_extra_lookup_observations_are_visible():
    expected=rows();excluded=copy.deepcopy(expected[0]);excluded['partition']='excluded';excluded['occurrences'][0]['line_start']=4
    result=compare_rows(expected+[excluded],expected)
    assert result['missing_occurrences']==1
    assert compare_rows(expected,expected+[excluded])['extra_occurrences']==1

def test_duplicate_occurrences_are_refused_not_silently_overwritten():
    with pytest.raises(ValueError,match='Duplicate'):compare_rows(rows(),rows()+rows())

def test_row_order_does_not_change_score_but_id_substitution_is_disclosed():
    expected=rows();assert compare_rows(expected,list(reversed(expected)))['exact_reference_rows_match']
    actual=copy.deepcopy(expected);actual[0]['sample']='position-1'
    assert compare_rows(expected,actual)['different_fields']['sample']==1

def test_reference_reader_preserves_multiline_physical_positions():
    result=list(csv_rows('id,note\na,"two\nlines"\nb,end\n','x.csv'))
    assert result[0][1]=={'file':'x.csv','line_start':2,'line_end':3}
    assert result[1][1]['line_start']==4
