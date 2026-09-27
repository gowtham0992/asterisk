"""Mutable UI files must be revalidated so releases do not mix cached versions."""
import pytest
from tests.test_api import client

@pytest.mark.parametrize('path',['/','/static/index.html','/static/app.js','/static/preparations.js','/static/preparations.css','/static/preparation-local-preview.mjs'])
def test_ui_resources_require_revalidation(client,path):
    response=client.get(path)
    assert response.status_code==200
    assert response.headers.get('cache-control')=='no-cache'
    assert response.headers.get('etag')


def test_unchanged_static_file_can_reuse_body_after_revalidation(client):
    first=client.get('/static/preparations.css')
    second=client.get('/static/preparations.css',headers={'If-None-Match':first.headers['etag']})
    assert second.status_code==304
    assert second.headers.get('cache-control')=='no-cache'
    assert not second.content


def test_private_api_stays_no_store(client):
    assert client.get('/api/session').headers['cache-control']=='no-store'
