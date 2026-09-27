"""New-installation setup must not need private state or reset spending."""
import json
import pytest
from app.preparation.init_budget import initialize
from app.preparation.provider import configured
from app.preparation.errors import BeforeDispatchBlocked


def test_fresh_configuration_calls_only_injected_worker_and_settles(tmp_path):
    path = initialize(tmp_path/'budget.json', .02)
    calls = []
    def worker(action, payload, timeout):
        assert len(json.loads(path.read_text())['reservations']) == 1
        calls.append(action)
        return {'usage': {'prompt_tokens': 10, 'completion_tokens': 20},
                'choices': [{'message': {'content': 'synthetic response'}}]}
    env = {'ASTERISK_PREPARATION_BUDGET': str(path), 'NEBIUS_API_KEY': 'fake'}
    adapter = configured(environ=env, worker=worker)
    assert calls == []
    assert adapter([], 100, 10)['content'] == 'synthetic response'
    assert calls == ['complete']
    assert json.loads(path.read_text())['settled_usd'] == pytest.approx(.000021)
    assert path.stat().st_mode & 0o777 == 0o600


def test_initializer_never_overwrites_or_follows_symlink(tmp_path):
    path = initialize(tmp_path/'budget.json', .01)
    before = path.read_bytes()
    with pytest.raises(FileExistsError): initialize(path, 1)
    link = tmp_path/'link'; link.symlink_to(path)
    with pytest.raises(FileExistsError): initialize(link, 1)
    assert path.read_bytes() == before


@pytest.mark.parametrize('limit', [0, -1, 1.01, float('nan'), float('inf'), True])
def test_invalid_cap_creates_nothing(tmp_path, limit):
    path = tmp_path/'budget.json'
    with pytest.raises(ValueError): initialize(path, limit)
    assert not path.exists()


def test_explicit_missing_budget_never_falls_back(tmp_path):
    with pytest.raises(FileNotFoundError):
        configured(environ={'ASTERISK_PREPARATION_BUDGET': str(tmp_path/'missing'), 'NEBIUS_API_KEY': 'fake'})


def test_exhausted_new_budget_blocks_worker(tmp_path):
    path = initialize(tmp_path/'budget.json', .000001)
    def forbidden(*args): pytest.fail('budget permitted provider call')
    adapter = configured(environ={'ASTERISK_PREPARATION_BUDGET': str(path), 'NEBIUS_API_KEY': 'fake'}, worker=forbidden)
    with pytest.raises(BeforeDispatchBlocked): adapter([], 100, 10)
