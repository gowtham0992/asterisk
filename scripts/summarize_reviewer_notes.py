"""Summarize locally recorded reviews without converting self-reports into validation."""
import argparse,json,statistics
from pathlib import Path


def summarize(paths):
    rows=[];excluded=[]
    for path in paths:
        row=json.loads(path.read_text())
        required=('reviewer_id','artifact_label','actor_type','supported','active_seconds','wall_seconds','committed_at')
        if any(k not in row for k in required):raise ValueError(f'{path.name}: incomplete review')
        if row['actor_type']!='human' or row.get('consent') is not True or row.get('labels_unseen') is not True:
            excluded.append({'file':path.name,'reason':'Not a consenting, label-blind human self-report'});continue
        if row['supported'] not in ('yes','no','uncertain'):raise ValueError('Invalid support rating')
        for key in ('active_seconds','wall_seconds'):
            if type(row[key]) not in (int,float) or row[key]<0:raise ValueError('Invalid timing')
        if row['active_seconds']>row['wall_seconds']+1:raise ValueError('Active time exceeds wall time')
        rows.append(row)
    groups={}
    for label in sorted({r['artifact_label'] for r in rows}):
        subset=[r for r in rows if r['artifact_label']==label]
        groups[label]={'reviews':len(subset),'median_active_seconds':statistics.median(r['active_seconds'] for r in subset),
                       'supported':sum(r['supported']=='yes' for r in subset),'unsupported':sum(r['supported']=='no' for r in subset),
                       'uncertain':sum(r['supported']=='uncertain' for r in subset)}
    return {'status':'unmeasured' if not rows else 'human_self_reports_recorded','human_review_count':len(rows),
            'distinct_reviewer_aliases':len({r['reviewer_id'] for r in rows}),'groups':groups,'excluded':excluded,
            'limitation':'Aliases and independence are not authenticated. No automatic pass, superiority, statistical significance or comprehension score is inferred. Inspect verbatim answers and the preregistered assignment.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('directory',type=Path);args=parser.parse_args()
    print(json.dumps(summarize(sorted(args.directory.glob('*.json'))),indent=2))
