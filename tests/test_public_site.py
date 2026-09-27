import json
from pathlib import Path
import pytest
from scripts.build_public_site import build, public_url


def test_static_build_contains_only_public_assets_and_explicit_destination(tmp_path):
    out = build(tmp_path/'pages', 'https://app.example.org/static/ladder.html#propose')
    assert {p.name for p in out.iterdir()} == {'index.html', 'site.css', 'evidence.json', '.nojekyll'}
    page = (out/'index.html').read_text()
    assert page.count('https://app.example.org/static/ladder.html#propose') == 3
    assert '<script' not in page and '<form' not in page and '{{' not in page
    assert 'href="site.css"' in page and 'href="evidence.json"' in page
    result = json.loads((out/'evidence.json').read_text())
    patient = next(level for level in result['levels'] if level['name'] == 'patient')
    assert f"{patient['shared']} patient identifiers" in page
    assert f"affecting {patient['affected_test_rows']} of {patient['test_rows']}" in page


def test_static_builder_refuses_stale_directory(tmp_path):
    (tmp_path/'private.txt').write_text('private')
    with pytest.raises(ValueError, match='empty'):
        build(tmp_path, 'https://app.example.org')
    assert (tmp_path/'private.txt').read_text() == 'private'


@pytest.mark.parametrize('value', ['javascript:alert(1)', '//example.org', 'https://user:secret@example.org',
                                  'http://example.org', 'https://example.org/\nsecret', 'https://example.org\\x'])
def test_destination_rejects_unsafe_or_ambiguous_urls(value):
    with pytest.raises(ValueError):
        public_url(value)


def test_local_preview_requires_explicit_option_and_html_escapes_urls(tmp_path):
    with pytest.raises(ValueError):
        public_url('http://127.0.0.1:8792')
    out = build(tmp_path/'preview', 'http://127.0.0.1:8792/#ladders', allow_local=True,
                source_url='https://example.org/repo?a=1&b=2')
    assert 'href="https://example.org/repo?a=1&amp;b=2"' in (out/'index.html').read_text()
