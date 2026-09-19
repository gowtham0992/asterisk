import pytest
import json
from types import SimpleNamespace
from app import agent
from app.examples import example
from app.models import AuditInput
from app.agent import canonicalize_citations, AgentError
from app.models import Proposal
from tests.test_audit import RULE


def proposal(quote):
    return Proposal.model_validate({'status':'ready','rule':{**RULE,'citations':[{'file':'README.md','quote':quote}]}})


def test_whitespace_only_variation_restores_literal_source():
    p=proposal('Every specimen has one identifier.')
    canonicalize_citations(p,{'README.md':'Every specimen\nhas one identifier.'})
    assert p.rule.citations[0].quote=='Every specimen\nhas one identifier.'


def test_fabricated_quote_is_rejected():
    p=proposal('Every specimen has a verified patient identifier.')
    with pytest.raises(AgentError,match='not found'):
        canonicalize_citations(p,{'README.md':'Every specimen has one identifier.'})


def test_csv_content_cannot_substitute_for_documentation():
    p=proposal('This is not documentation.')
    p.rule.citations[0].file='splits.csv'
    with pytest.raises(AgentError,match='documentation'):
        canonicalize_citations(p,{'splits.csv':'This is not documentation.'})


def fake_provider(monkeypatch, payloads):
    calls=[]
    class Client:
        def __init__(self, **kwargs):
            self.chat=SimpleNamespace(completions=self)
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def create(self, **kwargs):
            payload=payloads[len(calls)]
            calls.append(kwargs)
            return SimpleNamespace(model='test',usage=SimpleNamespace(total_tokens=10),choices=[SimpleNamespace(finish_reason='stop',message=SimpleNamespace(content=json.dumps(payload)))])
    monkeypatch.setattr(agent,'OpenAI',Client)
    return calls


def test_unverified_proposal_is_repaired_before_return(monkeypatch):
    bad={'status':'ready','rule':{**RULE,'citations':[{'file':'README.md','quote':'A quotation that is not in the source.'}]}}
    calls=fake_provider(monkeypatch,[bad,{'status':'ready','rule':RULE}])
    result,meta=agent.propose(AuditInput.model_validate(example()),'fake','test','https://example.invalid')
    assert result['rule']['citations']==RULE['citations'] and meta['attempts']==2 and meta['tokens']==20


def test_repeated_invalid_evidence_never_returns_a_rule(monkeypatch):
    bad={'status':'ready','rule':{**RULE,'citations':[{'file':'README.md','quote':'A quotation that is not in the source.'}]}}
    calls=fake_provider(monkeypatch,[bad,bad])
    with pytest.raises(AgentError,match='after one repair'):
        agent.propose(AuditInput.model_validate(example()),'fake','test','https://example.invalid')
    assert len(calls)==2
