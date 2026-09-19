import copy
import pytest
from app.primitives import measure
from app.witness import inspect_witness
from tests.test_primitives import FILES, ARGS


def test_witness_shows_original_rows_in_reordered_mapping():
    record = measure('entity_overlap', FILES, ARGS)
    view = inspect_witness(record, FILES, 0)
    assert view['input_hashes_verified']
    assert view['sides']['train']['mapping']['csv_row'] == 4
    assert view['sides']['train']['split']['values'] == {'image': 'a', 'part': 'train'}
    assert view['sides']['test']['mapping']['values'] == {'subject_id': 'u', 'image': 'b'}
    assert view['sides']['test']['mapping']['columns'] == ['subject_id', 'image']


@pytest.mark.parametrize('mutation', ['file', 'identity', 'partition', 'negative_row', 'boolean_row'])
def test_witness_refuses_changed_sources_and_invalid_references(mutation):
    files = dict(FILES)
    record = copy.deepcopy(measure('entity_overlap', files, ARGS))
    witness = record['output']['witnesses'][0]
    if mutation == 'file': files['map.csv'] += 'v,d\n'
    if mutation == 'identity': witness['entity'] = 'made-up'
    if mutation == 'partition': witness['train'] = dict(witness['test'])
    if mutation == 'negative_row': witness['train']['split_row'] = -1
    if mutation == 'boolean_row': witness['train']['mapping_row'] = True
    with pytest.raises(ValueError): inspect_witness(record, files, 0)


def test_multiline_cells_use_csv_records_and_preserve_text():
    files = {**FILES, 'split.csv': 'image,part,note\na,train,"first\nsecond"\nb,test,<script>alert(1)</script>\nc,test,last\n'}
    view = inspect_witness(measure('entity_overlap', files, ARGS), files, 0)
    assert view['sides']['train']['split']['values']['note'] == 'first\nsecond'
    assert view['sides']['test']['split']['csv_row'] == 3
    assert view['sides']['test']['split']['values']['image'] == 'b'


@pytest.mark.parametrize('index', [-1, 1, 999])
def test_missing_witness(index):
    with pytest.raises(LookupError): inspect_witness(measure('entity_overlap', FILES, ARGS), FILES, index)
