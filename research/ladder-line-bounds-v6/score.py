"""Offline semantic scoring, preserving original run records and their provisional scores."""
import json
from pathlib import Path
from app import ladder,ladder_proposal as lp
OUT=Path(__file__).resolve().parents[2]/'.data/line-bounds-v6-20261007'
def partitions(spec,files):
 return {r['sample']:r['partition'] for r in ladder.population(spec,files)['lineage']}
def correct(spec,reference,files):
 return (lp.semantic_match(spec,reference,files)['same_grouping'] and
         partitions(spec,files)==partitions(reference,files) and
         ladder.measure(spec,files)['finding']['status']==ladder.measure(reference,files)['finding']['status'])
def score():
 packet=json.loads((OUT/'packet.json').read_text());rows=[]
 for item in packet['requests']:
  r=json.loads((OUT/f"{item['version']}-{item['id']}-{item['trial']}.json").read_text());c=next(c for c in packet['cases'] if c['id']==r['id']);g=r.get('proposal',{})
  r['provisional_correct']=r['correct'];r['correct']=g.get('status')=='abstain' if c['reference'] is None else g.get('status')=='ladder' and correct(g['spec'],c['reference'],c['files'])
  r['false_reassurance']=bool(c['reference'] and g.get('status')=='ladder' and not r['correct'] and ladder.measure(g['spec'],c['files'])['finding']['status']=='held_out_pending_confirmation');rows.append(r)
 summary={}
 for v in ['v4','v6']:
  rs=[r for r in rows if r['version']==v]
  summary[v]={'correct':sum(r['correct'] for r in rs),'unsupported':sum(r['unsupported'] for r in rs),'false_reassurance':sum(r['false_reassurance'] for r in rs),'invalid_first':sum(bool(r.get('attempts') and r['attempts'][0]['error']) or 'error' in r for r in rs),'citation_errors':sum('Citation beyond file' in (a['error'] or '') for r in rs for a in r.get('attempts',[])),'calls':sum(r['usage']['calls'] for r in rs),'tokens':sum(r['usage']['total_tokens'] for r in rs)}
 a,b=summary['v4'],summary['v6'];supported={c['id'] for c in packet['cases'] if c['reference']}
 summary['promote']=b['unsupported']==b['false_reassurance']==0 and all(r['correct'] for r in rows if r['version']=='v6' and r['id'] in supported) and b['correct']>=a['correct']+2 and b['invalid_first']<a['invalid_first'] and b['citation_errors']<a['citation_errors']
 summary['correction']='Provisional run mistakenly compared whole population objects (including citation ranges and spec hashes), not sample-to-partition mappings. Offline scores compare the mappings. Cases, references, model requests and promotion criteria unchanged. All original records retained.'
 (OUT/'rescored.json').write_text(json.dumps({'summary':summary,'rows':rows},indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':score()
