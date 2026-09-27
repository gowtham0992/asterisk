import json
import subprocess
import sys

import pytest

from app import ladder_sandbox
from app.sandbox import SandboxError
from tests.test_ladder import tcga


def local_python(code, payload, key, project):
    """Run the exact replay program in a separate, clean interpreter, as the Sandbox would."""
    done = subprocess.run([sys.executable, '-I', '-c', code], input=payload, capture_output=True, text=True, timeout=60)
    return {'exit_code': done.returncode, 'stdout': done.stdout, 'truncated': False, 'seconds': 0.1, 'sdk_version': 'test'}


def test_the_replay_program_reproduces_the_local_ladder_exactly_in_a_clean_interpreter():
    spec, files = tcga(['TCGA-AB-0001-01Z-DX1', 'TCGA-AB-0002-01Z-DX1'], ['TCGA-AB-0001-01Z-DX2', 'TCGA-EF-0009-01Z-DX1'])
    result, provenance = ladder_sandbox.replay(spec, files, [], 'key', 'project', run=local_python)
    assert result['finding']['status'] == 'violation'
    assert provenance['matches_local'] is True and provenance['runtime'] == 'nebius-sandbox'
    assert len(provenance['program_sha256']) == 64


def test_confirmations_travel_to_the_replay():
    spec, files = tcga(['TCGA-AB-0001-01Z-DX1', 'TCGA-AB-0001-01Z-DX9'], ['TCGA-AB-0002-01Z-DX1', 'TCGA-AB-0002-01Z-DX2'])
    result, _ = ladder_sandbox.replay(spec, files, ['patient'], 'key', 'project', run=local_python)
    assert result['finding']['status'] == 'held_out'


def test_a_different_remote_answer_or_a_failed_run_records_nothing():
    spec, files = tcga(['TCGA-AB-0001-01Z-DX1'], ['TCGA-AB-0002-01Z-DX1'])
    tampered = lambda code, payload, key, project: {'exit_code': 0, 'stdout': '{}', 'truncated': False}
    with pytest.raises(SandboxError, match='differs from the local measurement'):
        ladder_sandbox.replay(spec, files, [], 'key', 'project', run=tampered)
    failed = lambda code, payload, key, project: {'exit_code': 1, 'stdout': '', 'truncated': False}
    with pytest.raises(SandboxError, match='failed'):
        ladder_sandbox.replay(spec, files, [], 'key', 'project', run=failed)

    def leaky(code, payload, key, project):
        raise RuntimeError('request body with secret')
    with pytest.raises(SandboxError) as caught:
        ladder_sandbox.replay(spec, files, [], 'key', 'project', run=leaky)
    assert 'secret' not in str(caught.value)
    with pytest.raises(SandboxError, match='credentials are missing'):
        ladder_sandbox.replay(spec, files, [], '', 'project', run=local_python)


def test_the_program_sends_engine_source_only():
    code = ladder_sandbox.program()
    assert 'NEBIUS' not in code and 'api_key' not in code.lower()
    assert json.loads(code.split('\n', 1)[0][len('SOURCES = '):]).keys() == {'executor', 'audit', 'ladder'}


def test_the_program_reads_the_uploaded_gzip_file_exactly_as_the_sandbox_will(tmp_path):
    import gzip
    spec, files = tcga(['TCGA-AB-0001-01Z-DX1'], ['TCGA-AB-0001-01Z-DX2'])
    path = tmp_path / 'input.json.gz'
    path.write_bytes(gzip.compress(json.dumps({'spec': spec, 'files': files, 'confirmed': []}).encode()))
    done = subprocess.run([sys.executable, '-I', '-c', ladder_sandbox.program(), str(path)], capture_output=True, text=True, timeout=60)
    assert done.returncode == 0 and done.stdout.strip() == ladder_sandbox.canonical(ladder_sandbox.ladder.measure(spec, files))


def test_the_replay_program_carries_the_field_and_characters_grammar():
    from tests.test_ladder import speech
    spec, files = speech(['84-121123-0000', '8463-294825-0000'], ['8463-287645-0001'], {'column': 'utterance', 'field': {'separator': '-', 'from': 1}})
    result, provenance = ladder_sandbox.replay(spec, files, [], 'key', 'project', run=local_python)
    assert result['finding']['status'] == 'violation' and provenance['matches_local'] is True
