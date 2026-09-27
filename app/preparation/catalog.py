"""Source metadata for the shared preparation editor; no inference."""
from pathlib import Path
from collections import Counter
from .review import executor

def sources(spec,files):
    result=[]
    tables=[]
    for name,text in files.items():
        fmt=Path(name).suffix.lower().lstrip('.')
        if fmt not in ('csv','json'):continue
        try:rows=executor.records(text,fmt,name)
        except (ValueError,TypeError,KeyError):continue
        tables.append({'file':name,'format':fmt,'columns':sorted({key for row,_ in rows for key in row})})
    for source in spec['sources']:
        records=executor.records(files[source['file']],source['format'],source['file'])
        columns=sorted({name for record,_ in records for name in record})
        values={};identity_counts={};repeated_examples={}
        for column in columns:
            counts=Counter(record.get(column) for record,_ in records
                           if isinstance(record.get(column),str) and record[column]
                           and len(record[column])<=4096 and '\0' not in record[column])
            identity_counts[column]={'text_records':sum(counts.values()),
                                     'distinct_values':len(counts),
                                     'repeated_values':sum(n>1 for n in counts.values()),
                                     'records_with_repeated_values':sum(n for n in counts.values() if n>1),
                                     'unusable_records':len(records)-sum(counts.values())}
            # Select in source order; display bounds never affect full-file counts.
            selected={}
            for value,count in counts.items():
                if count>1:selected[value]=[]
                if len(selected)==3:break
            for index,(record,reference) in enumerate(records,1):
                value=record.get(column)
                if isinstance(value,str) and value in selected and len(selected[value])<3:
                    selected[value].append({'record_number':index,'reference':reference})
            repeated_examples[column]=[{'value':value,'record_count':counts[value],'locations':locations}
                                       for value,locations in selected.items()]
            entries={record.get(column) for record,_ in records if isinstance(record.get(column),str)}
            if 0 < len(entries) <= 40 and all(isinstance(record.get(column),str) for record,_ in records):
                values[column]=sorted(entries)
        result.append({'file':source['file'],'columns':columns,'partition_values':values,'identity_counts':identity_counts,'repeated_examples':repeated_examples,
            'header_reference':({'file':source['file'],'line_start':1,'line_end':records[0][1]['line_start']-1} if source['format']=='csv' else None),
            'examples':[{'row':record,'reference':ref,'record_number':i} for i,(record,ref) in enumerate(records[:3],1)],
            'lookup_tables':tables,'record_count':len(records),'sample':source['sample'],'entity':source['entity'],'partition':source['partition']})
    return result
