"""Harness-owned measurements. No model-written result can enter this module's gates.

Static preprocessing is conservative; checkpoint analysis binds supplied helpers.
Unsupported/ambiguous flow is returned as unresolved, never inferred from names.
"""
import ast
import hashlib
import json
from collections import Counter
from .audit import execute,table,AuditError
VERSION='measurements-4'
KINDS=('entity_overlap','fit_sites','fit_trace','symbol_chain')

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def citation(files,c):
    if not isinstance(c,dict) or c.get('file') not in files:raise ValueError('Citation file missing.')
    start,end=c.get('start_line'),c.get('end_line')
    lines=files[c['file']].splitlines()
    if type(start)!=int or type(end)!=int or not 1<=start<=end<=len(lines) or end-start>=40:raise ValueError('Citation needs a valid 1-based range of at most 40 lines.')
    quote='\n'.join(lines[start-1:end])
    if len(quote)>4000:raise ValueError('Citation range exceeds 4000 characters; choose a narrower range.')
    return {'file':c['file'],'start_line':start,'end_line':end,'quote':quote}

def entity_overlap(files,args):
    required=('split_file','sample_column','partition_column','entity_column','train_values','test_values')
    missing=[k for k in required if not args.get(k)]
    if missing:return {'available':False,'missing':missing}
    try:
        result=execute(args,files)
        sf=args['split_file'];mf=args.get('mapping_file') or sf
        _,splits=table(files[sf]);_,mapping=table(files[mf])
        join=args.get('mapping_sample_column') or args['sample_column']
        index={r[join]:r[args['entity_column']] for r in mapping if r[join] and r[args['entity_column']]}
        coverage={}
        for group,labels in [('train',args['train_values']),('test',args['test_values'])]:
            rows=[r for r in splits if r[args['partition_column']] in labels]
            mapped=sum(r[args['sample_column']] in index for r in rows)
            coverage[group]={'rows':len(rows),'mapped':mapped,'complete':mapped==len(rows),'percent':100*mapped/len(rows)}
        for witness in result['witnesses']:
            for side,labels in [('train',args['train_values']),('test',args['test_values'])]:
                ref=witness[side];row=splits[ref['split_row']-2];mapping_row=mapping[ref['mapping_row']-2]
                if not (row[args['partition_column']] in labels and row[args['sample_column']]==ref['sample']==mapping_row[join] and mapping_row[args['entity_column']]==witness['entity']):raise ValueError('Witness verification failed.')
        return {'available':True,**result,'coverage':coverage,'witnesses_verified':True,'entity_column':args['entity_column'],'missing':[] if all(c['complete'] for c in coverage.values()) else ['coverage']}
    except (AuditError,KeyError,ValueError,TypeError) as exc:
        return {'available':False,'missing':['mapping file, entity column, join column, split labels, or coverage'],'error':str(exc)}

def symbol(node):
    if isinstance(node,ast.Name):return node.id
    if isinstance(node,ast.Attribute):return symbol(node.value)+'.'+node.attr
    return ''

def names(node):
    return {symbol(n) for n in ast.walk(node) if isinstance(n,(ast.Name,ast.Attribute)) and isinstance(n.ctx,ast.Load)}-{'self'}

def parse(files,args):
    from .source_analysis import normalize_source
    path=args.get('file') or args.get('entry_file')
    if path not in files:raise ValueError('Source file unavailable.')
    source,normalization=normalize_source(files[path],path)
    tree=ast.parse(source,filename=path)
    tree.asterisk_normalization=normalization
    return path,source,tree

def fit_sites(files,args):
    path,source,tree=parse(files,args)
    classes=args.get('class_names')
    if not isinstance(classes,list) or not classes or any(not isinstance(c,str) for c in classes):raise ValueError('Provide transformer class names.')
    aliases={};assignments={};unpacked={}
    parents={child:parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    def ancestors(node):
        out=[]
        while node in parents:node=parents[node];out.append(node)
        return out
    for node in ast.walk(tree):
        if isinstance(node,ast.ImportFrom):
            for item in node.names:aliases[item.asname or item.name]=item.name
        elif isinstance(node,ast.Import):
            for item in node.names:aliases[item.asname or item.name]=item.name
    # Rebinding makes an imported callable's identity uncertain. Deliberately
    # reject the affected alias for the whole file rather than guess branch,
    # scope, or execution order for a definitive static verdict.
    rebound=set()
    for node in ast.walk(tree):
        if isinstance(node,(ast.Name,ast.Attribute)) and isinstance(node.ctx,(ast.Store,ast.Del)):
            rebound.add(symbol(node).split('.')[0])
        elif isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
            rebound.add(node.name)
        elif isinstance(node,ast.arg):rebound.add(node.arg)
    def call_name(node):
        value=symbol(node.func);root=value.split('.')[0]
        if root in rebound and (root in aliases or value in ('train_test_split','cross_validate','cross_val_score')):
            return '<unresolved rebound callable>'
        return aliases.get(value,value).split('.')[-1]
    for node in ast.walk(tree):
        if isinstance(node,ast.Assign):
            for target in node.targets:
                if isinstance(target,ast.Name):assignments.setdefault(target.id,[]).append((node.lineno,node.value,node))
                elif (isinstance(target,(ast.Tuple,ast.List)) and isinstance(node.value,ast.Call)
                      and call_name(node.value)=='train_test_split' and len(target.elts)==2*len(node.value.args)):
                    for index,element in enumerate(target.elts):
                        if isinstance(element,ast.Name):
                            assignments.setdefault(element.id,[]).append((node.lineno,node.value.args[index//2],node))
                            unpacked[(element.id,node.lineno)]='train_slice' if index%2==0 else 'test_slice'
    splits=[node for node in ast.walk(tree) if isinstance(node,ast.Call) and call_name(node) in ('split','cross_validate','cross_val_score','train_test_split')]
    folds={}
    for node in ast.walk(tree):
        if isinstance(node,ast.For) and isinstance(node.iter,ast.Call) and symbol(node.iter.func).endswith('.split') and isinstance(node.target,(ast.Tuple,ast.List)) and len(node.target.elts)==2:
            folds[node.lineno]={'train':symbol(node.target.elts[0]),'test':symbol(node.target.elts[1]),'source':node.iter.args[0] if node.iter.args else None}
    def definition(name,before):
        choices=[item for item in assignments.get(name,[]) if item[0]<before]
        return max(choices,key=lambda item:item[0]) if choices else None
    def uncertain_definition(node,active=()):
        return any(isinstance(a,(ast.If,ast.FunctionDef,ast.AsyncFunctionDef,ast.Try,ast.While,ast.With,ast.Match))
                   or isinstance(a,ast.For) and a.lineno not in active for a in ancestors(node))
    def whole_columns(node):
        return (isinstance(node,ast.Subscript) and isinstance(node.slice,ast.Attribute)
                and node.slice.attr=='columns' and ast.dump(node.value)==ast.dump(node.slice.value))
    def preserving_call(node):
        """Return row-source expressions only for bounded row-preserving calls."""
        name=call_name(node)
        if name in ('fit_transform','transform','array','asarray','DataFrame') and node.args:return node.args[:1]
        if name in ('vstack','concatenate','concat') and node.args:
            first=node.args[0]
            return first.elts if isinstance(first,(ast.List,ast.Tuple)) else []
        if isinstance(node.func,ast.Attribute) and name in ('copy','reset_index','astype','to_numpy','toarray'):
            return [node.func.value]
        if isinstance(node.func,ast.Attribute) and name=='drop' and any(k.arg=='axis' and isinstance(k.value,ast.Constant) and k.value.value in (1,'columns') for k in node.keywords):
            return [node.func.value]
        return []
    def row_roots(node,before,seen=frozenset(),active=()):
        """Definition identities, not variable spellings, bind a fit to a split."""
        if node is None:return set()
        if isinstance(node,ast.Name):
            d=definition(node.id,before)
            if not d:return {('external',node.id)}
            identity=(node.id,d[0])
            if identity in seen or uncertain_definition(d[2],active):return set()
            return row_roots(d[1],d[0],seen|{identity},active)
        if whole_columns(node):
            return row_roots(node.value,before,seen,active)
        if isinstance(node,ast.Attribute) and node.attr=='values':return row_roots(node.value,before,seen,active)
        if isinstance(node,ast.Call):
            inputs=preserving_call(node)
            if inputs:return set().union(*(row_roots(x,before,seen,active) for x in inputs))
        return {('expression',getattr(node,'lineno',0),getattr(node,'col_offset',0),ast.dump(node))}
    def split_inputs(call):
        name=call_name(call)
        if name in ('cross_validate','cross_val_score'):
            return call.args[1:2] or [k.value for k in call.keywords if k.arg=='X']
        if name=='train_test_split':return call.args
        return call.args[:1]
    def matching_split(node,before,active):
        roots=row_roots(node,before,active=active)
        return bool(roots) and any(not uncertain_definition(call,active) and roots & row_roots(value,call.lineno,active=active)
                                  for call in splits for value in split_inputs(call))
    def unresolved(node):return {'resolved':False,'kind':'unresolved','expression':ast.unparse(node)}
    def resolve(node,before,active,seen=frozenset()):
        if isinstance(node,ast.Name):
            d=definition(node.id,before)
            if not d:return unresolved(node)
            identity=(node.id,d[0])
            if identity in seen or uncertain_definition(d[2],active):return unresolved(node)
            if identity in unpacked:
                r={'resolved':True,'kind':unpacked[identity],'expression':node.id,'split_line':d[0]}
            else:
                r=resolve(d[1],d[0],active,seen|{identity})
                # Unknown loaders are full only when the same definition flows to a split.
                if not r['resolved'] and matching_split(node,before,active):r={'resolved':True,'kind':'full','expression':node.id}
            return {**r,'definition_line':d[0],'definition':ast.unparse(d[1])}
        if isinstance(node,ast.Subscript):
            if whole_columns(node):return {**resolve(node.value,before,active,seen),'expression':ast.unparse(node),'selection':'all rows / columns'}
            indices=names(node.slice)
            train={folds[line]['train'] for line in active};test={folds[line]['test'] for line in active}
            # Index roles apply only to the matrix split by that loop.
            roots=row_roots(node.value,before,active=active)
            relevant=[line for line in active if roots & row_roots(folds[line]['source'],line,active=active)]
            if indices & {folds[line]['test'] for line in relevant}:return {'resolved':True,'kind':'test_slice','expression':ast.unparse(node)}
            if indices & {folds[line]['train'] for line in relevant} and not indices & test:return {'resolved':True,'kind':'train_slice','expression':ast.unparse(node)}
            return unresolved(node)
        if isinstance(node,ast.Call):
            children=[resolve(child,before,active,seen) for child in preserving_call(node)]
            kinds={child['kind'] for child in children}
            if children and all(child['resolved'] for child in children):
                if kinds & {'test_slice','includes_test'}:kind='includes_test'
                elif 'full' in kinds:kind='full'
                elif kinds=={'train_slice'}:kind='train_slice'
                else:return unresolved(node)
                return {'resolved':True,'kind':kind,'expression':ast.unparse(node)}
            if call_name(node) in ('array','arange','zeros','ones') and all(isinstance(arg,(ast.Constant,ast.List,ast.Tuple)) for arg in node.args):
                return {'resolved':True,'kind':'full','expression':ast.unparse(node)}
        if isinstance(node,(ast.List,ast.Tuple)) and all(isinstance(item,(ast.Constant,ast.List,ast.Tuple)) for item in node.elts):return {'resolved':True,'kind':'full','expression':ast.unparse(node)}
        if isinstance(node,ast.Attribute) and node.attr=='values':return resolve(node.value,before,active,seen)
        return unresolved(node)
    def class_of(node,before,active,seen=frozenset()):
        if isinstance(node,ast.Call):return call_name(node)
        if isinstance(node,ast.Name):
            d=definition(node.id,before)
            if d and (node.id,d[0]) not in seen and not uncertain_definition(d[2],active):return class_of(d[1],d[0],active,seen|{(node.id,d[0])})
        return None
    constructions=[];fits=[]
    for node in ast.walk(tree):
        if not isinstance(node,ast.Call):continue
        cname=call_name(node)
        if cname in classes:constructions.append({'class':cname,'line':node.lineno,'text':ast.get_source_segment(source,node)})
        if not (isinstance(node.func,ast.Attribute) and node.func.attr in ('fit','fit_transform','partial_fit')):continue
        active=[a.lineno for a in ancestors(node) if isinstance(a,ast.For) and a.lineno in folds]
        cls=class_of(node.func.value,node.lineno,active)
        if cls not in classes:continue
        value=node.args[0] if node.args else next((k.value for k in node.keywords if k.arg=='X'),None)
        resolved=resolve(value,node.lineno,active) if value else {'resolved':False,'kind':'unresolved'}
        same=matching_split(value,node.lineno,active) if value else False
        conditional=any(isinstance(a,(ast.If,ast.FunctionDef,ast.AsyncFunctionDef,ast.Try,ast.While,ast.With,ast.Match)) for a in ancestors(node))
        violation=not conditional and bool(splits) and (resolved['kind'] in ('includes_test','test_slice') or resolved['kind']=='full' and same)
        fits.append({'line':node.lineno,'class':cls,'argument':ast.unparse(value) if value else None,'resolution':resolved,'fold_index_slice':resolved['kind']=='train_slice','enclosing_loops':[a.lineno for a in ancestors(node) if isinstance(a,(ast.For,ast.While))],'fold_loops':active,'text':ast.get_source_segment(source,node),'conditional_or_function_scope':conditional,'same_split_source':same,'violation':violation})
    return {'available':True,'file':path,'normalization':tree.asterisk_normalization,'constructions':constructions,'fit_calls':fits,'split_calls':[{'line':node.lineno,'text':ast.get_source_segment(source,node)} for node in splits],'missing':[] if splits and fits else ['split call' if not splits else 'fit call']}

def symbol_chain(files,args):
    from .checkpoint import symbol_chain as bound_chain
    return bound_chain(files,args)


def measure(kind,files,args):
    if kind not in KINDS or not isinstance(args,dict):raise ValueError('Unknown primitive or invalid arguments.')
    try:
        if kind=='fit_trace':
            from .fit_trace import fit_trace
            output=fit_trace(files,args)
        else:output=globals()[kind](files,args)
    except (ValueError,TypeError,KeyError,SyntaxError) as exc:output={'available':False,'missing':['measurement unavailable'],'error':str(exc)}
    return {'primitive':kind,'version':VERSION,'arguments':args,'input_hashes':{n:hashlib.sha256(v.encode()).hexdigest() for n,v in files.items()},'output':output}

def gate(category,records,citations):
    """Compute the only permitted verdict from retained trusted primitive records."""
    selected=[r for r in records if r.get('version')==VERSION]
    outputs=lambda kind:sorted([r['output'] for r in selected if r['primitive']==kind],key=lambda o:not (o.get('violation') or o.get('shared_entities',0)>0))
    missing=[];limitations=[]
    if category=='entity_overlap':
        for o in outputs('entity_overlap'):
            if not o.get('available'):missing+=o.get('missing',[]);continue
            if o['shared_entities']>0 and o['witnesses'] and o['witnesses_verified']:return {'verdict':'violation','passed':True,'missing':[],'limitations':['Recorded entity identities only; no accuracy effect established.']}
            if o['shared_entities']==0 and all(c['complete'] for c in o['coverage'].values()):
                record=next(r for r in selected if r['primitive']=='entity_overlap' and r['output'] is o)
                binding={'entity_column':o['entity_column'],'mapping_file':(record['arguments'].get('mapping_file') or record['arguments']['split_file']),
                         'input_hashes':record['input_hashes'],'arguments':record['arguments']}
                binding['text']=f"{binding['entity_column']} in {binding['mapping_file']} is the generating unit named by this claim."
                return {'verdict':'clear_pending_confirmation','passed':True,'missing':['human confirmation of the entity binding'],
                        'binding':binding,'limitations':['No shared recorded identities in the selected partitions; semantic identity binding requires human review.']}
            missing+=o.get('missing',[])
    elif category=='preprocessing':
        for o in outputs('fit_trace'):
            if o.get('available') and any(e.get('includes_test') for e in o.get('events',[])):return {'verdict':'violation','passed':True,'missing':[],'limitations':['Observed fit events in the supplied execution only.']}
        for o in outputs('fit_sites'):
            if any(f.get('violation') for f in o.get('fit_calls',[])):return {'verdict':'violation','passed':True,'missing':[],'limitations':['Resolved static fit-site flow; unsupported aliases remain unresolved.']}
        for o in outputs('fit_trace'):
            if o.get('available') and o.get('complete') and o.get('events') and all(e.get('exact_train') for e in o['events']):return {'verdict':'clear','passed':True,'missing':[],'limitations':['Every observed fit matched its fold training fingerprint; supplied run only.']}
        missing=['complete fit trace matching every fold training fingerprint'];missing+=[m for o in outputs('fit_trace')+outputs('fit_sites') for m in o.get('missing',[])]
    elif category=='checkpoint_selection':
        for o in outputs('symbol_chain'):
            if o.get('violation'):return {'verdict':'violation','passed':True,'missing':[],'limitations':['Verified five-link source chain; historical execution not recovered.']}
            if o.get('clear'):
                limitations=['validation and test disjointness not established']
                # An arbitrary train/test overlap record is not proof of validation/test disjointness.
                return {'verdict':'clear','passed':True,'missing':[],'limitations':limitations}
            missing+=o.get('missing',[])
    else:raise ValueError('Unknown investigation category.')
    return {'verdict':'insufficient','passed':True,'missing':sorted(set(missing or ['required trusted primitive measurement'])),'limitations':['Required evidence gate was not established.']}
