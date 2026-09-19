"""Remote execution adapter for baked, immutable harness measurements."""
import hashlib,json
from pathlib import Path
from .probes import ProbeSandbox,validate_files,sha
from .primitives import VERSION
FILES=('audit.py','primitives.py','fit_trace.py','source_analysis.py','checkpoint.py')
SOURCES={n:(Path(__file__).parent/n).read_text() for n in FILES}
def implementation_hash():
    return sha(json.dumps({n:sha(v) for n,v in SOURCES.items()},sort_keys=True))
BOOTSTRAP='''import ctypes,json,os,pathlib,sys
request=json.load(sys.stdin)
pathlib.Path('/work/request.json').write_text(json.dumps(request))
pathlib.Path('/work/inputs').mkdir(parents=True,exist_ok=True)
libc=ctypes.CDLL(None,use_errno=True)
if libc.unshare(0x40000000)!=0:sys.exit(78)
os.setgroups([]);os.setgid(65534);os.setuid(65534)
os.chdir('/work/inputs')
os.execve('/usr/local/bin/python',['python','/opt/asterisk/primitive_main.py'],{'PATH':'/usr/local/bin:/usr/bin:/bin','PYTHONHASHSEED':'0','OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','HOME':'/tmp'})
'''
DRIVER='''import json,hashlib,pathlib,sys
sys.path.insert(0,'/opt/asterisk')
from app.primitives import measure
request=json.loads(pathlib.Path('/work/request.json').read_text())
files={n:pathlib.Path('/work/inputs',n).read_text() for n in request['input_names']}
result=measure(request['kind'],files,request['arguments'])
parts={n:hashlib.sha256(pathlib.Path('/opt/asterisk/app',n).read_bytes()).hexdigest() for n in __TRUSTED_FILES__}
result['implementation_hash']=hashlib.sha256(json.dumps(parts,sort_keys=True).encode()).hexdigest()
print(json.dumps(result,sort_keys=True,allow_nan=False))
'''.replace('__TRUSTED_FILES__',repr(FILES))
class PrimitiveSandbox(ProbeSandbox):
    sources=SOURCES
    def primitive(self,kind,args,files):
        validate_files(files)
        request={'kind':kind,'arguments':args,'input_names':list(files)}
        try:
            result=self.client.images.use(self.image).run('python',args=['-c',BOOTSTRAP],stdin=json.dumps(request),files={'/work/inputs/'+n:v.encode() for n,v in files.items()},timeout=30,disposable=True,truncate_output_at=65536).wait()
            if result.exit_code!=0 or result.result.truncated:raise ValueError('Primitive failed or output truncated.')
            record=json.loads(result.stdout)
            if record.get('implementation_hash')!=implementation_hash() or record.get('version')!=VERSION or record.get('primitive')!=kind or record.get('arguments')!=args or record.get('input_hashes')!={n:sha(v) for n,v in files.items()}:raise ValueError('Baked primitive provenance mismatch. Rebuild the measurement image.')
            return {**record,'execution':{'image':self.image,'bootstrap_hash':sha(BOOTSTRAP),'seconds':result.result.elapsed_time.total_seconds(),'exit_code':result.exit_code}}
        except Exception as exc:
            return {'primitive':kind,'version':VERSION,'arguments':args,'input_hashes':{n:sha(v) for n,v in files.items()},'output':{'available':False,'missing':['trusted primitive execution'],'error':type(exc).__name__},'execution_error':True}
