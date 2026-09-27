import json,subprocess,sys
from pathlib import Path
from tests.test_api import client,HEADERS
from tests.test_investigations import setup,create,PAYLOAD
from tests.test_primitives import ARGS,FILES
from app.receipt import profiles

BAD='"sample,partition\na,train\nb,test\n'

def test_profiles_reports_bad_header_without_crashing():
    assert profiles({'bad.csv':BAD})['bad.csv']['error']=='Malformed CSV. Check quotation marks, headers and row lengths.'

def test_binding_preview_returns_input_error_for_bad_header(setup):
    c,_=setup
    files={**FILES,'bad.csv':BAD}
    id=create(c,{**PAYLOAD,'files':[{'name':n,'content':t} for n,t in files.items()]})
    url='/api/investigations/'+id
    assert c.post(url+'/manual-plan',headers=HEADERS).status_code==200
    r=c.post(url+'/binding-preview',headers=HEADERS,json={'arguments':{**ARGS,'split_file':'bad.csv'}})
    assert r.status_code==422
    assert r.json()['detail']=='Malformed CSV. Check quotation marks, headers and row lengths.'

def test_cli_malformed_header_is_clean_error(tmp_path):
    root=Path(__file__).resolve().parents[1]
    for n,t in FILES.items():
        p=tmp_path/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(t)
    (tmp_path/ARGS['split_file']).write_text(BAD)
    cfg={'schema_version':1,'claim':'Evaluation specimens must be unseen.','files':list(FILES),'arguments':ARGS}
    p=tmp_path/'asterisk.json';p.write_text(json.dumps(cfg))
    r=subprocess.run([sys.executable,str(root/'asterisk.py'),'check',str(p),'--output',str(tmp_path/'out')],capture_output=True,text=True)
    assert r.returncode==2
    assert 'Malformed CSV' in r.stderr and 'Traceback' not in r.stderr
    assert not (tmp_path/'out').exists()


def test_browser_preserved_bom_and_unicode_survive_storage_and_header_profiling(setup):
    c,_=setup
    text='\ufeffsample,identity\r\na,μ\r\nb,�\r\n'
    id=create(c,{**PAYLOAD,'files':[{'name':'bom.csv','content':text}]})
    retained=c.get('/api/investigations/'+id+'/inputs').json()['files'][0]['content']
    assert retained.encode('utf-8')==text.encode('utf-8')
    assert profiles({'bom.csv':retained})['bom.csv']=={
        'rows':2,'columns':{'sample':{'distinct':2,'blank':0},'identity':{'distinct':2,'blank':0}}}
