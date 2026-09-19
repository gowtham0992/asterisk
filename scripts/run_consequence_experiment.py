"""Reproduce the predeclared local experiment; no network, inference or training on host-supplied code."""
import csv,hashlib,io,json,math,random,statistics,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from asterisk import export_split,load_config
from app.primitives import measure
from app.repair import propose

def solve(a,b):
    a=[list(row)+[v] for row,v in zip(a,b)];n=len(b)
    for i in range(n):
        j=max(range(i,n),key=lambda j:abs(a[j][i]));a[i],a[j]=a[j],a[i]
        if abs(a[i][i])<1e-12:raise ValueError('Singular normal equations')
        scale=a[i][i];a[i]=[x/scale for x in a[i]]
        for j in range(n):
            if i==j:continue
            scale=a[j][i];a[j]=[x-scale*y for x,y in zip(a[j],a[i])]
    return [row[-1] for row in a]

def ridge(x,y,train,test):
    p=len(x[0]);mu=[statistics.fmean(x[i][j] for i in train) for j in range(p)]
    sd=[math.sqrt(statistics.fmean((x[i][j]-mu[j])**2 for i in train)) or 1 for j in range(p)]
    ym=statistics.fmean(y[i] for i in train);a=[[float(j==k) for k in range(p)] for j in range(p)];b=[0.]*p
    for i in train:
        z=[(x[i][j]-mu[j])/sd[j] for j in range(p)];target=y[i]-ym
        for j in range(p):
            b[j]+=z[j]*target
            for k in range(p):a[j][k]+=z[j]*z[k]
    beta=solve(a,b);pred=[ym+sum(beta[j]*(x[i][j]-mu[j])/sd[j] for j in range(p)) for i in test]
    return {'mae':statistics.fmean(abs(v-y[i]) for v,i in zip(pred,test)), 'coefficients':beta,'training_mean':mu,'training_scale':sd,'intercept':ym}

def size_matched_training(subjects,parts,held,moved_count,seed):
    train=[i for i,p in enumerate(parts) if p=='train']
    candidates=[i for i in train if subjects[i] not in held]
    dropped=set(random.Random(1000+seed).sample(candidates,moved_count))
    return [i for i in train if i not in dropped],sorted(dropped)


def run(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    protocol=(ROOT/'docs/experiments/score-protocol.md').read_bytes();(out/'protocol.md').write_bytes(protocol)
    amendment=(ROOT/'docs/experiments/size-control-protocol.md').read_bytes();(out/'size-control-protocol.md').write_bytes(amendment)
    source=ROOT/'.data/probe-pilot/resources/parkinsons.zip'
    with zipfile.ZipFile(source) as z:raw=z.read('parkinsons_updrs.data')
    rows=list(csv.DictReader(io.StringIO(raw.decode())));excluded={'subject#','age','sex','test_time','motor_UPDRS','total_UPDRS'}
    features=[k for k in rows[0] if k not in excluded];assert len(features)==16
    x=[[float(r[k]) for k in features] for r in rows];y=[float(r['motor_UPDRS']) for r in rows];subjects=[r['subject#'] for r in rows];trials=[]
    for seed in range(42,47):
        rng=random.Random(seed);people=sorted(set(subjects));rng.shuffle(people);held=set(people[:12]);planted=set(people[:6]);parts=['test' if s in held else 'train' for s in subjects]
        for person in sorted(planted):
            ids=[i for i,s in enumerate(subjects) if s==person];rng.shuffle(ids)
            for i in ids[:max(1,len(ids)//5)]:parts[i]='train'
        cfg=export_split(out/str(seed)/'overlapping',sample_ids=[str(i) for i in range(len(rows))],entity_ids=subjects,partitions=parts,claim='Evaluation participants must be absent from training.',identity_definition='entity is subject#, the participant ID from UCI Parkinsons Telemonitoring.')
        c,args,files=load_config(cfg);measurement=measure('entity_overlap',files,args)
        investigation={'id':str(seed),'input':{'claim':c['claim'],'files':[{'name':n,'content':v} for n,v in files.items()]},'result':{'primitive_measurements':{'m':measurement}}}
        proposal,repaired=propose(investigation,'training_to_evaluation','test');after=measure('entity_overlap',repaired,args)
        d=out/str(seed)/'repaired';d.mkdir()
        for n,t in repaired.items():(d/n).write_text(t)
        (d/'asterisk.json').write_text(json.dumps(c,indent=2));(d/'proposal.json').write_text(json.dumps(proposal,indent=2))
        repaired_parts=[r['partition'] for r in csv.DictReader(io.StringIO(repaired['splits.csv']))];test=[i for i,p in enumerate(parts) if p=='test']
        contaminated=ridge(x,y,[i for i,p in enumerate(parts) if p=='train'],test);clean=ridge(x,y,[i for i,p in enumerate(repaired_parts) if p=='train'],test)
        control_train,dropped=size_matched_training(subjects,parts,held,len(proposal['moves']),seed)
        assert len(control_train)==repaired_parts.count('train') and not set(test)&set(control_train)
        control=ridge(x,y,control_train,test)
        dropped_set=set(dropped);control_parts=['excluded_control' if i in dropped_set else part for i,part in enumerate(parts)]
        export_split(out/str(seed)/'size-matched-control',sample_ids=[str(i) for i in range(len(rows))],entity_ids=subjects,partitions=control_parts,claim=c['claim'],identity_definition=files['identity.md'].rstrip('\n'))
        (out/str(seed)/'size-matched-control/removed-rows.json').write_text(json.dumps({'seed':1000+seed,'removed_rows':dropped,'selection':'Only participants outside the original evaluation group'},indent=2))
        trials.append({'control':control,'control_mae_difference':control['mae']-contaminated['mae'],'control_training_rows':len(control_train),'seed':seed,'shared_before':measurement['output']['shared_entities'],'shared_after':after['output']['shared_entities'],'moved_rows':len(proposal['moves']),'common_evaluation_rows':len(test),'training_before':parts.count('train'),'training_after':repaired_parts.count('train'),'overlapping':contaminated,'repaired':clean,'mae_difference':clean['mae']-contaminated['mae']})
    report={'control_protocol_sha256':hashlib.sha256(amendment).hexdigest(),'control_protocol':amendment.decode(),'control_status':'Post-review extension; Fable results were already known.','mean_control_mae_difference':statistics.fmean(t['control_mae_difference'] for t in trials),'relative_repair_mae_percent':100*statistics.fmean(t['mae_difference'] for t in trials)/statistics.fmean(t['overlapping']['mae'] for t in trials),'protocol_sha256':hashlib.sha256(protocol).hexdigest(),'source_archive_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'data_sha256':hashlib.sha256(raw).hexdigest(),'source':'https://archive.ics.uci.edu/dataset/189/parkinsons+telemonitoring','license':'CC BY 4.0','attribution':'Tsanas, A. & Little, M. (2009). Parkinsons Telemonitoring. UCI Machine Learning Repository. DOI:10.24432/C5ZS3N','rows':len(rows),'participants':len(set(subjects)),'features':features,'trials':trials,'mean_mae_difference':statistics.fmean(t['mae_difference'] for t in trials),'scope':protocol.decode()}
    (out/'results.json').write_text(json.dumps(report,indent=2));(out/'manifest.json').write_text(json.dumps({str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob('*')) if p.is_file()},indent=2))
    print(json.dumps({'rows':len(rows),'participants':len(set(subjects)),'trials':[{k:v for k,v in t.items() if k not in ('overlapping','repaired','control')}|{'mae_overlapping':t['overlapping']['mae'],'mae_repaired':t['repaired']['mae']} for t in trials],'mean_mae_difference':report['mean_mae_difference'],'mean_control_mae_difference':report['mean_control_mae_difference'],'relative_repair_mae_percent':report['relative_repair_mae_percent']},indent=2))
if __name__=='__main__':run(sys.argv[1])
