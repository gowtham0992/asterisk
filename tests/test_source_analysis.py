import pytest
from app.primitives import measure, gate


def inspect(source):
    return measure('fit_sites', {'notebook.py': source}, {'file': 'notebook.py', 'class_names': ['StandardScaler']})


HEAD = '''from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split as partition
X = load_frame()
scaler = StandardScaler()
'''


def test_display_magic_preserves_original_fit_line_and_records_normalization():
    source = '%matplotlib inline\n' + HEAD + 'scaled = scaler.fit_transform(X[X.columns])\na, b = partition(scaled)\n'
    result = inspect(source)
    assert result['output']['available'], result
    fit = result['output']['fit_calls'][0]
    assert fit['line'] == 6 and fit['violation']
    normalization = result['output']['normalization']
    assert normalization['changes'][0]['line'] == 1
    assert normalization['line_map'] == list(range(1, 8))
    assert gate('preprocessing', [result], [])['verdict'] == 'violation'


def test_train_test_split_tuple_positions_determine_role_not_variable_names():
    for variable, expected in [('banana', 'train_slice'), ('apple', 'test_slice')]:
        result = inspect(HEAD + f'banana, apple = partition(X)\nalias = {variable}\nscaler.fit(alias)\n')
        fit = result['output']['fit_calls'][0]
        assert fit['resolution']['kind'] == expected
        assert fit['violation'] == (expected == 'test_slice')


def test_whole_row_column_selection_retains_full_matrix_flow():
    result = inspect(HEAD + 'scaler.fit(X[X.columns])\na, b = partition(X)\n')
    assert result['output']['fit_calls'][0]['violation']


def test_column_selection_on_training_rows_stays_training_only():
    result = inspect(HEAD + 'banana, apple = partition(X)\nscaler.fit(banana[banana.columns])\n')
    fit = result['output']['fit_calls'][0]
    assert fit['resolution']['kind'] == 'train_slice'
    assert not fit['violation']


def test_unrelated_reassignment_does_not_share_split_source():
    result = inspect(HEAD + 'scaler.fit(X[X.columns])\nX = another_frame()\na, b = partition(X)\n')
    assert not result['output']['fit_calls'][0]['violation']


def test_conditional_assignment_is_unresolved_even_when_it_mentions_test_rows():
    source = HEAD + 'banana, apple = partition(X)\nchosen = banana\nif flag:\n    chosen = apple\nscaler.fit(chosen)\n'
    fit = inspect(source)['output']['fit_calls'][0]
    assert not fit['violation']
    assert fit['resolution']['kind'] == 'unresolved'


@pytest.mark.parametrize('magic', ['%run mutate.py', '%time X = alter(X)', '%%python', '!python mutate.py', "get_ipython().system('python mutate.py')"])
def test_execution_magics_are_explicitly_unavailable(magic):
    result = inspect(magic + '\n' + HEAD + 'scaler.fit(X)\na, b = partition(X)\n')
    assert not result['output']['available']
    assert 'magic' in result['output']['error'].lower() or 'shell' in result['output']['error'].lower()


def test_unknown_row_subset_is_not_reclassified_as_full_matrix():
    result = inspect(HEAD + 'subset = X[mask]\nscaler.fit(subset)\na, b = partition(X)\n')
    assert not result['output']['fit_calls'][0]['violation']
    assert result['output']['fit_calls'][0]['resolution']['kind'] == 'unresolved'


def test_transformer_constructed_inside_fold_still_has_a_fit_site():
    source = '''from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold
X = load_frame()
for a, b in KFold(2).split(X):
    scaler = StandardScaler()
    scaler.fit(X[b])
'''
    result = inspect(source)
    assert len(result['output']['fit_calls']) == 1
    assert result['output']['fit_calls'][0]['violation']


def test_train_named_full_matrix_cannot_hide_rows_and_unknown_calls_stay_unknown():
    bad = inspect(HEAD + 'train_only = X\nscaler.fit(train_only)\na, b = partition(X)\n')
    assert bad['output']['fit_calls'][0]['violation']
    unknown = inspect(HEAD + 'a, b = partition(X)\nscaler.fit(custom_filter(b))\n')
    assert not unknown['output']['fit_calls'][0]['violation']


def test_split_label_array_uses_second_pair_positions():
    source = HEAD + 'labels = load_labels()\na, b, c, d = partition(X, labels)\nscaler.fit(d)\n'
    fit = inspect(source)['output']['fit_calls'][0]
    assert fit['resolution']['kind'] == 'test_slice' and fit['violation']


def test_display_magic_inside_a_multiline_string_is_untouched():
    from app.source_analysis import normalize_source
    source = 'description = """\n%matplotlib inline\n!do_not_run\n"""\n'
    normalized, record = normalize_source(source, 'description.py')
    assert normalized == source and record['changes'] == []
    assert record['original_sha256'] == record['normalized_sha256']


def test_standard_ipython_display_export_is_recorded_and_line_stable():
    from app.source_analysis import normalize_source
    source = "get_ipython().run_line_magic('matplotlib', 'inline')\r\nvalue = 3\r\n"
    normalized, record = normalize_source(source, 'notebook.py')
    assert normalized.splitlines()[1] == 'value = 3'
    assert normalized.count('\r\n') == 2
    assert record['changes'][0]['kind'] == 'ipython-matplotlib-inline'
    assert record['line_map'] == [1, 2]


@pytest.mark.parametrize('source', [
    "get_ipython().run_line_magic('run', 'mutate.py')\n",
    "get_ipython().run_cell_magic('python', '', 'mutate()')\n",
    "get_ipython().run_line_magic('matplotlib', 'inline'); mutate()\n",
    "%matplotlib inline; mutate()\n",
    "%matplotlib inline\\\nmutate()\n",
])
def test_normalization_never_drops_non_display_execution(source):
    from app.source_analysis import normalize_source
    with pytest.raises((ValueError, SyntaxError)):
        normalize_source(source, 'notebook.py')


@pytest.mark.parametrize('rebinding', [
    'def partition(value):\n    return value, value',
    'partition = replacement_splitter',
    'class partition:\n    pass',
    'del partition',
])
def test_rebound_imported_split_alias_cannot_establish_test_rows(rebinding):
    source = HEAD + rebinding + '\nleft, right = partition(X)\nscaler.fit(right)\n'
    result = inspect(source)
    assert result['output']['available']
    assert not result['output']['fit_calls'][0]['violation']
    assert result['output']['fit_calls'][0]['resolution']['kind'] == 'unresolved'
    assert gate('preprocessing', [result], [])['verdict'] == 'insufficient'


def test_mutating_imported_module_splitter_is_unresolved():
    source = HEAD.replace('from sklearn.model_selection import train_test_split as partition', 'import sklearn.model_selection as ms')
    source += 'ms.train_test_split = replacement_splitter\nleft, right = ms.train_test_split(X)\nscaler.fit(right)\n'
    result = inspect(source)
    assert not result['output']['fit_calls'][0]['violation']
    assert result['output']['fit_calls'][0]['resolution']['kind'] == 'unresolved'
