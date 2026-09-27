"""Synthetic integration: retained model output enters the real review API.

No model request, scientific confirmation, or Sandbox execution is performed.
"""
import json
from tests.test_api import client, HEADERS
from tests.test_benchmark_smoke_runner import packet
from scripts.run_benchmark_smoke import run
from app.preparation.intake import reopen


def test_saved_proposal_survives_product_review_and_reopen(packet, client):
    directory, approval, output = packet
    spec = {'status': 'extract', 'sources': [{'file': 'rows.csv', 'format': 'csv',
            'sample': {'column': 'sample'}, 'entity': {'column': 'person'},
            'partition': {'column': 'split', 'map': {'train': 'train', 'test': 'test'}}}],
            'citations': [{'file': 'documentation.txt', 'start_line': 1, 'end_line': 1}]}
    run(directory, approval, output, completion_factory=lambda:
        lambda *args: {'content': json.dumps(spec)})
    inputs = json.loads((directory / 'dermamnist.json').read_text())['files']
    model = json.loads((output / 'dermamnist/model-record.json').read_text())
    # Explicit developer test fixture choices, not inferred human agreement.
    policies = {'rows.csv': {'sample': {'column': 'sample'}, 'repeats': 'distinct',
                            'evidence': spec['citations']}}
    response = client.post('/api/preparations/review-proposal', headers=HEADERS, json={
        'files': inputs, 'spec_text': json.dumps(spec), 'policies': policies,
        'model_proposal': model})
    assert response.status_code == 200, response.text
    record = response.json()['record']
    assert response.json()['confirmation'] is None
    assert record['model_proposal'] == model
    assert record['original_spec'] == spec
    restored = reopen(json.dumps(record))
    assert restored.model_proposal == model
    assert restored.confirmation is None
    assert restored.files == inputs
    # The same provenance cannot be silently attached to an altered binding.
    changed = json.loads(json.dumps(spec))
    changed['sources'][0]['entity'] = {'column': 'sample'}
    rejected = client.post('/api/preparations/review-proposal', headers=HEADERS, json={
        'files': inputs, 'spec_text': json.dumps(changed), 'policies': policies,
        'model_proposal': model})
    assert rejected.status_code == 422
