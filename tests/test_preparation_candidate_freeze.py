import importlib.util
import json
import hashlib
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('preparation_freeze', Path(__file__).parents[1] / 'scripts/freeze_preparation_candidate.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def source_tree(root):
    for name in ('app/preparation/prompt_contract.py', 'app/main.py', 'static/ui.mjs',
                 'requirements.txt', 'requirements.lock.txt', 'requirements-sandbox.txt',
                 'asterisk.py', 'evaluation/real-preparation-v1/PROTOCOL.md',
                 '.env', 'app/state.sqlite', '.data/private.py') + module.RUNTIME_FILES:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(name)


def test_nested_prompt_is_frozen_secrets_excluded_and_bytes_reproduce(tmp_path):
    root = tmp_path / 'repo'
    source_tree(root)
    destination = tmp_path / 'frozen'
    manifest = module.freeze(root, destination)
    hashes = manifest['source_hashes']
    assert 'app/preparation/prompt_contract.py' in hashes
    assert set(module.RUNTIME_FILES) <= hashes.keys()
    assert not {'.env', 'app/state.sqlite', '.data/private.py'} & hashes.keys()
    assert all(hashlib.sha256((destination / 'source' / name).read_bytes()).hexdigest() == digest for name, digest in hashes.items())
    assert manifest['snapshot_hash'] == hashlib.sha256(json.dumps(hashes, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    (root / 'app/preparation/prompt_contract.py').write_text('changed prompt')
    second = module.freeze(root, tmp_path / 'second')
    assert second['snapshot_hash'] != manifest['snapshot_hash']
    with pytest.raises(FileExistsError):
        module.freeze(root, destination)


def test_symlink_cannot_pull_external_source_into_packet(tmp_path):
    root = tmp_path / 'repo'
    source_tree(root)
    external = tmp_path / 'external.py'
    external.write_text('private')
    (root / 'app/external.py').symlink_to(external)
    with pytest.raises(ValueError, match='symlink'):
        module.freeze(root, tmp_path / 'frozen')


def test_real_snapshot_can_load_preparation_without_working_tree(tmp_path):
    import subprocess
    import sys
    destination = tmp_path / 'snapshot'
    module.freeze(module.ROOT, destination)
    result = subprocess.run([sys.executable, '-I', '-c',
        'import sys; sys.path.insert(0, sys.argv[1]); '
        'from app.preparation import proposal, model_record, review; '
        'assert review.executor.records("id\\nx\\n", "csv", "a.csv")[0][0] == {"id":"x"}',
        str(destination / 'source')], cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
