"""Deterministic repair proposals. Proposed changes never certify scientific validity."""
import csv,io,json,hashlib,zipfile
from .audit import table,execute
from .receipt_comparison import snapshot

POLICIES=('evaluation_to_training','training_to_evaluation')
SCOPE='Candidate reassignment only. Review scientific suitability and partition sizes; retrain and reevaluate after changing a split. No accuracy improvement is claimed.'

def csv_text(fields,rows,lineterminator="\n"):
    out=io.StringIO(newline='');w=csv.DictWriter(out,fieldnames=fields,lineterminator=lineterminator);w.writeheader();w.writerows(rows);return out.getvalue()

def repair_rows(a):
    s=snapshot(a);files={f['name']:f['content'] for f in a['input']['files']};args=s['args']
    _,rows=table(files[args['split_file']]);_,mapping=table(files[args['mapping_file']])
    mapping_rows={}
    for i,r in enumerate(mapping,2):
        if r[args['mapping_sample_column']] and r[args['entity_column']]:mapping_rows.setdefault(r[args['mapping_sample_column']],i)
    affected=[];missing=[];selected=s['groups']['train']|s['groups']['test']
    for i,r in enumerate(rows,2):
        sid=r[args['sample_column']];part=r[args['partition_column']]
        if sid not in selected:continue
        role='training' if sid in s['groups']['train'] else 'evaluation'
        item={'sample':sid,'partition':part,'role':role,'entity':s['ids'].get(sid,''),'split_file':args['split_file'],'split_row':i,'mapping_file':args['mapping_file'],'mapping_row':mapping_rows.get(sid,'')}
        if sid in s['missing']:missing.append({**item,'reason':'No usable identity mapping'})
        elif s['ids'][sid] in s['shared']:affected.append(item)
    return s,affected,missing

def inventory_zip(a):
    s,affected,missing=repair_rows(a);out=io.BytesIO()
    fields=['sample','partition','role','entity','split_file','split_row','mapping_file','mapping_row']
    # JSON preserves exact IDs. CSVs are machine-readable; import identifiers as text in spreadsheets.
    contents={'affected.csv':csv_text(fields,affected),'unmapped.csv':csv_text(fields+['reason'],missing),
              'rows.json':json.dumps({'affected':affected,'unmapped':missing},indent=2),
              'README.txt':'Open rows.json first for exact identifiers without spreadsheet formula interpretation. All selected affected rows, not capped witness examples. Rows include the header as logical row 1. CSV values are exact; import identifiers as text, not spreadsheet formulas. JSON preserves exact values.\n'+SCOPE,
              'provenance.json':json.dumps({'parent_id':a.get('id'),'input_hashes':s['hashes'],'arguments':s['args'],'scope':SCOPE},indent=2)}
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for n,t in contents.items():z.writestr(n,t)
        z.writestr('manifest.json',json.dumps({n:hashlib.sha256(t.encode()).hexdigest() for n,t in contents.items()},indent=2))
    return out.getvalue()

def propose(a,policy,target_label):
    if policy not in POLICIES:raise ValueError('Select a supported reassignment policy.')
    s,affected,missing=repair_rows(a);args=s['args'];files={f['name']:f['content'] for f in a['input']['files']}
    if missing:raise ValueError('Complete identity mappings before proposing a group repair. Download the unmapped-row list.')
    if not s['shared']:raise ValueError('There is no recorded overlap to repair.')
    destination='train_values' if policy=='evaluation_to_training' else 'test_values'
    if target_label not in args[destination]:raise ValueError('Choose an existing label in the destination partition.')
    source=s['groups']['test'] if policy=='evaluation_to_training' else s['groups']['train']
    fields,rows=table(files[args['split_file']]);moves=[]
    for i,row in enumerate(rows,2):
        sid=row[args['sample_column']]
        if sid in source and s['ids'][sid] in s['shared']:
            moves.append({'sample':sid,'entity':s['ids'][sid],'split_row':i,'before':row[args['partition_column']],'after':target_label})
            row[args['partition_column']]=target_label
    if any(not any(r[args['partition_column']] in args[k] for r in rows) for k in ('train_values','test_values')):
        raise ValueError('The proposed split must retain at least one training and one evaluation row. Choose another policy.')
    original=files[args['split_file']];reader=io.StringIO(original,newline='');next(csv.reader(reader));header=original[:reader.tell()]
    ending='\r\n' if header.endswith('\r\n') else '\r' if header.endswith('\r') else '\n'
    revised={**files,args['split_file']:csv_text(fields,rows,ending)}
    formatting={'line_ending':{'\r\n':'CRLF','\r':'CR','\n':'LF'}[ending],'quoting':'minimal','notice':'Record line endings follow the original header. CSV quoting is normalized; values are preserved. A text diff can show formatting changes beyond the partition moves.'}
    after=execute(args,revised) # Fails if either selected partition becomes empty.
    before=execute(args,files)
    if after['shared_entities']!=0:raise ValueError('The proposed reassignment did not remove recorded overlap.')
    summary=lambda o:{k:o[k] for k in ('shared_entities','affected_test_rows','train_rows','test_rows','ignored_rows')}
    before_test=s['groups']['test']
    after_test={r[args['sample_column']] for r in rows if r[args['partition_column']] in args['test_values']}
    population={'evaluation_rows_retained':len(before_test & after_test),
                'evaluation_rows_removed':len(before_test-after_test),
                'evaluation_rows_added':len(after_test-before_test),
                'evaluation_identities_before':len({s['ids'][sid] for sid in before_test}),
                'evaluation_identities_after':len({s['ids'][sid] for sid in after_test})}
    consequence=(f"Evaluation changes from {len(before_test)} to {len(after_test)} rows: "
                 f"{population['evaluation_rows_removed']} removed and {population['evaluation_rows_added']} added. "
                 f"Distinct evaluation identities change from {population['evaluation_identities_before']} to {population['evaluation_identities_after']}. "
                 "This changes who is evaluated and the training data. Removing recorded overlap does not establish a better or representative experiment. Review whether the revised population still answers the original claim; retrain and evaluate again.")
    payload={'evaluation_population':population,'scientific_consequence':consequence,'evaluation_intent':a['input'].get('evaluation_intent'),'original_claim':a['input']['claim'],'parent_id':a.get('id'),'input_hashes':s['hashes'],'arguments':args,'policy':policy,'target_label':target_label,'moves':moves,'before':summary(before),'after':summary(after),'csv_format':formatting,'scope':SCOPE+' '+formatting['notice']}
    payload['proposal_hash']=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return payload,revised
