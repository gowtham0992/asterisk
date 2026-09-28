import json
import subprocess
import sys
from pathlib import Path

import pytest

from app import ladder
from app.ladder import LadderError, measure, render, validate
from app.preparation.review import executor

ROOT = Path(__file__).resolve().parents[1]
DOC = 'image is one slide.\nThe first 12 characters identify the patient.\nThe first 7 characters identify the site.\n'


def tcga(train, test, levels=None, claim='patient', extra_files=None):
    files = {'train.json': json.dumps([{'image': x} for x in train]),
             'test.json': json.dumps([{'image': x} for x in test]),
             'README.md': DOC, **(extra_files or {})}
    spec = {'schema': 'asterisk-ladder/1',
            'claim': {'text': 'Evaluation patients are unseen in training.', 'level': claim},
            'sources': [{'file': 'train.json', 'format': 'json', 'sample': {'column': 'image'}, 'partition': {'value': 'train'}},
                        {'file': 'test.json', 'format': 'json', 'sample': {'column': 'image'}, 'partition': {'value': 'test'}}],
            'levels': levels or [
                {'name': 'slide', 'kind': 'observation', 'expression': {'column': 'image'}},
                {'name': 'patient', 'kind': 'unit', 'expression': {'column': 'image', 'prefix': 12}},
                {'name': 'site', 'kind': 'unit', 'expression': {'column': 'image', 'prefix': 7}}],
            'citations': [{'file': 'README.md', 'start_line': 1, 'end_line': 3}]}
    return spec, files


def level(result, name):
    return next(r for r in result['levels'] if r['name'] == name)


def test_slide_disjoint_patient_shared_is_a_violation_with_native_witness():
    spec, files = tcga(['TCGA-AB-0001-01Z-DX1', 'TCGA-AB-0002-01Z-DX1'], ['TCGA-AB-0001-01Z-DX2', 'TCGA-EF-0009-01Z-DX1'])
    r = measure(spec, files)
    assert level(r, 'slide')['shared'] == 0
    assert level(r, 'patient')['shared'] == 1 and level(r, 'patient')['affected_test_rows'] == 1
    assert level(r, 'site')['shared'] == 1
    assert r['finding']['status'] == 'violation' and r['finding']['level'] == 'patient'
    w = level(r, 'patient')['witnesses'][0]
    assert w['unit'] == 'TCGA-AB-0001'
    assert w['train']['unit_source'] == [{'file': 'train.json', 'at': '/0'}]
    assert w['test']['unit_source'] == [{'file': 'test.json', 'at': '/0'}]
    assert r['headline'].startswith('No shared values: slide. Shared: patient (1 shared), site (1 shared).')


def test_patient_disjoint_site_shared_holds_the_claim_but_shows_the_site():
    spec, files = tcga(['TCGA-AB-0001-01Z-DX1', 'TCGA-AB-0001-01Z-DX2'], ['TCGA-AB-0002-01Z-DX1'])
    r = measure(spec, files)
    assert r['finding']['status'] == 'held_out_pending_confirmation'
    assert 'per-sample identifier' in r['finding']['warning']
    assert level(r, 'site')['shared'] == 1
    assert 'Shared: site (1 shared)' in r['headline']


def test_one_unit_per_sample_is_not_established_until_a_person_confirms_the_column_meaning():
    # Evaluation run v2-D: a model bound "patient" to a per-row filename and got a guaranteed zero.
    levels = [{'name': 'slide', 'kind': 'observation', 'expression': {'column': 'image'}},
              {'name': 'patient', 'kind': 'unit', 'expression': {'column': 'image'}}]
    spec, files = tcga(['TCGA-AB-0001-01Z-DX1'], ['TCGA-AB-0001-01Z-DX2'], levels=levels)
    r = measure(spec, files)
    assert level(r, 'patient')['one_unit_per_sample'] is True
    assert level(r, 'slide')['one_unit_per_sample'] is False  # expected for observations
    assert r['finding']['status'] == 'not_established' and 'guaranteed' in r['finding']['reason']
    assert 'not an image, file or accession identifier' in r['finding']['warning']
    confirmed = measure(spec, files, confirmed=['patient'])
    assert confirmed['finding']['status'] == 'held_out' and confirmed['confirmed_levels'] == ['patient']
    assert 'not an image, file or accession identifier' in confirmed['finding']['warning']


def test_confirmation_turns_pending_into_held_out_but_never_rescues_a_violation_or_unknown_level():
    spec, files = tcga(['TCGA-AB-0001-01Z-DX1', 'TCGA-AB-0001-01Z-DX9'], ['TCGA-AB-0002-01Z-DX1', 'TCGA-AB-0002-01Z-DX2'])
    assert measure(spec, files)['finding']['status'] == 'held_out_pending_confirmation'
    assert measure(spec, files, confirmed=['patient'])['finding']['status'] == 'held_out'
    leaky, leaky_files = tcga(['TCGA-AB-0001-01Z-DX1'], ['TCGA-AB-0001-01Z-DX2'])
    assert measure(leaky, leaky_files, confirmed=['patient'])['finding']['status'] == 'violation'
    with pytest.raises(LadderError, match='not in the ladder'):
        measure(spec, files, confirmed=['tissue'])


def test_a_claim_bound_to_the_observation_is_guaranteed_and_not_established_even_if_confirmed():
    spec, files = tcga(['TCGA-AB-0001-01Z-DX1'], ['TCGA-AB-0002-01Z-DX1'], claim='slide')
    for confirmed in ((), ('slide',)):
        r = measure(spec, files, confirmed=confirmed)
        assert r['finding']['status'] == 'not_established' and 'observation itself' in r['finding']['reason']


def test_a_partition_read_from_the_claim_unit_column_is_a_tautology_even_if_confirmed():
    # Evaluation run v2-D: a model partitioned CAMELYON by center instead of the recorded split and hid a planted leak.
    files = {'stages.csv': 'slide,center,split\ns1,0,train\ns2,0,train\ns3,4,test\ns4,4,train\n',
             'README.md': 'Centers 0-2 are training and center 4 is the test center.\n'}
    spec = {'schema': 'asterisk-ladder/1', 'claim': {'text': 'The test center is unseen in training.', 'level': 'center'},
            'sources': [{'file': 'stages.csv', 'format': 'csv', 'sample': {'column': 'slide'},
                         'partition': {'column': 'center', 'map': {'0': 'train', '4': 'test'}}}],
            'levels': [{'name': 'slide', 'kind': 'observation', 'expression': {'column': 'slide'}},
                       {'name': 'center', 'kind': 'unit', 'expression': {'column': 'center'}}],
            'citations': [{'file': 'README.md', 'start_line': 1, 'end_line': 1}]}
    for confirmed in ((), ('center',)):
        r = measure(spec, files, confirmed=confirmed)
        assert r['finding']['status'] == 'not_established' and 'recorded split assignment' in r['finding']['reason']
    spec['sources'][0]['partition'] = {'column': 'split', 'map': {'train': 'train', 'test': 'test'}}
    assert measure(spec, files)['finding']['status'] == 'violation'  # the recorded split shows the moved slide


def test_plain_label_codes_are_not_treated_as_disjoint_identifier_families():
    files = {'split.csv': 'file,split\nSC4001E0,train\nSC4011E0,train\nST7011J0,test\nST7022J0,test\n',
             'README.md': 'SC files are the cassette study; ST files are the telemetry study.\n'}
    spec = {'schema': 'asterisk-ladder/1', 'claim': {'text': 'Test recordings come from another study.', 'level': 'study'},
            'sources': [{'file': 'split.csv', 'format': 'csv', 'sample': {'column': 'file'},
                         'partition': {'column': 'split', 'map': {'train': 'train', 'test': 'test'}}}],
            'levels': [{'name': 'recording', 'kind': 'observation', 'expression': {'column': 'file'}},
                       {'name': 'study', 'kind': 'unit', 'expression': {'column': 'file', 'prefix': 2}}],
            'citations': [{'file': 'README.md', 'start_line': 1, 'end_line': 1}]}
    assert measure(spec, files)['finding']['status'] == 'held_out_pending_confirmation'


def test_disjoint_identifier_namespaces_are_not_separation():
    files = {'train.csv': 'image,lesion\ni1,HAM_001\ni2,HAM_001\ni3,HAM_002\n',
             'test.csv': 'image,lesion\nt1,HAMTEST_001\nt2,HAMTEST_001\n',
             'README.md': 'lesion identifies the lesion.\n'}
    spec = {'schema': 'asterisk-ladder/1', 'claim': {'text': 'Test lesions are unseen.', 'level': 'lesion'},
            'sources': [{'file': 'train.csv', 'format': 'csv', 'sample': {'column': 'image'}, 'partition': {'value': 'train'}},
                        {'file': 'test.csv', 'format': 'csv', 'sample': {'column': 'image'}, 'partition': {'value': 'test'}}],
            'levels': [{'name': 'image', 'kind': 'observation', 'expression': {'column': 'image'}},
                       {'name': 'lesion', 'kind': 'unit', 'expression': {'column': 'lesion'}}],
            'citations': [{'file': 'README.md', 'start_line': 1, 'end_line': 1}]}
    r = measure(spec, files)
    assert level(r, 'lesion')['disjoint_namespaces'] == {'train_tokens': ['HAM_'], 'test_tokens': ['HAMTEST_']}
    assert r['finding']['status'] == 'not_established'


def blank_site_spec(test_site):
    files = {'split.csv': f'ecg,patient,site,fold\ne1,p1,s1,train\ne2,p2,,train\ne3,p3,{test_site},test\ne4,p4,,test\n',
             'README.md': 'patient identifies the person. site identifies the recording site.\n'}
    spec = {'schema': 'asterisk-ladder/1', 'claim': {'text': 'Test sites are unseen.', 'level': 'site'},
            'sources': [{'file': 'split.csv', 'format': 'csv', 'sample': {'column': 'ecg'},
                         'partition': {'column': 'fold', 'map': {'train': 'train', 'test': 'test'}}}],
            'levels': [{'name': 'ecg', 'kind': 'observation', 'expression': {'column': 'ecg'}},
                       {'name': 'patient', 'kind': 'unit', 'expression': {'column': 'patient'}},
                       {'name': 'site', 'kind': 'unit', 'expression': {'column': 'site'}}],
            'citations': [{'file': 'README.md', 'start_line': 1, 'end_line': 1}]}
    return spec, files


def test_blank_values_reject_the_level_unless_declared_unmapped():
    spec, files = blank_site_spec('s2')
    r = measure(spec, files)
    assert level(r, 'site')['status'] == 'unavailable'
    assert 'missing: unmapped' in level(r, 'site')['reason']
    assert r['finding']['status'] == 'insufficient'
    spec['levels'][2]['missing'] = 'unmapped'
    r = measure(spec, files)
    assert level(r, 'site')['unmapped_rows'] == 2
    assert r['finding']['status'] == 'insufficient'  # zero shared with unmapped rows proves nothing


def test_verified_overlap_is_a_violation_even_with_unmapped_rows():
    spec, files = blank_site_spec('s1')
    spec['levels'][2]['missing'] = 'unmapped'
    r = measure(spec, files)
    assert level(r, 'site')['shared'] == 1 and level(r, 'site')['unmapped_rows'] == 2
    assert r['finding']['status'] == 'violation'


def test_nesting_reports_a_finer_unit_split_across_coarser_units():
    files = {'split.csv': 'rec,patient,site,fold\nr1,p1,s1,train\nr2,p1,s2,train\nr3,p2,s1,test\n',
             'README.md': 'patient is a person; site is a hospital.\n'}
    spec = {'schema': 'asterisk-ladder/1', 'claim': {'text': 'Test patients are unseen.', 'level': 'patient'},
            'sources': [{'file': 'split.csv', 'format': 'csv', 'sample': {'column': 'rec'},
                         'partition': {'column': 'fold', 'map': {'train': 'train', 'test': 'test'}}}],
            'levels': [{'name': 'rec', 'kind': 'observation', 'expression': {'column': 'rec'}},
                       {'name': 'patient', 'kind': 'unit', 'expression': {'column': 'patient'}},
                       {'name': 'site', 'kind': 'unit', 'expression': {'column': 'site'}}],
            'citations': [{'file': 'README.md', 'start_line': 1, 'end_line': 1}]}
    r = measure(spec, files)
    assert level(r, 'site')['nests_previous'] == {'violations': 1, 'examples': [{'unit': 'p1', 'parents': ['s1', 's2']}]}


def test_agreement_counts_disagreeing_identifiers():
    files = {'split.csv': 'clip,src,fold\n1-100-A-0.wav,100,train\n1-101-A-0.wav,999,test\n',
             'README.md': 'The filename encodes fold-source-take-target. src identifies the source recording.\n'}
    spec = {'schema': 'asterisk-ladder/1', 'claim': {'text': 'Test recordings are unseen.', 'level': 'recording'},
            'sources': [{'file': 'split.csv', 'format': 'csv', 'sample': {'column': 'clip'},
                         'partition': {'column': 'fold', 'map': {'train': 'train', 'test': 'test'}}}],
            'levels': [{'name': 'clip', 'kind': 'observation', 'expression': {'column': 'clip'}},
                       {'name': 'recording', 'kind': 'unit', 'expression': {'column': 'src'}},
                       {'name': 'recording_prefix', 'kind': 'attribute', 'expression': {'column': 'clip', 'prefix': 5}}],
            'agreements': [['recording', 'recording_prefix']],
            'citations': [{'file': 'README.md', 'start_line': 1, 'end_line': 1}]}
    r = measure(spec, files)
    assert r['agreements'][0]['disagreements'] == 2


def test_lookup_level_matches_the_frozen_executor():
    files = {'split.csv': 'img,fold\na,train\nb,train\nc,test\n',
             'map.csv': 'img,patient\na,P1\nb,P2\nc,P1\n',
             'README.md': 'map.csv maps each image to its patient.\n'}
    expr = {'lookup': {'file': 'map.csv', 'format': 'csv', 'key_column': 'img', 'value_column': 'patient', 'on': {'column': 'img'}}}
    spec = {'schema': 'asterisk-ladder/1', 'claim': {'text': 'Test patients are unseen.', 'level': 'patient'},
            'sources': [{'file': 'split.csv', 'format': 'csv', 'sample': {'column': 'img'},
                         'partition': {'column': 'fold', 'map': {'train': 'train', 'test': 'test'}}}],
            'levels': [{'name': 'img', 'kind': 'observation', 'expression': {'column': 'img'}},
                       {'name': 'patient', 'kind': 'unit', 'expression': expr}],
            'citations': [{'file': 'README.md', 'start_line': 1, 'end_line': 1}]}
    r = measure(spec, files)
    assert level(r, 'patient')['shared'] == 1
    frozen = executor.extract(ladder.level_spec(validate(spec), spec['levels'][1]), files)
    assert {row['sample']: row['entity'] for row in frozen['lineage']} == {'a': 'P1', 'b': 'P2', 'c': 'P1'}
    # The witness cites the split row and the mapping row that supplied the patient.
    w = level(r, 'patient')['witnesses'][0]
    assert w['train']['unit_source'] == [{'file': 'split.csv', 'at': 'line 2'}, {'file': 'map.csv', 'at': 'line 2'}]
    assert w['test']['unit_source'] == [{'file': 'split.csv', 'at': 'line 4'}, {'file': 'map.csv', 'at': 'line 4'}]


@pytest.mark.parametrize('expr', [{'column': 'image'}, {'column': 'image', 'prefix': 12},
                                  {'column': 'image', 'basename': True}, {'column': 'image', 'basename': True, 'prefix': 7}])
def test_derivation_equals_frozen_executor_entities(expr):
    spec, files = tcga(['x/TCGA-AB-0001-01Z-DX1', 'x/TCGA-CD-0002-01Z-DX1'], ['y/TCGA-AB-0001-01Z-DX2'])
    spec['levels'] = [{'name': 'slide', 'kind': 'observation', 'expression': {'column': 'image'}},
                      {'name': 'unit', 'kind': 'unit', 'expression': expr}]
    spec['claim']['level'] = 'unit'
    checked = validate(spec)
    base = ladder.population(checked, files)
    values, missing = ladder._derive(checked, checked['levels'][1], files, base, ladder._record_index(files, checked))
    frozen = executor.extract(ladder.level_spec(checked, checked['levels'][1]), files)
    assert not missing
    assert values == {row['sample']: row['entity'] for row in frozen['lineage']}


def test_short_prefix_makes_only_that_level_unavailable():
    levels = [{'name': 'slide', 'kind': 'observation', 'expression': {'column': 'image'}},
              {'name': 'patient', 'kind': 'unit', 'expression': {'column': 'image', 'prefix': 64}}]
    spec, files = tcga(['TCGA-AB-0001'], ['TCGA-AB-0002'], levels=levels)
    r = measure(spec, files)
    assert level(r, 'slide')['status'] == 'measured'
    assert level(r, 'patient')['status'] == 'unavailable' and 'prefix' in level(r, 'patient')['reason']
    assert r['finding']['status'] == 'insufficient'


@pytest.mark.parametrize('mutate,message', [
    (lambda s: s['claim'].update(level='nowhere'), 'claim must name'),
    (lambda s: s['levels'].append(dict(s['levels'][0])), 'unique'),
    (lambda s: s['levels'][1].update(kind='label'), 'kind'),
    (lambda s: s['levels'][2].update(missing='ignore'), 'missing'),
    (lambda s: s.update(schema='other'), 'schema'),
    (lambda s: s.update(extra=1), 'Unknown'),
    (lambda s: s['levels'][1].update(name='Patient ID'), 'lowercase'),
])
def test_validation_rejects_malformed_ladders(mutate, message):
    spec, _ = tcga(['a'], ['b'])
    mutate(spec)
    with pytest.raises(LadderError, match=message):
        validate(spec)


def test_claim_cannot_require_an_attribute():
    spec, _ = tcga(['a'], ['b'])
    spec['levels'][2]['kind'] = 'attribute'
    spec['claim']['level'] = 'site'
    with pytest.raises(LadderError, match='attribute'):
        validate(spec)


def test_rendered_page_escapes_every_value_and_loads_nothing():
    spec, files = tcga(['TCGA-AB-0001-01Z-DX1'], ['TCGA-AB-0001-01Z-DX2'])
    spec['levels'][1]['meaning'] = '<script>alert(1)</script>'
    spec['claim']['text'] = '"><img src=x onerror=alert(1)>'
    page = render(measure(spec, files))
    assert '<script' not in page.lower() and '<img' not in page.lower()
    assert "default-src 'none'" in page
    assert '&lt;script&gt;' in page


def test_cli_writes_ladder_and_refuses_changed_pinned_inputs(tmp_path):
    spec, files = tcga(['TCGA-AB-0001-01Z-DX1'], ['TCGA-AB-0001-01Z-DX2'])
    src = tmp_path / 'src'
    src.mkdir()
    for name, content in files.items():
        (src / name).write_text(content)
    (tmp_path / 'spec.json').write_text(json.dumps(spec))
    import hashlib
    manifest = {'files': {'train.json': {'sha256': hashlib.sha256(files['train.json'].encode()).hexdigest()}}}
    (tmp_path / 'manifest.json').write_text(json.dumps(manifest))
    run = lambda out, man: subprocess.run([sys.executable, str(ROOT / 'asterisk.py'), 'ladder', str(tmp_path / 'spec.json'),
                                           '--sources', str(src), '--output', str(tmp_path / out), '--manifest', str(man)],
                                          capture_output=True, text=True, cwd=ROOT)
    done = run('out', tmp_path / 'manifest.json')
    assert done.returncode == 1, done.stderr
    assert json.loads(done.stdout)['finding'] == 'violation'
    saved = json.loads((tmp_path / 'out' / 'ladder.json').read_text())
    assert saved['finding']['level'] == 'patient'
    assert (tmp_path / 'out' / 'ladder.html').read_text().startswith('<!doctype html>')
    (src / 'train.json').write_text(files['train.json'].replace('0001', '0003'))
    refused = run('out2', tmp_path / 'manifest.json')
    assert refused.returncode == 2 and 'pinned SHA-256' in refused.stderr
    assert not (tmp_path / 'out2').exists()


def test_public_example_specs_are_valid_ladders():
    for path in sorted((ROOT / 'examples' / 'ladders').glob('*.json')):
        if path.name == 'sources.json':
            continue
        validate(json.loads(path.read_text()))


def test_http_ladder_is_session_scoped_and_local(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from app import main
    monkeypatch.setattr(main, 'DB', tmp_path / 'test.sqlite')
    with main.connect() as db:
        db.executescript('CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY);')
    spec, files = tcga(['TCGA-AB-0001-01Z-DX1'], ['TCGA-AB-0001-01Z-DX2'])
    body = {'spec': spec, 'files': [{'name': n, 'content': c} for n, c in files.items()]}
    headers = {'X-Asterisk-Request': '1'}
    with TestClient(main.app) as anonymous:
        assert anonymous.post('/api/ladder', json=body, headers=headers).status_code == 401
    with TestClient(main.app) as c:
        c.get('/api/session')
        assert c.post('/api/ladder', json=body).status_code == 403  # CSRF header required
        r = c.post('/api/ladder', json=body, headers=headers)
        assert r.status_code == 200, r.text
        assert r.json()['finding']['status'] == 'violation'
        review = c.post('/api/ladder/review', json=body, headers=headers)
        assert review.status_code == 200
        assert review.json()['population'] == {'train': 1, 'test': 1, 'excluded': 0}
        assert 'finding' not in review.json()
        assert c.post('/api/ladder/review', json=body).status_code == 403
        bad = c.post('/api/ladder', json={**body, 'spec': {**spec, 'schema': 'x'}}, headers=headers)
        assert bad.status_code == 422 and 'schema' in bad.json()['detail']


def test_headline_names_an_underivable_level_unavailable_not_unestablished():
    spec, files = tcga(['TCGA-AB-0001-01Z-DX1'], ['TCGA-EF-0009-01Z-DX1'])
    spec['levels'].append({'name': 'tissue', 'kind': 'unit', 'expression': {'column': 'image', 'prefix': 40}})
    r = measure(spec, files)
    assert 'Unavailable: tissue.' in r['headline'] and 'tissue' not in r['headline'].split('Unavailable')[0]


def test_the_finding_says_explicitly_whether_a_person_can_confirm_it():
    spec, files = tcga(['TCGA-AB-0001-01Z-DX1', 'TCGA-AB-0001-01Z-DX9'], ['TCGA-AB-0002-01Z-DX1', 'TCGA-AB-0002-01Z-DX2'])
    assert measure(spec, files)['finding']['confirmable'] is True
    assert measure(spec, files, confirmed=['patient'])['finding']['confirmable'] is False
    leaky, leaky_files = tcga(['TCGA-AB-0001-01Z-DX1'], ['TCGA-AB-0001-01Z-DX2'])
    assert 'confirmable' not in measure(leaky, leaky_files)['finding']


def test_the_headline_never_calls_a_guaranteed_zero_held_out():
    levels = [{'name': 'slide', 'kind': 'observation', 'expression': {'column': 'image'}},
              {'name': 'patient', 'kind': 'unit', 'expression': {'column': 'image'}}]
    spec, files = tcga(['TCGA-AB-0001-01Z-DX1'], ['TCGA-AB-0001-01Z-DX2'], levels=levels)
    headline = measure(spec, files)['headline']
    assert 'Not established: patient.' in headline and 'No shared values: slide.' in headline


def speech(train, test, expression, claim='speaker'):
    files = {'split.csv': 'utterance,split\n' + ''.join(f'{u},train\n' for u in train) + ''.join(f'{u},test\n' for u in test),
             'README.md': 'Files are named <speaker>-<chapter>-<utterance>.\n'}
    spec = {'schema': 'asterisk-ladder/1', 'claim': {'text': 'Test speakers are unseen in training.', 'level': claim},
            'sources': [{'file': 'split.csv', 'format': 'csv', 'sample': {'column': 'utterance'},
                         'partition': {'column': 'split', 'map': {'train': 'train', 'test': 'test'}}}],
            'levels': [{'name': 'utterance', 'kind': 'observation', 'expression': {'column': 'utterance'}},
                       {'name': claim, 'kind': 'unit', 'expression': expression}],
            'citations': [{'file': 'README.md', 'start_line': 1, 'end_line': 1}]}
    return spec, files


def test_a_field_reaches_variable_length_identifiers_a_prefix_cannot():
    # Speaker 84 and speaker 8463: a 2- or 4-character prefix would mis-group one of them.
    spec, files = speech(['84-121123-0000', '8463-294825-0000'], ['8463-287645-0001', '1034-121119-0003'],
                         {'column': 'utterance', 'field': {'separator': '-', 'from': 1}})
    r = measure(spec, files)
    assert level(r, 'speaker')['shared'] == 1 and level(r, 'speaker')['witnesses'][0]['unit'] == '8463'


def test_fields_can_be_joined_and_characters_read_from_the_middle():
    spec, files = speech(['airport-barcelona-0-0-a', 'airport-helsinki-0-1-a'], ['bus-barcelona-0-2-b', 'bus-helsinki-3-0-b'],
                         {'column': 'utterance', 'field': {'separator': '-', 'from': 2, 'to': 3}}, claim='location')
    r = measure(spec, files)
    assert level(r, 'location')['shared'] == 1 and level(r, 'location')['witnesses'][0]['unit'] == 'barcelona-0'
    spec, files = speech(['SC4011E0'], ['SC4012E0', 'SC4021E0'], {'column': 'utterance', 'characters': {'from': 4, 'to': 5}}, claim='subject')
    assert level(measure(spec, files), 'subject')['shared'] == 1


@pytest.mark.parametrize('expression, message', [
    ({'column': 'utterance', 'characters': {'from': 4, 'to': 5}, 'prefix': 3}, 'characters or prefix'),
    ({'column': 'utterance', 'characters': {'from': 5, 'to': 4}}, 'to at least from'),
    ({'column': 'utterance', 'characters': {'from': 0}}, 'from 1'),
    ({'column': 'utterance', 'field': {'from': 1}}, 'separator'),
    ({'column': 'utterance', 'field': {'separator': '', 'from': 1}}, 'separator'),
    ({'column': 'utterance', 'field': {'separator': '-', 'from': 9}}, 'fewer than 9 fields'),
    ({'column': 'utterance', 'characters': {'from': 1, 'to': 99}}, 'shorter than 99'),
])
def test_malformed_or_impossible_derivations_make_the_level_unavailable_not_guessed(expression, message):
    spec, files = speech(['84-121123-0000'], ['1034-121119-0003'], expression)
    r = measure(spec, files)
    assert level(r, 'speaker')['status'] == 'unavailable' and message in level(r, 'speaker')['reason']
    assert r['finding']['status'] == 'insufficient'


def test_swapped_partition_is_visible_in_review_and_receipt():
    spec, files = speech(['s1-a', 's1-b'], ['s1-c', 's2-a'], {'column': 'utterance', 'field': {'separator': '-', 'from': 1}})
    files['split.csv'] += 's3-a,val\ns3-b,val\n'
    spec['sources'][0]['partition']['map'] = {'train': 'train', 'test': 'excluded', 'val': 'test'}
    result = measure(spec, files, ['speaker'])
    assert result['finding']['status'] == 'held_out'
    context = result['review_context']
    assert {'file': 'split.csv', 'column': 'split', 'label': 'test', 'role': 'excluded', 'rows': 2} in context['partitions']
    assert '"val"' in context['confirmation'] and 'evaluation' in context['confirmation']
    page = render(result)
    assert 'test → excluded' in page and 'val → test' in page
    assert '2 excluded' in page and 'How each level was derived' in page
    assert 'Files are named' in page


def test_near_singleton_and_folded_identity_warnings_survive_outliers():
    spec, files = speech(['p1-a', 'p1-b', 'p2-a'], ['P1-c', 'P2-b', 'p3-a'],
                         {'column': 'utterance', 'field': {'separator': '-', 'from': 1}})
    result = measure(spec, files)
    row = level(result, 'speaker')
    assert row['folded_shared_units'] == 2
    assert row['evaluation_unit_ratio'] == 1
    assert 'case' in result['finding']['warning']
    assert 'No shared values' in render(result)
    assert 'Held out:' not in result['headline']
