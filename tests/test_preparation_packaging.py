"""A clean source distribution must load preparation without the developer tree."""
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile


def test_clean_archive_imports_preparation_and_executes_offline(tmp_path):
    from scripts.package_release import release_files,package
    root=Path(__file__).resolve().parents[1]
    staging=tmp_path/'source';staging.mkdir()
    for source in release_files(root):
        target=staging/source.relative_to(root);target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target)
    with zipfile.ZipFile(package(staging)) as archive:
        names=archive.namelist()
        assert {'asterisk/evaluation/real-preparation-v1/PROTOCOL.md',
                'asterisk/research/extraction-observation-review/verify_record.py'} <= set(names)
        extraction_files={name for name in names if '/evaluation/extraction-' in name}
        assert extraction_files=={'asterisk/evaluation/'+name for name in (
            'extraction-v1/executor.py','extraction-v2/proposal.py','extraction-v3/proposal.py',
            'extraction-holdout-v1/completion.py','extraction-holdout-v1/deadline.py','extraction-holdout-v1/worker.py')}
        assert not any('/.data/' in name or name.endswith('/.env') for name in names)
        archive.extractall(tmp_path/'extracted')
    extracted=tmp_path/'extracted/asterisk'
    # Resolve shipped relative imports from extracted bytes, not the developer tree.
    for module in (extracted/'static').rglob('*'):
        if module.suffix not in ('.js','.mjs'):
            continue
        for reference in re.findall(r"(?:from\s*|import\s*)['\"](\.[^'\"]+)['\"]", module.read_text()):
            dependency=(module.parent/reference.split('?',1)[0]).resolve()
            assert dependency.is_relative_to(extracted.resolve()), reference
            assert dependency.is_file(), f'{module.relative_to(extracted)} imports missing {reference}'
    program='''
import sys, socket
sys.path.insert(0, '.')
def no_network(*args, **kwargs): raise AssertionError('Packaging test attempted network access')
socket.socket.connect = no_network
from app.main import app
from app.binding_examples import source_examples
from app.preparation.proposal import ProposalRequest
from app.preparation.review import executor
from app.preparation import provider
files={'data.csv':'sample,subject,split\\na,p1,train\\nb,p2,test\\n', 'notes.txt':'sample is an observation. subject is the generating unit.'}
request=ProposalRequest(files,'Evaluation subjects must be absent from training.',['notes.txt'])
assert request.preview()['maximum_output_tokens']==4000
spec={'status':'extract','sources':[{'file':'data.csv','format':'csv','sample':{'column':'sample'},'entity':{'column':'subject'},'partition':{'column':'split','map':{'train':'train','test':'test'}}}],'citations':[{'file':'notes.txt','start_line':1,'end_line':1}]}
result=executor.extract(spec,files)
assert len(result['lineage'])==2
from app.preparation.intake import open_inputs
from app.preparation.handoff import files_for
from app.preparation.receipt_context import retained_preparation
session=open_inputs(executor.canonical(spec),files)
review=session.preview({'data.csv':{'sample':{'column':'sample'},'repeats':'distinct','evidence':spec['citations']}})
record=session.confirm(review['review_hash'],True)
record['confirmation']['actor']='automated packaging fixture; not human validation'
record['record_hash']=executor.sha(executor.canonical({k:v for k,v in record.items() if k!='record_hash'}))
context=retained_preparation(files_for(record))
assert context['actor']=='automated packaging fixture; not human validation'
assert context['passages'][0]['quote']==files['notes.txt']
args={'split_file':'data.csv','mapping_file':'data.csv','sample_column':'sample','mapping_sample_column':'sample','entity_column':'subject','partition_column':'split','train_values':['train'],'test_values':['test']}
assert [r['entity'] for r in source_examples(files,args)['rows']]==['p1','p2']
from pathlib import Path
for name in ('synthetic-example.js','claim-draft.js','setup-backup.js','setup-reload-guard.js'):
    assert Path('static',name).is_file()
assert provider.deadline.Path(provider.deadline.__file__).with_name('worker.py').is_file()
# Run fresh provider setup with no developer .data directory and no network.
from app.preparation.init_budget import initialize
from app.preparation.runtime import configure
budget_path=Path('fresh-budget.json').resolve()
initialize(budget_path, .01)
calls=[]
def stub(action,payload,timeout):
    calls.append(action)
    return {'usage':{'prompt_tokens':1,'completion_tokens':1},'choices':[{'message':{'content':'offline'}}]}
adapter=provider.configured(environ={'ASTERISK_PREPARATION_BUDGET':str(budget_path),'NEBIUS_API_KEY':'fake'},worker=stub)
configure(app,environ={'ASTERISK_PREPARATION_NEBIUS':'1'},factory=lambda:adapter)
assert app.state.preparation_complete([],100,10)['content']=='offline'
assert calls==['complete']
assert not Path('.data/extraction-v1/cost-start.json').exists()
assert any(route.path=='/api/preparations' for route in app.routes)
print('clean archive preparation passed')
'''
    env={'PATH':os.environ.get('PATH',''),'ASTERISK_DB':str(tmp_path/'isolated.sqlite'),'ASTERISK_PREPARATION_NEBIUS':'0'}
    result=subprocess.run([sys.executable,'-I','-c',program],cwd=extracted,env=env,capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stderr
    assert 'clean archive preparation passed' in result.stdout
