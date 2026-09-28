import json

import pytest

from app import ladder_proposal as lp
from app.ladder import LadderError

FILES = {
    'train.json': json.dumps([{'image': 'TCGA-AB-0001-01Z-DX1', 'age': '61'}, {'image': 'TCGA-AB-0001-01Z-DX2', 'age': '61'},
                              {'image': 'TCGA-AB-0003-01Z-DX1', 'age': '61'}]),
    'test.json': json.dumps([{'image': 'TCGA-AB-0001-01Z-DX3', 'age': '61'}, {'image': 'TCGA-CD-0002-01Z-DX1', 'age': '48'}]),
    'README.md': 'image is one slide.\nThe first 12 characters identify the patient.\nThe first 7 characters identify the site.\n',
}
CLAIM = 'Evaluation patients are unseen in training.'


def spec(level='patient', prefix=12):
    return {'schema': 'asterisk-ladder/1', 'claim': {'text': CLAIM, 'level': level},
            'sources': [{'file': 'train.json', 'format': 'json', 'sample': {'column': 'image'}, 'partition': {'value': 'train'}},
                        {'file': 'test.json', 'format': 'json', 'sample': {'column': 'image'}, 'partition': {'value': 'test'}}],
            'levels': [{'name': 'slide', 'kind': 'observation', 'expression': {'column': 'image'}},
                       {'name': 'patient', 'kind': 'unit', 'expression': {'column': 'image', 'prefix': prefix}},
                       {'name': 'site', 'kind': 'unit', 'expression': {'column': 'image', 'prefix': 7}}],
            'citations': [{'file': 'README.md', 'start_line': 1, 'end_line': 3}]}


def test_payload_sends_counts_but_no_values_unless_a_column_is_chosen():
    body = lp.payload(CLAIM, FILES)
    age = body['tables']['train.json']['columns']['age']
    assert age == {'rows': 3, 'distinct': 1, 'blank': 0, 'repeating_values': 1}
    assert '61' not in json.dumps(body)
    chosen = lp.payload(CLAIM, FILES, share_examples=[('train.json', 'image')])
    assert chosen['tables']['train.json']['columns']['image']['examples'][0].startswith('TCGA-AB-0001')
    assert 'examples' not in chosen['tables']['train.json']['columns']['age']
    assert body['documentation'] == {'README.md': FILES['README.md'].splitlines()}


def test_oversized_documentation_is_refused_rather_than_truncated():
    with pytest.raises(LadderError, match='instead of truncating'):
        lp.payload(CLAIM, {**FILES, 'big.md': 'x' * (lp.DOC_LIMIT + 1)})


def test_valid_proposal_is_dry_run_against_local_files():
    got, attempts = lp.propose(CLAIM, FILES, lambda messages, maximum, timeout: json.dumps({'status': 'ladder', 'spec': spec()}))
    assert got['status'] == 'ladder' and got['spec']['claim']['level'] == 'patient'
    assert attempts == [{'reply': json.dumps({'status': 'ladder', 'spec': spec()}), 'error': None}]


def test_one_repair_turn_sees_only_the_validator_error_then_stops():
    seen = []

    def complete(messages, maximum, timeout):
        seen.append(messages)
        return '{"status": "ladder"}' if len(seen) == 1 else json.dumps({'status': 'ladder', 'spec': spec()})
    got, attempts = lp.propose(CLAIM, FILES, complete)
    assert got['status'] == 'ladder' and [a['error'] is None for a in attempts] == [False, True]
    assert seen[1][-2] == {'role': 'assistant', 'content': '{"status": "ladder"}'}
    assert seen[1][-1]['content'].startswith('Validation failed: A ladder proposal contains only status and spec')
    with pytest.raises(LadderError):
        lp.propose(CLAIM, FILES, lambda m, x, t: 'not json')
    with pytest.raises(LadderError):
        lp.propose(CLAIM, FILES, lambda m, x, t: 'not json', repairs=0)


def test_v2_numbers_documentation_lines_and_v1_is_kept_for_reproducibility():
    v2 = lp.request(CLAIM, FILES)
    body = json.loads(v2[1]['content'])
    assert body['documentation']['README.md'][1] == 'The first 12 characters identify the patient.'
    assert v2[0]['content'] == lp.SYSTEM_V4 and '"start_line"' in lp.SYSTEM_V4  # the default prompt
    v1 = lp.request(CLAIM, FILES, version='v1')
    assert v1[0]['content'] == lp.SYSTEM_V1 and json.loads(v1[1]['content'])['documentation'] == {'README.md': FILES['README.md']}


def test_the_v2_worked_example_is_itself_a_valid_ladder_on_the_shipped_synthetic_files():
    from pathlib import Path
    example = Path(__file__).resolve().parents[1] / 'static' / 'ladder-example'
    files = {n: (example / n).read_text() for n in ('split.csv', 'subjects.csv', 'README.md')}
    text = lp.SYSTEM_V2.split('Reply:\n', 1)[1]
    got = lp.parse(text, files, 'Evaluation subjects were never seen in training.')
    assert got['status'] == 'ladder' and got['spec']['claim']['level'] == 'subject'


def test_abstention_is_a_first_class_answer():
    got = lp.parse(json.dumps({'status': 'abstain', 'missing': 'No document defines the patient part of the barcode.'}), FILES, CLAIM)
    assert got['status'] == 'abstain'


@pytest.mark.parametrize('reply,message', [
    ('not json', 'valid JSON'),
    (json.dumps({'status': 'verdict', 'clear': True}), 'ladder or an abstention'),
    (json.dumps({'status': 'ladder', 'spec': {**spec(), 'claim': {'text': 'Something else.', 'level': 'patient'}}}), "changed the user's claim"),
    (json.dumps({'status': 'ladder', 'spec': {**spec(), 'citations': [{'file': 'train.json', 'start_line': 1, 'end_line': 1}]}}), 'documentation, not from data'),
    (json.dumps({'status': 'ladder', 'spec': spec(), 'verdict': 'clear'}), 'only status and spec'),
    (json.dumps({'status': 'ladder', 'spec': {**spec(), 'sources': [{'file': 'nowhere.json', 'format': 'json', 'sample': {'column': 'image'}, 'partition': {'value': 'train'}}]}}), 'cannot be read'),
])
def test_invalid_proposals_are_rejected_before_anyone_sees_them(reply, message):
    with pytest.raises(LadderError, match=message):
        lp.parse(reply, FILES, CLAIM)


def test_semantic_match_compares_meaning_not_syntax():
    reference = spec()
    renamed = spec()
    renamed['levels'][1]['name'] = 'participant'
    renamed['claim']['level'] = 'participant'
    assert lp.semantic_match(renamed, reference, FILES)['same_grouping'] is True
    wrong = spec(prefix=7)  # valid syntax, correct arithmetic, wrong unit
    assert lp.semantic_match(wrong, reference, FILES)['same_grouping'] is False


def test_a_txt_data_file_can_be_declared_data_and_citations_must_come_from_declared_documentation():
    files = {**FILES, 'test_list.txt': 'TCGA-AB-0001-01Z-DX3\n'}
    with pytest.raises(LadderError, match='instead of truncating'):
        lp.payload(CLAIM, {**files, 'test_list.txt': 'x\n' * lp.DOC_LIMIT})
    body = lp.payload(CLAIM, files, documentation=['README.md'])
    assert set(body['documentation']) == {'README.md'} and body['tables']['test_list.txt']['format'] == 'lines'
    with pytest.raises(LadderError, match='not supplied'):
        lp.payload(CLAIM, files, documentation=['missing.md'])
    cited_data = spec()
    cited_data['citations'] = [{'file': 'test_list.txt', 'start_line': 1, 'end_line': 1}]
    with pytest.raises(LadderError, match='from documentation'):
        lp.parse(json.dumps({'status': 'ladder', 'spec': cited_data}), files, CLAIM, documentation=['README.md'])


@pytest.mark.parametrize('column', ['split', 'patient_name_set', 'fold', 'subset'])
def test_split_like_columns_require_explicit_value_sharing(column):
    files = {'data.csv': f'record,{column}\na,Alice Example\nb,Bob Example\n'}
    body = lp.payload(CLAIM, files)
    assert 'Alice Example' not in json.dumps(body)
    assert 'Bob Example' not in json.dumps(body)
    selected = lp.payload(CLAIM, files, share_examples=[('data.csv', column)])
    assert 'Alice Example' in json.dumps(selected)


@pytest.mark.parametrize('citation', ['README.md:3', None, {},
    {'file': [], 'start_line': 1, 'end_line': 2},
    {'file': 'README.md', 'start_line': True, 'end_line': 2},
    {'file': 'README.md', 'start_line': 3, 'end_line': 1},
    {'file': 'README.md', 'start_line': 1, 'end_line': 41}])
def test_malformed_citations_reach_validation_repair(citation):
    bad = spec()
    bad['citations'] = [citation]
    replies = iter([json.dumps({'status': 'ladder', 'spec': bad}),
                    json.dumps({'status': 'ladder', 'spec': spec()})])
    got, attempts = lp.propose(CLAIM, FILES, lambda *args: next(replies))
    assert got['status'] == 'ladder'
    assert len(attempts) == 2 and attempts[0]['error'] and attempts[1]['error'] is None


def test_v4_extends_only_the_grammar_and_its_examples_run_on_the_engine():
    from app.ladder import _evaluate
    assert lp.SYSTEM is lp.SYSTEM_V4 and lp.PROMPTS['v4'] == lp.SYSTEM_V4 and lp.PROMPT_VERSION == 'v4'
    assert lp.SYSTEM_V4.replace(lp.EXPR_V4, lp.EXPR_V2) == lp.SYSTEM_V2  # nothing else differs from v2
    assert _evaluate({'column': 'image', 'basename': True, 'field': {'separator': '_', 'from': 2}}, {'image': 'a/s1_d07_v2.png'}, {}, {}) == 'd07'
    assert _evaluate({'column': 'code', 'characters': {'from': 4, 'to': 7}}, {'code': 'ABX0412Q'}, {}, {}) == '0412'
    assert json.loads(lp.request(CLAIM, FILES, version='v4')[1]['content'])['documentation']['README.md'][0] == 'image is one slide.'
