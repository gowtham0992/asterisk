"""Structural citation cues, never a semantic evidence or verdict gate."""
import re

from .ladder import describe_expression


def review(spec, files, documentation=None):
    tables = {s['file'] for s in spec['sources']}
    requirements = []

    def expression(label, expr):
        if 'lookup' in expr:
            q = expr['lookup']
            if not isinstance(q,dict) or not all(isinstance(q.get(k),str) for k in ('file','key_column','value_column')) or not isinstance(q.get('on'),dict):
                raise ValueError('Cannot review a malformed lookup expression.')
            tables.add(q['file'])
            terms = [q['file'], q['key_column'], q['value_column']]
            if 'column' in q['on']: terms.append(q['on']['column'])
            requirements.append({'kind':'join','description':label+': '+describe_expression(expr), 'terms':list(dict.fromkeys(terms))})
        elif 'column' in expr:
            requirements.append({'kind':'identity','description':label+': '+describe_expression(expr), 'terms':[expr['column']]})
        else:
            requirements.append({'kind':'identity','description':label+': one source row', 'terms':[]})

    for source in spec['sources']:
        expression('Observation in '+source['file'], source['sample'])
        p=source['partition']
        requirements.append({'kind':'partition','description':'Partition in '+source['file']+': '+str(p),
                             'terms':([p['column']] if 'column' in p else [source['file']])})
    for level in spec['levels']:
        if level['kind']=='observation': continue
        expression(level['name'],level['expression'])
        for name,expr in level.get('by_source',{}).items():expression(level['name']+' in '+name,expr)
    docs = sorted(set(documentation) if documentation is not None else
                  {n for n in files if n not in tables and n.lower().endswith(('.md','.txt','.rst'))})
    omitted = max(0,len(docs)-20) if documentation is None else 0
    if omitted:
        cited_names={c['file'] for c in spec['citations']}
        docs=sorted(docs,key=lambda n:(n not in cited_names,n))[:20]
    if len(docs)>20 or any(n not in files for n in docs):
        raise ValueError('Choose at most 20 supplied documentation files.')
    cited=[]
    for c in spec['citations']:
        if c['file'] in docs:
            cited.extend(files[c['file']].splitlines()[c['start_line']-1:c['end_line']])
    def contains(text,term):
        return bool(re.search(r'(?<![\w])'+re.escape(term)+r'(?![\w])',text,re.I))
    quoted='\n'.join(cited)
    for r in requirements:
        r['missing_terms']=[t for t in r['terms'] if not contains(quoted,t)]
        r['status']='field_references_missing' if r['missing_terms'] else 'meaning_not_verified'
        candidates=[]
        for name in docs:
            for i,line in enumerate(files[name][:60_000].splitlines(),1):
                matches=sum(contains(line,t) for t in r['terms'])
                if matches:
                    candidates.append((matches,name,i,line))
        candidates.sort(key=lambda x:(-x[0],x[1],x[2]))
        r['candidates']=[{'file':n,'line':i,'text':line[:500],'truncated':len(line)>500} for _,n,i,line in candidates[:5]]
    return {'schema':'asterisk-citation-review/1','requirements':requirements,'other_document_candidates_omitted':omitted,
            'documents':[{'file':n,'lines':len(files[n].splitlines()),'candidate_search_truncated':len(files[n])>60_000} for n in docs],
            'scope':'Field references are structural cues only. Matching words, including denials, do not verify identity meaning or a join. Candidate search is limited to the first 60,000 characters per document; read the full documentation. This review does not alter the measurement or confirm anything.'}
