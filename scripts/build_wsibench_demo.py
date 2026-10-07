"""Project pinned WSI-Bench report files to slide identifiers only; no clinical conversations."""
import argparse, hashlib, json
from pathlib import Path
from app import ladder
ROOT=Path(__file__).resolve().parents[1]

def build(data, output):
    pins=json.loads((ROOT/'examples/ladders/sources.json').read_text())['files']
    output=Path(output)
    if output.exists() and any(output.iterdir()): raise ValueError('Choose an empty output directory')
    files={}; provenance={}
    for role in ['train','test']:
        name=f'wsibench/Report_all_type_all_{role}_single.json'; raw=(Path(data)/name).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=pins[name]['sha256']: raise ValueError('Source hash differs from the pinned public file')
        rows=json.loads(raw)
        projected=[{'image':row['image']} for row in rows]
        if any(not isinstance(row['image'],str) for row in projected): raise ValueError('Every slide needs an identifier')
        files[role+'.json']=json.dumps(projected,ensure_ascii=False,separators=(',',':'))+'\n'
        provenance[role+'.json']={'source_url':pins[name]['url'],'source_sha256':pins[name]['sha256'],
            'rows':len(projected),'kept_columns':['image'],'excluded_columns':['id','conversations'],
            'projection_sha256':hashlib.sha256(files[role+'.json'].encode()).hexdigest()}
    files['README.md']=('WSI-Bench report-task identifier projection, not a synthetic example.\n'
        'train.json contains the original report-task training rows; test.json contains its evaluation rows.\n'
        'The image field identifies one whole-slide image file; use its basename for the slide identifier.\n'
        'GDC TCGA barcode: the first 12 characters of the basename (Project-TSS-Participant) identify the participant.\n'
        'The first 7 characters identify the project prefix and tissue source site.\n'
        'This check asks whether evaluation patients appear in training; it does not assert the authors promised patient-disjoint evaluation.\n'
        'Only image identifiers are retained. Clinical conversations and question IDs are excluded.\n'
        'GDC definition: https://docs.gdc.cancer.gov/Encyclopedia/pages/TCGA_Barcode/\n'
        'Source repository: https://github.com/XinhengLyu/WSI-LLaVA/tree/aeaf1b5dc556034d0c7832bd721d5b3f82213673\n'
        'Repository license: Apache-2.0. Derived-data licensing is not separately stated.\n')
    # Check the projection preserves the recorded baseline; do not supply its answer to the proposer.
    spec=json.loads((ROOT/'examples/ladders/wsibench-report.json').read_text())
    for source in spec['sources']: source['file']=source['partition']['value']+'.json'
    spec['citations']=[{'file':'README.md','start_line':2,'end_line':5}]
    measured=ladder.measure(spec,files)
    levels={l['name']:l for l in measured['levels']}
    assert levels['slide']['shared']==0 and levels['patient']['shared']==42
    assert levels['patient']['test_units']==207 and levels['patient']['affected_test_rows']==43
    output.mkdir(parents=True,exist_ok=True)
    for n,body in files.items(): (output/n).write_text(body)
    (output/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    return provenance

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    print(json.dumps(build(a.data,a.output),indent=2))
