import json
from datetime import date
from app.primitive_policy import categories
from app.primitive_runtime import implementation_hash
from app.primitives import digest

def test_old_acceptance_and_dates_cannot_expand_v4_scope(tmp_path,monkeypatch):
 monkeypatch.delenv('ASTERISK_ENTITY_ONLY',raising=False)
 assert categories(tmp_path,date(2026,10,7))==['entity_overlap']
 folder=tmp_path/'.data/primitive-v3';folder.mkdir(parents=True)
 (folder/'twins.json').write_text(json.dumps({'implementation_hash':implementation_hash(),'passed':True,'pairs':[{'passed':True} for _ in range(6)]}))
 assert categories(tmp_path,date(2026,10,8))==['entity_overlap']
 snapshot={'implementation_hash':implementation_hash(),'frozen_at':'2026-09-18'}
 (folder/'snapshot.json').write_text(json.dumps(snapshot))
 report={'status':'pass','freeze_hash':digest(snapshot),'implementation_hash':implementation_hash()}
 (folder/'acceptance-report.json').write_text(json.dumps(report))
 assert categories(tmp_path,date(2026,10,8))==['entity_overlap']
 report['freeze_hash']='stale';(folder/'acceptance-report.json').write_text(json.dumps(report))
 assert categories(tmp_path,date(2026,10,8))==['entity_overlap']

def test_gate_a_failure_enforces_entity_only(tmp_path,monkeypatch):
 monkeypatch.delenv('ASTERISK_ENTITY_ONLY',raising=False)
 folder=tmp_path/'.data/primitive-v3';folder.mkdir(parents=True)
 (folder/'gate-a.json').write_text(json.dumps({'status':'fail','implementation_hash':implementation_hash()}))
 assert categories(tmp_path,date(2026,9,18))==['entity_overlap']
