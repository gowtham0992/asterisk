import copy
import pytest
from app.audit import execute, AuditError, table
from app.examples import example

RULE = {'unit':'specimen','explanation':'New specimens must remain separate.', 'split_file':'splits.csv',
        'sample_column':'capture','partition_column':'partition','train_values':['train'],'test_values':['test'],
        'mapping_file':'specimens.csv','mapping_sample_column':'capture','entity_column':'subject',
        'citations':[{'file':'README.md','quote':'the persistent specimen identifier'}], 'limitations':[]}


def files(kind='overlap'):
    return {f['name']:f['content'] for f in example(kind)['files']}


def test_entity_overlap_is_found_despite_distinct_images():
    result = execute(RULE, files())
    assert (result['shared_entities'],result['affected_test_rows'],result['affected_percent']) == (16,16,40)
    assert result['shared_sample_ids'] == 0
    assert result['witnesses'][0]['train']['sample'] == 'frame_0001'
    assert result['witnesses'][0]['test']['sample'] == 'frame_0081'


def test_clean_control_is_clear():
    result = execute(RULE, files('clean'))
    assert result['status'] == 'clear'
    assert result['mapping_coverage_percent'] == 100


def test_missing_mapping_never_yields_clear():
    source = files('clean')
    source['specimens.csv'] = source['specimens.csv'].replace('frame_0120,specimen_0120\n','')
    result = execute(RULE, source)
    assert result['status'] == 'incomplete'
    assert result['missing_count'] == 1


def test_overlap_is_lower_bound_when_mapping_incomplete():
    source = files()
    source['specimens.csv'] = source['specimens.csv'].replace('frame_0120,specimen_0120\n','')
    result = execute(RULE, source)
    assert result['status']=='overlap' and result['missing_count']==1


def test_conflicting_mapping_is_rejected():
    source = files()
    source['specimens.csv'] += 'frame_0001,other_entity\n'
    with pytest.raises(AuditError, match='conflicting'): execute(RULE,source)


def test_duplicate_split_membership_is_rejected():
    source = files()
    source['splits.csv'] += 'frame_0001,test\n'
    with pytest.raises(AuditError, match='Duplicate'): execute(RULE,source)


@pytest.mark.parametrize('text', ['a,a\n1,2\n','a,b\n1\n','a,b\n1,2,3\n','a,b\n'])
def test_malformed_csv_is_rejected(text):
    with pytest.raises(AuditError): table(text)


def test_overlapping_partition_labels_are_rejected():
    rule = copy.deepcopy(RULE);rule['test_values']=['train']
    with pytest.raises(AuditError,match='disjoint'): execute(rule,files())


def test_unknown_column_is_rejected():
    rule = copy.deepcopy(RULE);rule['entity_column']='invented'
    with pytest.raises(AuditError,match='column'): execute(rule,files())


def test_identity_values_are_not_normalized():
    source={'splits.csv':'capture,partition,subject\na,train,Case\nb,test,case\n'}
    rule={**RULE,'mapping_file':None}
    assert execute(rule,source)['status']=='clear'
