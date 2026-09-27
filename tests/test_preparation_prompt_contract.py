"""Execute advertised examples; do not score model ability with hand-written specs."""
import copy
import json
import pytest
from app.preparation.prompt_contract import EXAMPLES
from app.preparation.proposal import ProposalRequest, proposal, executor


@pytest.mark.parametrize('example', EXAMPLES)
def test_advertised_examples_execute_without_confirmation(example):
    spec=proposal.parse(json.dumps(example['spec']))
    result=executor.extract(spec,example['files'])
    assert result['confirmation'] is None
    expected=([('c1','u7','train'),('c2','u7','test'),('c3','u9','excluded')]
              if 'assignments.csv' in example['files'] else
              [('images/Q701-a.png','Q701','train'),('images/Q701-b.png','Q701','test')])
    assert [(r['sample'],r['entity'],r['partition']) for r in result['lineage']]==expected


def test_join_example_rejects_missing_identity_instead_of_dropping_observation():
    example=copy.deepcopy(EXAMPLES[0])
    example['files']['units.csv']='capture,unit\nc1,u7\nc3,u9\n'
    with pytest.raises(ValueError,match='Unmapped sample'):
        executor.extract(example['spec'],example['files'])


def test_actual_approved_prompt_contains_executable_examples_and_is_hash_bound():
    example=EXAMPLES[0]
    for documentation in (None,['guide.txt']):
        request=ProposalRequest(example['files'],'Evaluation physical units must be absent from training.',documentation)
        preview=request.preview()
        prompt=preview['messages'][0]['content']
        embedded=json.loads(prompt.split('Complete synthetic examples, checked against the same executor:\n')[1])
        assert embedded==EXAMPLES
        # Demonstrate that the actual uploaded instructions, not a side document,
        # are part of the payload whose consent is checked.
        payload={k:v for k,v in preview.items() if k not in ('payload_hash','notice')}
        assert executor.sha(executor.canonical(payload))==preview['payload_hash']
        payload['messages'][0]['content']+='changed'
        assert executor.sha(executor.canonical(payload))!=preview['payload_hash']
