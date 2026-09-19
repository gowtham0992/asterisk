"""Package verified release bytes only. Test execution is confined to a disposable copy."""
import argparse,hashlib,json,os,subprocess,sys,tempfile,zipfile
from pathlib import Path,PurePosixPath

def permitted(name):
    p=PurePosixPath(name)
    if not name or p.is_absolute() or '..' in p.parts or '\\' in name or str(p)!=name:raise ValueError('Forbidden archive path')
    if any(x.startswith('.') or x=='__pycache__' for x in p.parts) and name not in ('.env.example','.gitignore'):raise ValueError('Forbidden runtime or hidden file')
    if p.suffix.lower() in ('.sqlite','.sqlite3','.db','.pyc'):raise ValueError('Forbidden database or cache')

def build_packet(release,target,*,tester=None):
    release=Path(release);target=Path(target)
    if target.exists():raise ValueError('Choose a new output; prior packets are immutable.')
    with zipfile.ZipFile(release) as z:
        names=z.namelist()
        if len(set(names))!=len(names):raise ValueError('Duplicate archive entries')
        manifest=json.loads(z.read('asterisk/RELEASE-MANIFEST.json'))
        expected={'asterisk/'+n for n in manifest}|{'asterisk/RELEASE-MANIFEST.json'}
        if set(names)!=expected:raise ValueError('Archive contains unlisted files')
        source={}
        for n,h in manifest.items():
            permitted(n);data=z.read('asterisk/'+n)
            if hashlib.sha256(data).hexdigest()!=h:raise ValueError('Source hash mismatch')
            source[n]=data
        source['RELEASE-MANIFEST.json']=z.read('asterisk/RELEASE-MANIFEST.json')
    with tempfile.TemporaryDirectory(prefix='asterisk-review-test-') as d:
        scratch=Path(d)
        for n,b in source.items():
            p=scratch/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
        if tester:result=tester(scratch)
        else:
            env={k:v for k,v in os.environ.items() if not k.startswith(('NEBIUS_','ASTERISK_')) and k not in ('PYTHONPATH','PYTHONHOME')}
            r=subprocess.run([sys.executable,'-m','pytest','-q'],cwd=scratch,env=env,capture_output=True,text=True)
            result={'returncode':r.returncode,'output':r.stdout+r.stderr}
        if result['returncode']:raise ValueError('Extracted tests failed: '+result['output'][-2000:])
    payload={'source/'+n:b for n,b in source.items()}
    status={'source_archive_sha256':hashlib.sha256(release.read_bytes()).hexdigest(),'source_entries':len(manifest),'source_manifest_verified':True,'test_returncode':result['returncode'],'test_environment':'Separate temporary source copy; existing interpreter/dependencies, not a fresh dependency installation.','payload':'Only verified allowlisted release bytes, test output, status and manifests. No test-created files or runtime state.'}
    payload['REVIEW-STATUS.json']=json.dumps(status,indent=2).encode();payload['records/extracted-tests.txt']=result['output'].encode()
    payload['PACKET-MANIFEST.json']=json.dumps({n:hashlib.sha256(b).hexdigest() for n,b in payload.items()},indent=2).encode()
    target.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(target,'x',zipfile.ZIP_DEFLATED) as z:
        for n,b in payload.items():z.writestr(n,b)
    return status

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('release',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    print(json.dumps(build_packet(a.release,a.output),indent=2))
