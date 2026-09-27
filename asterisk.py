"""Notebook export and repeatable local checks. Run: python -m asterisk --help."""
import argparse,csv,io,json,sys
from pathlib import Path


def export_split(directory, *, sample_ids, entity_ids, partitions, claim, identity_definition, train_labels=('train',), test_labels=('test',), title='Notebook split'):
    """Export realized arrays only; never infer a split or execute notebook code."""
    sample_ids=list(sample_ids);entity_ids=list(entity_ids);partitions=list(partitions)
    if not sample_ids or not len(sample_ids)==len(entity_ids)==len(partitions):raise ValueError('All three arrays must have the same nonzero length.')
    if any(v is None for row in zip(sample_ids,entity_ids,partitions) for v in row):raise ValueError('Use explicit IDs and partition labels; None is not an identifier.')
    rows=[(str(s),str(e),str(p)) for s,e,p in zip(sample_ids,entity_ids,partitions)]
    if len({s for s,e,p in rows})!=len(rows) or any(not s or not e or not p for s,e,p in rows):raise ValueError('Sample IDs must be unique and all values nonblank.')
    def emit(header,values):
        f=io.StringIO(newline='');w=csv.writer(f,lineterminator='\n');w.writerow(header);w.writerows(values);return f.getvalue()
    files={'splits.csv':emit(['sample','partition'],[(s,p) for s,e,p in rows]),'identities.csv':emit(['sample','entity'],[(s,e) for s,e,p in rows]),'identity.md':identity_definition+'\n'}
    args={'split_file':'splits.csv','mapping_file':'identities.csv','sample_column':'sample','mapping_sample_column':'sample','partition_column':'partition','entity_column':'entity','train_values':list(train_labels),'test_values':list(test_labels)}
    from app.receipt import preview
    from app.probes import validate_files
    validate_files(files);preview(claim,files,args)
    config={'schema_version':1,'title':title,'claim':claim,'arguments':args,'files':list(files),'scope':'CSV identifiers are exact and can resemble spreadsheet formulas. Import as text. Saved column configuration; review scientific meaning for each new input. No automatic human confirmation.'}
    out=Path(directory);out.mkdir(parents=True,exist_ok=False)
    for name,text in files.items():(out/name).write_text(text)
    (out/'asterisk.json').write_text(json.dumps(config,indent=2));return out/'asterisk.json'


def load_config(path):
    from app.receipt import EntityBinding
    from app.probes import validate_files
    path=Path(path).resolve()
    if path.stat().st_size>100_000:raise ValueError('Configuration is too large.')
    c=json.loads(path.read_text())
    if not isinstance(c,dict):raise ValueError('Configuration must be an object.')
    if not isinstance(c.get('claim'),str) or not 1<=len(c['claim'])<=4000:raise ValueError('Supply a claim of 1–4,000 characters.')
    if not isinstance(c.get('files'),list) or not 1<=len(c['files'])<=80 or any(not isinstance(n,str) for n in c['files']):raise ValueError('Supply 1–80 input filenames.')
    total=0
    if c.get('schema_version')!=1:raise ValueError('Unsupported saved configuration version.')
    args=EntityBinding.model_validate(c['arguments']).model_dump();files={}
    for name in c['files']:
        p=(path.parent/name).resolve()
        if not p.is_relative_to(path.parent) or not p.is_file() or p.stat().st_size>10_000_000:raise ValueError('Input path is unsafe, missing or too large.')
        total+=p.stat().st_size
        if total>16_000_000:raise ValueError('Inputs exceed 16 MB total.')
        if name in files:raise ValueError('Duplicate input path.')
        files[name]=p.read_bytes().decode("utf-8")
    validate_files(files);return c,args,files


def check(config,output,compare_to=None):
    from app.receipt import preview
    from app.primitives import measure,gate
    from app.primitive_runtime import implementation_hash,SOURCES
    from app.probe_evidence import bundle
    c,args,files=load_config(config);p=preview(c['claim'],files,args,c.get('evaluation_intent'))
    m=measure('entity_overlap',files,args);m['implementation_hash']=implementation_hash()
    verdict=gate('entity_overlap',[m],[])
    r={'evaluation_intent':c.get('evaluation_intent'),'identity_diagnostics':p['identity_diagnostics'],'engine_version':'primitive-v4','execution_mode':'local_cli','claim':c['claim'],'original_claim':c['claim'],'input_hashes':p['input_hashes'],'verdict':{**verdict,'gate':verdict,'measurements':{'measurement-1':m['output']},'scope':'Local exact-ID measurement; no remote replay or human confirmation.'},'primitive_measurements':{'measurement-1':m},'primitive_replays':[],'primitive_sources':SOURCES,'probes':{},'runs':[],'replays':[],'model':'none; deterministic local check','setup_observation':{'mode':'saved_configuration','confirmed_arguments':None,'configured_arguments':args}}
    if compare_to is not None:
        from app.receipt_comparison import compare_receipts
        prior=Path(compare_to).resolve();previous=json.loads((prior/'result.json').read_text())
        prior_files={}
        for name in previous['input_hashes']:
            source=(prior/'inputs'/name).resolve()
            if not source.is_relative_to(prior/'inputs'):raise ValueError('Unsafe prior input path.')
            prior_files[name]=source.read_bytes().decode("utf-8")
        wrap=lambda result,inputs:{'input':{'evaluation_intent':result.get('evaluation_intent'),'claim':result['claim'],'files':[{'name':n,'content':v} for n,v in inputs.items()]},'result':result}
        r['revision_comparison']=compare_receipts(wrap(previous,prior_files),wrap(r,files))
        r['revision']={'parent_result_sha256':__import__('hashlib').sha256((prior/'result.json').read_bytes()).hexdigest(),'kind':'local_recheck'}
    bundle(r,files,output)
    return {'verdict':verdict['verdict'],'output':str(output),'shared_entities':m['output'].get('shared_entities'),'mode':'local; no provider upload or human confirmation'}


def _ladder_files(spec):
    names=[s.get('file') for s in spec.get('sources',[]) if isinstance(s,dict)]
    def walk(expr):
        if isinstance(expr,dict):
            q=expr.get('lookup')
            if isinstance(q,dict):
                names.append(q.get('file'));walk(q.get('on'))
    for level in spec.get('levels',[]):
        if isinstance(level,dict):
            walk(level.get('expression'))
            for e in (level.get('by_source') or {}).values():walk(e)
    names+=[c.get('file') for c in spec.get('citations',[]) if isinstance(c,dict)]
    if any(not isinstance(n,str) or not n for n in names):raise ValueError('Every source, lookup and citation needs a file name.')
    return list(dict.fromkeys(names))


def ladder(spec_path,sources,output,manifest=None,confirmed=()):
    """Measure one split against every level of a ladder spec. Local only: no model, network or Sandbox."""
    import hashlib
    from app.ladder import measure as measure_ladder,render
    spec_path=Path(spec_path).resolve()
    if spec_path.stat().st_size>200_000:raise ValueError('Ladder spec is too large.')
    spec=json.loads(spec_path.read_text())
    if not isinstance(spec,dict):raise ValueError('Ladder spec must be an object.')
    roots=[Path(x).resolve() for x in (sources if isinstance(sources,(list,tuple)) else [sources])];pins=None
    if manifest is not None:
        pins=json.loads(Path(manifest).read_text()).get('files')
        if not isinstance(pins,dict):raise ValueError('Manifest needs a files object.')
    files={};total=0
    for name in _ladder_files(spec):
        found=[(r/name).resolve() for r in roots if (r/name).resolve().is_relative_to(r) and (r/name).resolve().is_file()]
        if not found:raise ValueError(f'Input {name} is missing or outside the source directories.')
        p=found[0]
        data=p.read_bytes();total+=len(data)
        if total>16_000_000:raise ValueError('Ladder inputs exceed 16 MB total.')
        if pins is not None and name in pins:
            pin=pins[name]
            if not isinstance(pin,dict) or hashlib.sha256(data).hexdigest()!=pin.get('sha256'):
                raise ValueError(f'{name} does not match its pinned SHA-256; refusing to measure a different file.')
        files[name]=data.decode('utf-8')
    result=measure_ladder(spec,files,confirmed or ())
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    (output/'ladder.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    (output/'ladder.html').write_text(render(result))
    return {'finding':result['finding']['status'],'headline':result['headline'],'output':str(output),
            'mode':'local; no model, upload or Sandbox; '+('confirmed levels: '+', '.join(result['confirmed_levels']) if result['confirmed_levels'] else 'level meanings still need human confirmation')}


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('check',help='Recheck CSVs using saved columns; never makes a network call');p.add_argument('config',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--compare-to',type=Path,help='Prior extracted receipt directory; checks hashes before comparing')
    p=sub.add_parser('verify',help='Verify an extracted receipt locally with installed checker code; no credentials or network');p.add_argument('receipt',type=Path)
    p=sub.add_parser('ladder',help='Show which unit a split holds out at every declared level; local only');p.add_argument('spec',type=Path);p.add_argument('--sources',type=Path,action='append',required=True,help='Directory holding files named in the spec; repeat to search several');p.add_argument('--output',type=Path,required=True);p.add_argument('--manifest',type=Path,help='JSON with pinned SHA-256 per file; listed files that differ are refused');p.add_argument('--confirm',action='append',default=[],metavar='LEVEL',help='Record that you confirmed what LEVEL means; repeatable')
    args=parser.parse_args()
    try:
        if args.command=='verify':
            from app.bundle_verifier import verify_bundle
            from app.receipt_verification import assess_receipt
            from app.probes import validate_files
            root=args.receipt.resolve();result=verify_bundle(root)
            files={n:(root/'inputs'/n).read_bytes().decode('utf-8') for n in result['input_hashes']}
            validate_files(files)
            report=assess_receipt(result,files)
            print(json.dumps({'byte_integrity':True,**report,'mode':'local installed checker; no upload or bundled code execution'},indent=2))
            return 0 if report['matches'] else 1
        if args.command=='ladder':
            from app.ladder import LadderError
            try:r=ladder(args.spec,args.sources,args.output,args.manifest,args.confirm)
            except LadderError as e:parser.exit(2,str(e)+'\n')
            print(json.dumps(r,indent=2));return {'violation':1,'held_out':0,'held_out_pending_confirmation':0}.get(r['finding'],2)
        r=check(args.config,args.output,args.compare_to)
    except csv.Error:parser.exit(2,'Malformed CSV. Check quotation marks, headers and row lengths.\n')
    except (ValueError,KeyError,OSError,TypeError) as e:parser.exit(2,str(e)+'\n')
    print(json.dumps(r,indent=2));return 1 if r['verdict']=='violation' else 0 if r['verdict']=='clear_pending_confirmation' else 2
if __name__=='__main__':sys.exit(main())
