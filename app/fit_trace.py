"""Trusted fit/split hooks for a bounded scientific-script grammar.

This module is invoked only in a Nebius VM in the application. The script cannot
import the harness, mutate attributes, define callbacks, introspect objects or
replace hooks. Rejection is trace unavailable, never evidence of a clear result.
"""
import ast
import contextlib
import hashlib
import inspect
import io
import json
from collections import Counter
from .source_analysis import normalize_source

MODULES={'numpy','sklearn.preprocessing','sklearn.feature_selection','sklearn.decomposition','sklearn.impute','sklearn.linear_model','sklearn.pipeline','sklearn.model_selection','sklearn.datasets'}
METHODS={'partial_fit','fit','fit_transform','transform','split','predict','score','reshape','copy','astype','tolist'}
NUMPY={'array','arange','zeros','ones','vstack','hstack','concatenate','stack','mean','sum','allclose','asarray','linspace'}

def validate_script(source):
    tree=ast.parse(source);imports={}
    for node in ast.walk(tree):
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef,ast.Lambda,ast.With,ast.AsyncWith,ast.Try,ast.While,ast.Global,ast.Nonlocal,ast.Delete,ast.NamedExpr,ast.Await,ast.Yield,ast.YieldFrom)):
            raise ValueError('Unsupported script construct: '+type(node).__name__)
        if isinstance(node,ast.Name) and node.id.startswith('_'):raise ValueError('Private/introspection names are unsupported.')
        if isinstance(node,ast.Attribute) and (node.attr.startswith('_') or isinstance(node.ctx,ast.Store)):raise ValueError('Private attributes and attribute mutation are unsupported.')
        if isinstance(node,ast.Import):
            for a in node.names:
                if a.name not in MODULES:raise ValueError('Unsupported import: '+a.name)
                imports[a.asname or a.name]=a.name
        if isinstance(node,ast.ImportFrom):
            if node.module not in MODULES or node.level:raise ValueError('Unsupported import module.')
            for a in node.names:
                if a.name=='*' or a.name.startswith('_'):raise ValueError('Wildcard/private imports unsupported.')
                imports[a.asname or a.name]=node.module+'.'+a.name
    safe_names={'print','range','len','enumerate','zip','list','tuple','int','float','str','bool','min','max','sum'}
    for node in ast.walk(tree):
        if isinstance(node,ast.Call):
            if isinstance(node.func,ast.Name):
                target=imports.get(node.func.id)
                if node.func.id not in safe_names and not target:raise ValueError('Unsupported callable: '+node.func.id)
                if target and target.startswith('numpy.') and target.split('.')[-1] not in NUMPY:raise ValueError('Unsupported numpy callable.')
            elif isinstance(node.func,ast.Attribute):
                root=node.func
                while isinstance(root,ast.Attribute):root=root.value
                imported=imports.get(root.id,'') if isinstance(root,ast.Name) else ''
                if imported=='numpy':
                    if not isinstance(node.func.value,ast.Name) or node.func.attr not in NUMPY:raise ValueError('Unsupported numpy access.')
                elif node.func.attr not in METHODS and not imported.startswith('sklearn.'):raise ValueError('Unsupported method: '+node.func.attr)
            else:raise ValueError('Indirect calls unsupported.')
            if any(k.arg=='n_jobs' and not (isinstance(k.value,ast.Constant) and k.value.value in (None,1)) for k in node.keywords):raise ValueError('Trace requires n_jobs=1.')
        # Rebinding an imported symbol could substitute an uninstrumented callable.
        if isinstance(node,ast.Name) and isinstance(node.ctx,ast.Store) and node.id in imports:raise ValueError('Import rebinding unsupported.')
    return tree,imports

def validate_transformers(requested, transformers):
    if not isinstance(requested,list) or any(not isinstance(n,str) or not n for n in requested):
        raise ValueError('class_names must be a list of preprocessing transformer names; use [] to observe all supported transformers.')
    unsupported=sorted(set(requested)-set(transformers))
    if unsupported:
        raise ValueError('Unsupported preprocessing transformer(s): '+', '.join(unsupported)+'. Predictive estimators are not transformers. Use [] to observe all supported transformers.')

def fit_trace(files,args):
    path=args.get('entry_file') or args.get('file')
    if path not in files:return {'available':False,'missing':['entry file'],'error':'Entry file not supplied.'}
    normalization=None
    try:
        source=files[path];normalized,normalization=normalize_source(source,path)
        tree,imports=validate_script(normalized)
        import importlib
        import numpy as np
        import sklearn.model_selection as ms
        from sklearn.model_selection import _validation
        from sklearn.base import TransformerMixin
        requested=args.get('class_names',[])
        modules={n:importlib.import_module(n) for n in MODULES}
        transformers={}
        for name,module in modules.items():
            if not name.startswith('sklearn.'):continue
            for clsname in dir(module):
                cls=getattr(module,clsname)
                if inspect.isclass(cls) and issubclass(cls,TransformerMixin) and cls is not TransformerMixin and hasattr(cls,'fit'):
                    transformers[clsname]=cls
        validate_transformers(requested,transformers)
        # Instrument every supported transformer, not only the model-selected subset.
        events=[];folds=[];active=[None];objects={};row_origins={};ambiguous=[False];patches=[];fitting=[0]
        constructed={};observed=set();holdout_depth=[0];ambiguous_hashes=set()
        def source_line():
            frame=inspect.currentframe()
            try:
                while frame:
                    if frame.f_code.co_filename==path:return frame.f_lineno
                    frame=frame.f_back
            finally:del frame
            return None
        def value_rows(x):
            a=np.asarray(x)
            if a.ndim!=2 or a.dtype.kind not in 'biuf':raise ValueError('Trace supports numeric 2D feature matrices only.')
            if not np.isfinite(a).all():raise ValueError('Nonfinite feature values unsupported.')
            return [hashlib.sha256(json.dumps(row.tolist(),separators=(',',':')).encode()).hexdigest() for row in a]
        def ids(x):
            found=objects.get(id(x))
            if found is not None and found[0] is x:return found[1]
            hashes=value_rows(x)
            if len(set(hashes))!=len(hashes) or any(h in ambiguous_hashes for h in hashes):ambiguous[0]=True
            values=[row_origins.get(h,h) for h in hashes]
            objects[id(x)]=(x,values)
            return values
        def remember(result,origins):
            if hasattr(result,'shape') and len(result.shape)==2 and result.shape[0]==len(origins):
                objects[id(result)]=(result,list(origins))
                for h,origin in zip(value_rows(result),origins):
                    if h in row_origins and row_origins[h]!=origin:ambiguous_hashes.add(h)
                    row_origins[h]=origin
        def fingerprint(values):return hashlib.sha256(json.dumps(sorted(Counter(values).items())).encode()).hexdigest()
        def add_fold(x,train,test):
            origin=ids(x);tr=[origin[int(i)] for i in train];te=[origin[int(i)] for i in test]
            f={'id':len(folds)+1,'line':source_line(),'kind':'split','train':tr,'test':te,'train_fingerprint':fingerprint(tr),'test_fingerprint':fingerprint(te)};folds.append(f);return f
        def patch(obj,name,fn):
            owned=name in obj.__dict__;original=getattr(obj,name);patches.append((obj,name,original,owned));setattr(obj,name,fn(original))
        def constructor_hook(clsname):
            def factory(original):
                # sklearn inspects constructor signatures while cloning estimators.
                import functools
                @functools.wraps(original)
                def wrapped(self,*a,**kw):
                    result=original(self,*a,**kw)
                    if source_line() is not None:constructed[id(self)]=(self,clsname)
                    return result
                return wrapped
            return factory
        def fit_hook(clsname,method):
            def factory(original):
                def wrapped(self,X,*a,**kw):
                    origins=ids(X);outer=fitting[0]==0;fitting[0]+=1
                    observed.add(id(self))
                    try:
                        if outer:events.append({'class':clsname,'method':method,'line':source_line(),'row_ids':list(origins),'fold':active[0]['id'] if active[0] else None,'fit_fingerprint':fingerprint(origins)})
                        result=original(self,X,*a,**kw)
                        if method=='fit_transform':remember(result,origins)
                        return result
                    finally:fitting[0]-=1
                return wrapped
            return factory
        def transform_hook(original):
            def wrapped(self,X,*a,**kw):
                origins=ids(X);result=original(self,X,*a,**kw);remember(result,origins);return result
            return wrapped
        # Install inherited methods before mutating any base class, avoiding wrapper stacking.
        originals={(cls,name):getattr(cls,name) for cls in set(transformers.values()) for name in ('fit','fit_transform','partial_fit','transform','__init__') if hasattr(cls,name)}
        for clsname,cls in transformers.items():
            for name in ('fit','fit_transform','partial_fit','transform','__init__'):
                if (cls,name) not in originals:continue
                factory=constructor_hook(clsname) if name=='__init__' else transform_hook if name=='transform' else fit_hook(clsname,name)
                original=originals[cls,name]
                patch(cls,name,lambda ignored,factory=factory,original=original:factory(original))
        def splitter_hook(original):
            def wrapped(self,X,y=None,groups=None):
                for train,test in original(self,X,y,groups):
                    if holdout_depth[0] or fitting[0]:
                        yield train,test
                        continue
                    previous=active[0];active[0]=add_fold(X,train,test)
                    try:yield train,test
                    finally:active[0]=previous
            return wrapped
        for name in ('KFold','StratifiedKFold','GroupKFold','ShuffleSplit','StratifiedShuffleSplit','GroupShuffleSplit','TimeSeriesSplit'):
            patch(getattr(ms,name),'split',splitter_hook)
        def holdout_hook(original):
            def wrapped(*arrays,**kw):
                if not arrays:raise ValueError('Holdout needs arrays.')
                # Append row indices to the same split call: no second RNG draw.
                index=np.arange(len(arrays[0]));holdout_depth[0]+=1
                try:result=original(*arrays,index,**kw)
                finally:holdout_depth[0]-=1
                record=add_fold(arrays[0],result[-2],result[-1]);record['kind']='holdout'
                for i,array in enumerate(arrays):
                    if getattr(array,'ndim',None)==2:
                        origin=ids(array)
                        remember(result[2*i],[origin[int(j)] for j in result[-2]])
                        remember(result[2*i+1],[origin[int(j)] for j in result[-1]])
                return result[:-2]
            return wrapped
        patch(ms,'train_test_split',holdout_hook)
        def scoring_hook(original):
            signature=inspect.signature(original)
            def wrapped(*a,**kw):
                bound=signature.bind(*a,**kw).arguments;previous=active[0]
                active[0]=add_fold(bound['X'],bound['train'],bound['test'])
                try:return original(*a,**kw)
                finally:active[0]=previous
            return wrapped
        patch(_validation,'_fit_and_score',scoring_hook)
        def safe_import(name,globals=None,locals=None,fromlist=(),level=0):
            if name not in MODULES or level:raise ValueError('Import rejected.')
            # Restrict imported names to public scientific APIs; no module objects exposing internals.
            module=modules[name]
            for item in (fromlist or ()):
                if item.startswith('_') or not hasattr(module,item):raise ValueError('Import name rejected.')
            return module
        builtins={'__import__':safe_import,'print':print,'range':range,'len':len,'enumerate':enumerate,'zip':zip,'list':list,'tuple':tuple,'int':int,'float':float,'str':str,'bool':bool,'min':min,'max':max,'sum':sum}
        try:
            with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
                exec(compile(tree,path,'exec'),{'__builtins__':builtins})
        finally:
            for obj,name,original,owned in reversed(patches):
                if owned:setattr(obj,name,original)
                else:delattr(obj,name)
        result_events=[];partition_ambiguous=False
        for event in events:
            rows=set(event['row_ids'])
            intersecting=[f for f in folds if rows & (set(f['train'])|set(f['test']))]
            # Active CV scope is authoritative. Outside it only a persistent holdout
            # can bind a subsequent fit; never compare fold A's fit to fold B's test.
            if event['fold']:
                relevant=[f for f in folds if f['id']==event['fold']]
            else:
                relevant=[f for f in intersecting if f['kind']=='holdout'] or intersecting
            exacts=[event['fit_fingerprint']==f['train_fingerprint'] for f in relevant]
            if event['fold'] is None and len(set(exacts))>1:partition_ambiguous=True
            exact=bool(exacts) and all(exacts)
            test=any(rows & set(f['test']) for f in relevant)
            result_events.append({k:v for k,v in event.items() if k!='row_ids'}|{'partition_ids':[f['id'] for f in relevant],'exact_train':exact,'includes_test':bool(test),'rows':len(rows)})
        if ambiguous[0]:return {'available':False,'complete':False,'events':[],'normalization':normalization,'missing':['unambiguous row identities'],'error':'Duplicate row fingerprints cannot establish distinct row membership.'}
        if partition_ambiguous:return {'available':False,'complete':False,'events':result_events,'normalization':normalization,'missing':['ambiguous partition membership']}
        unobserved=sorted({name for ident,(_,name) in constructed.items() if ident not in observed})
        # AST construction check is an additional conservative guard (even dead
        # constructors block completeness); instance tracking prevents same-class masking.
        expected=set()
        for node in ast.walk(tree):
            if isinstance(node,ast.Call):
                target=imports.get(node.func.id,'') if isinstance(node.func,ast.Name) else ast.unparse(node.func)
                name=target.split('.')[-1]
                if name in transformers:expected.add(name)
        unobserved=sorted(set(unobserved)|(expected-{e['class'] for e in events}))
        complete=bool(events and folds) and not unobserved and all(e['partition_ids'] for e in result_events)
        missing=(['constructed transformer without observed fit: '+n for n in unobserved]
                 +([] if all(e['partition_ids'] for e in result_events) and events and folds else ['split call or unambiguous partition association']))
        return {'available':True,'executed_file':path,'source_sha256':hashlib.sha256(source.encode()).hexdigest(),'normalization':normalization,'events':result_events,'folds':[{k:v for k,v in f.items() if k not in ('train','test')} for f in folds],'complete':complete,'unobserved_transformers':unobserved,'missing':missing,'grammar':'restricted scientific script; supported constructors only; no callbacks, private access, attribute writes or parallel jobs'}
    except Exception as exc:
        return {'available':False,'complete':False,'events':[],'normalization':normalization,'missing':['fit trace unavailable'],'error':type(exc).__name__+': '+str(exc)[:500]}
