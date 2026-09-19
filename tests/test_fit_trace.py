import pytest
from app.fit_trace import fit_trace, validate_script, validate_transformers


def test_empty_transformer_selection_observes_all_supported_classes():
    validate_transformers([], {'StandardScaler': object()})
    validate_transformers(['StandardScaler'], {'StandardScaler': object()})


@pytest.mark.parametrize('requested', [['Ridge'], 'StandardScaler', [None]])
def test_invalid_transformer_selection_provides_recovery_instruction(requested):
    with pytest.raises(ValueError, match=r'Use \[\]|use \[\]'):
        validate_transformers(requested, {'StandardScaler': object()})


def test_unavailable_trace_retains_normalization_and_original_line_map():
    source='%matplotlib inline\nimport pandas as pd\n'
    result=fit_trace({'notebook.py':source}, {'entry_file':'notebook.py','class_names':[]})
    assert result['available'] is False
    assert 'Unsupported import' in result['error']
    assert result['normalization']['line_map']==[1,2]
    assert result['normalization']['changes'][0]['line']==1


def test_execution_magic_cannot_be_silently_skipped_by_trace():
    result=fit_trace({'notebook.py':'!curl example.com\n'}, {'entry_file':'notebook.py','class_names':[]})
    assert result['available'] is False and result['normalization'] is None
    assert 'Unsupported notebook magic' in result['error']
