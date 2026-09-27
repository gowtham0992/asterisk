"""Integration boundary for reviewed preparation, without enabling its routes."""
import json
import subprocess
import sys
from pathlib import Path
import pytest
from app.preparation.intake import open_inputs,reopen
from app.preparation.draft import save
from app.preparation.handoff import archive
from app.preparation.verify_record import verify

ROOT=Path(__file__).resolve().parents[1]


def prepared():
    files={'data.csv':'sample,subject,split\na,p1,train\nb,p2,test\n',
           'notes.txt':'sample identifies an observation; subject identifies its generating unit.'}
    spec={'status':'extract','sources':[{'file':'data.csv','format':'csv','sample':{'column':'sample'},'entity':{'column':'subject'},'partition':{'column':'split','map':{'train':'train','test':'test'}}}],
          'citations':[{'file':'notes.txt','start_line':1,'end_line':1}]}
    session=open_inputs(json.dumps(spec),files)
    session.preview({'data.csv':{'sample':{'column':'sample'},'repeats':'distinct','evidence':spec['citations']}})
    return session


def test_application_import_round_trip_keeps_drafts_unconfirmed():
    session=prepared();record=save(session,session.review['review_hash'])
    restored=reopen(json.dumps(record))
    assert restored.review==session.review and restored.confirmation is None
    with pytest.raises(ValueError):archive(record)
    confirmed=restored.confirm(restored.review['review_hash'],True)
    assert verify(confirmed)['recomputed_population']=={'train':1,'test':1,'excluded':0}
    assert archive(confirmed).startswith(b'PK')


def test_legacy_verifier_still_runs_outside_repository(tmp_path):
    session=prepared();record=session.confirm(session.review['review_hash'],True)
    source=tmp_path/'record.json';source.write_text(json.dumps(record))
    result=subprocess.run([sys.executable,str(ROOT/'research/extraction-observation-review/verify_record.py'),str(source)],cwd=tmp_path,capture_output=True,text=True,check=True)
    assert json.loads(result.stdout)==verify(record)


def test_package_does_not_import_generic_prototype_names_or_open_network():
    code='''
import sys,types,socket
for name in ('review','session','intake','verify_record','model_record','handoff','draft'):
    sys.modules[name]=types.ModuleType(name)
def forbidden(*args,**kwargs):raise AssertionError('Unexpected network access')
socket.socket=forbidden
from app.preparation.intake import open_inputs
from app.preparation.draft import restore
from app.preparation.handoff import archive
assert callable(open_inputs) and callable(restore) and callable(archive)
'''
    subprocess.run([sys.executable,'-c',code],cwd=ROOT,capture_output=True,text=True,check=True)


def test_realistic_lineage_export_fits_without_dropping_record_fields():
    """Formatting overhead must not block otherwise supported benchmark sizes."""
    from app.preparation.handoff import files_for
    template=prepared()
    rows=['sample,subject,split']
    for i in range(18000):
        rows.append(f'sample-{i:06d},subject-{i//2:06d},'+('train' if i<14000 else 'test'))
    files={'data.csv':'\n'.join(rows)+'\n','notes.txt':template.files['notes.txt']}
    session=open_inputs(json.dumps(template.spec),files)
    session.preview({'data.csv':{'sample':{'column':'sample'},'repeats':'distinct','evidence':template.spec['citations']}})
    # Synthetic developer fixture, not a real research confirmation.
    record=session.confirm(session.review['review_hash'],True)
    assert len(json.dumps(record,ensure_ascii=False,indent=2).encode())>10_000_000
    exported=files_for(record)
    assert len(exported['preparation-review.json'].encode())<10_000_000
    assert sum(len(value.encode()) for value in exported.values())<16_000_000
    assert json.loads(exported['preparation-review.json'])==record
    assert len(record['review']['extraction']['lineage'])==18000
    from app.prepared_archive import unpack
    imported={item['name']:item['content'] for item in unpack(archive(record))}
    assert imported==exported
