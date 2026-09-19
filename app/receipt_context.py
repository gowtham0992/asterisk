"""Display context only. Never grants a verdict or confirms scientific meaning."""
import re,hashlib
from .identity_diagnostics import identity_formats


def review_context(result, files):
    records=[r for r in result.get('primitive_measurements',{}).values() if r.get('primitive')=='entity_overlap']
    args=[r.get('arguments') or {} for r in records]
    terms={a[k] for a in args for k in ('sample_column','mapping_sample_column','entity_column') if a.get(k)}
    documentation=[]
    for name,text in sorted(files.items()):
        if not name.lower().endswith(('.md','.txt')):continue
        lines=text.splitlines();seen=set()
        for i,line in enumerate(lines):
            if not any(re.search(r'(?<!\w)'+re.escape(t)+r'(?!\w)',line) for t in terms):continue
            lo=max(0,i-1);hi=min(len(lines),i+2)
            if (lo,hi) in seen:continue
            seen.add((lo,hi))
            documentation.append({'file':name,'start_line':lo+1,'end_line':hi,'quote':'\n'.join(lines[lo:hi]),'basis':'Column-name mention; meaning requires review'})
    citations=[]
    for c in (result.get('verdict') or {}).get('citations',[]):
        header=c.get('file','').lower().endswith('.csv') and c.get('start_line')==1 and c.get('end_line')==1
        citations.append({**c,'display_scope':'Column names only; this passage does not define identity meaning.' if header else 'Original cited passage; exact text alone does not verify its meaning.'})
    first=args[0] if args else {}
    diagnostic={'available':False,'message':'Identity-format diagnostic unavailable.'}
    if len(records)==1 and records[0].get('input_hashes')=={n:hashlib.sha256(t.encode()).hexdigest() for n,t in files.items()}:
        try:diagnostic=identity_formats(files,first)
        except (KeyError,ValueError,TypeError):pass
    return {'identity_diagnostics':diagnostic,'blocked':any((r.get('output') or {}).get('available') is not True for r in records),
            'documentation':documentation[:12],'documentation_total':len(documentation),'citations':citations,
            'partition_labels':{'train':first.get('train_values',[]),'test':first.get('test_values',[])}}
