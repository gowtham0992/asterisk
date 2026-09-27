import copy,json,sqlite3
import pytest
from app.preparation.store import DraftStore,MissingDraft,StaleDraft,DraftLimit
from app.preparation.draft import save
from tests.test_preparation_package import prepared


@pytest.fixture
def storage(tmp_path):
    path=tmp_path/'drafts.sqlite'
    def connect():
        db=sqlite3.connect(path);db.row_factory=sqlite3.Row;return db
    return DraftStore(connect),connect


def record():
    session=prepared();return save(session,session.review['review_hash'])


def test_restart_reopens_recomputed_unconfirmed_draft(storage):
    store,connect=storage;draft=record();meta=store.create('alice',' My preparation ',draft)
    reopened=DraftStore(connect).load('alice',meta['id'])
    assert reopened['title']=='My preparation' and reopened['revision']==1
    assert reopened['session'].confirmation is None
    assert reopened['session'].review['reviewed_population']=={'train':1,'test':1,'excluded':0}
    assert reopened['session'].files==draft['inputs']
    assert set(store.list('alice')[0])=={'id','title','revision','created_at','updated_at'}


def test_other_owner_cannot_list_load_or_update(storage):
    store,_=storage;meta=store.create('alice','Private draft',record())
    assert store.list('bob')==[]
    with pytest.raises(MissingDraft):store.load('bob',meta['id'])
    with pytest.raises(MissingDraft):store.update('bob',meta['id'],1,'Changed',record())
    assert store.load('alice',meta['id'])['title']=='Private draft'


def test_stale_second_tab_cannot_overwrite_newer_draft(storage):
    store,connect=storage;meta=store.create('alice','Original',record())
    second=DraftStore(connect);before=second.load('alice',meta['id'])
    changed=store.update('alice',meta['id'],1,'Revised',record())
    assert changed['revision']==2 and changed['created_at']==meta['created_at']
    with pytest.raises(StaleDraft):second.update('alice',meta['id'],before['revision'],'Old tab',record())
    assert store.load('alice',meta['id'])['title']=='Revised'


def test_update_committed_during_validation_cannot_be_overwritten(storage,monkeypatch):
    import app.preparation.store as module
    store,connect=storage;draft=record();meta=store.create('alice','Original',draft)
    second=DraftStore(connect);validate=module.validated_payload
    def competing_update(value):
        # A second request commits after this request read revision 1 but
        # before its write transaction starts. Exercise the SQL guard itself.
        monkeypatch.setattr(module,'validated_payload',validate)
        second.update('alice',meta['id'],1,'Concurrent edit',draft)
        return validate(value)
    monkeypatch.setattr(module,'validated_payload',competing_update)
    with pytest.raises(StaleDraft):store.update('alice',meta['id'],1,'Lost edit',draft)
    persisted=store.load('alice',meta['id'])
    assert persisted['title']=='Concurrent edit' and persisted['revision']==2


def test_invalid_replacement_leaves_persisted_draft_intact(storage):
    store,_=storage;original=record();meta=store.create('alice','Original',original)
    broken=copy.deepcopy(original);broken['inputs']['data.csv']='broken'
    with pytest.raises(ValueError):store.update('alice',meta['id'],1,'Bad',broken)
    after=store.load('alice',meta['id'])
    assert after['revision']==1 and after['title']=='Original'
    assert after['session'].files==original['inputs']


def test_confirmation_cannot_enter_storage(storage):
    store,_=storage;session=prepared()
    confirmed=session.confirm(session.review['review_hash'],True)
    with pytest.raises(ValueError):store.create('alice','Confirmed',confirmed)
    draft=record();draft['confirmation']={'accepted':True}
    with pytest.raises(ValueError):store.create('alice','Injected',draft)
    assert store.list('alice')==[]


def test_quota_is_per_owner_and_invalid_metadata_is_rejected(storage):
    store,_=storage;draft=record()
    for i in range(10):store.create('alice',str(i),draft)
    with pytest.raises(DraftLimit):store.create('alice','Eleventh',draft)
    assert store.create('bob','Other workspace',draft)['revision']==1
    for owner,title in [('', 'Title'),('alice',' '),('alice','x'*121)]:
        with pytest.raises(ValueError):store.create(owner,title,draft)
    with pytest.raises(ValueError):store.update('alice','unknown',True,'Title',draft)


def test_tampered_database_payload_is_not_trusted(storage):
    store,connect=storage;meta=store.create('alice','Original',record())
    with connect() as db:
        db.execute('UPDATE preparation_drafts SET payload=? WHERE id=?',(json.dumps({'draft_version':1}),meta['id']))
    with pytest.raises(ValueError):store.load('alice',meta['id'])


def test_concurrent_create_retries_commit_one_draft(storage):
    from concurrent.futures import ThreadPoolExecutor
    store,connect=storage;draft=record();key='a'*32
    def create(_):return DraftStore(connect).create('alice','Retry-safe',draft,key)
    with ThreadPoolExecutor(max_workers=2) as pool:responses=list(pool.map(create,range(2)))
    assert responses[0]==responses[1]
    assert len(store.list('alice'))==1
    # Reopening and replaying the request preserves the first response.
    assert create(None)==responses[0]
    with pytest.raises(StaleDraft,match='different choices'):
        store.create('alice','Changed',draft,key)
    assert store.create('bob','Retry-safe',draft,key)['id']!=responses[0]['id']


def test_retry_does_not_resurrect_deleted_draft_or_reset_edited_draft(storage):
    store,_=storage;draft=record();key='a'*32
    first=store.create('alice','Original',draft,key)
    changed=store.update('alice',first['id'],1,'Edited',draft)
    assert store.create('alice','Original',draft,key)==first
    assert store.load('alice',first['id'])['title']=='Edited'
    store.delete('alice',first['id'],changed['revision'])
    with pytest.raises(StaleDraft,match='deleted'):store.create('alice','Original',draft,key)
    assert store.list('alice')==[]


def test_retry_is_available_at_draft_quota(storage):
    store,_=storage;draft=record();key='a'*32
    first=store.create('alice','Original',draft,key)
    for i in range(9):store.create('alice',str(i),draft)
    assert store.create('alice','Original',draft,key)==first
    with pytest.raises(DraftLimit):store.create('alice','New',draft,'b'*32)
