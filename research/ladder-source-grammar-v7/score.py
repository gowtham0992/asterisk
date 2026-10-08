"""Post-run scoring correction: invalid model output is a measured failure, not missing data.

The frozen runner's original summary is retained. No label or promotion threshold
changes; this separates completed inference from accepted preparation.
"""
import json
from pathlib import Path

def summarize(rows):
    result={}
    for version in ('v4','v7'):
        arm=[r for r in rows if r['version']==version]
        result[version]={key:sum(r.get(key,False) for r in arm) for key in
            ('first_valid','first_correct','final_correct','unsupported','wrong_reassurance','rejected_calls')}
        result[version].update(proposals=len(arm),tokens=sum(r['usage']['total_tokens'] for r in arm),
                              calls=sum(len(r['trace']) for r in arm))
    pairs={(r['id'],r['trial'],r['version']):r for r in rows}
    expected={(name,trial,v) for name in ('ucf101-exposed','qualified-lines','middle-characters','lookup-distractor','denied-specimen','actor-missing')
              for trial in (1,2) for v in ('v4','v7')}
    complete=(len(rows)==len(pairs)==24 and set(pairs)==expected and
              all(r['trace'] and all('reply' in t and 'error' not in t for t in r['trace']) for r in rows))
    regressions=[(r['id'],r['trial']) for r in rows if r['version']=='v7' and not r['final_correct'] and
                 pairs.get((r['id'],r['trial'],'v4'),{}).get('final_correct')]
    a,b=result['v4'],result['v7']
    result.update(inference_complete=complete,paired_regressions=regressions,
        promote=(complete and b['final_correct']==12 and b['unsupported']==b['wrong_reassurance']==0 and not regressions and
                 b['first_correct']>=a['first_correct']+2 and b['rejected_calls']<a['rejected_calls'] and
                 all(r['first_correct'] for r in rows if r['version']=='v7' and r['id']=='ucf101-exposed')))
    return result

if __name__=='__main__':
    out=Path(__file__).resolve().parents[2]/'.data/ladder-source-grammar-v7-20261007'
    rows=[json.loads(p.read_text()) for p in sorted(out.glob('v*-*-*.json'))]
    result=summarize(rows);result['scorer_correction']='The original runner conflated rejected model outputs with unfinished inference. Original summary retained; corrected completeness cannot change the failed UCF101 gate.'
    result['estimated_usd']=json.loads((out/'budget.json').read_text())['settled_usd']
    (out/'scored-summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
