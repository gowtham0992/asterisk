"""Rebuild static/ladders/ from pinned public metadata. Local only: no model, upload or Sandbox.

Usage:
  .venv/bin/python scripts/build_public_ladders.py --data /path/to/downloaded/metadata

The data directory must hold the files listed in examples/ladders/sources.json, at
the listed relative paths, byte-identical to their pinned SHA-256. Third-party
metadata is never copied into the repository; only aggregate ladder results with
source hashes are written.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.ladder import measure  # noqa: E402
from asterisk import _ladder_files  # noqa: E402

GALLERY = [
    ('wsibench-report', 'WSI-Bench · report task',
     'A computational-pathology benchmark built from TCGA slides. No slide appears in both splits.',
     'https://github.com/XinhengLyu/WSI-LLaVA'),
    ('wsibench-cross-task', 'WSI-Bench · across tasks',
     'Report-task test slides compared with the training files of four other WSI-Bench tasks.',
     'https://github.com/XinhengLyu/WSI-LLaVA'),
    ('ptbxl', 'PTB-XL · recommended split',
     'A 12-lead ECG benchmark whose documentation promises patient-disjoint folds.',
     'https://physionet.org/content/ptb-xl/1.0.3/'),
    ('esc50-fold2', 'ESC-50 · fold 2 held out',
     'An environmental-sound benchmark whose README promises that fragments of one source recording stay in one fold.',
     'https://github.com/karolpiczak/ESC-50'),
    ('esc50-fold1', 'ESC-50 · fold 1 held out',
     'The same benchmark with a different held-out fold — a control where the promise holds.',
     'https://github.com/karolpiczak/ESC-50'),
    ('urbansound8k-fold1', 'UrbanSound8K · fold 1 held out',
     'An urban-sound benchmark whose page warns against reshuffling related samples across folds.',
     'https://urbansounddataset.weebly.com/urbansound8k.html'),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--out', type=Path, default=ROOT / 'static' / 'ladders')
    args = parser.parse_args()
    examples = ROOT / 'examples' / 'ladders'
    pins = json.loads((examples / 'sources.json').read_text())['files']
    args.out.mkdir(parents=True, exist_ok=True)
    index = []
    for key, title, summary, url in GALLERY:
        spec = json.loads((examples / f'{key}.json').read_text())
        files = {}
        for name in _ladder_files(spec):
            path = (examples / name) if (examples / name).is_file() else (args.data / name)
            data = path.read_bytes()
            if name in pins and hashlib.sha256(data).hexdigest() != pins[name]['sha256']:
                raise SystemExit(f'{name} does not match its pinned SHA-256; refusing to publish a different result.')
            files[name] = data.decode('utf-8')
        result = measure(spec, files)
        result['source'] = {'title': title, 'summary': summary, 'url': url,
                            'licences': sorted({pins[n]['licence'] for n in files if n in pins}),
                            'spec': f'examples/ladders/{key}.json'}
        (args.out / f'{key}.json').write_text(json.dumps(result, indent=1, ensure_ascii=False) + '\n')
        index.append({'key': key, 'title': title, 'summary': summary, 'headline': result['headline'],
                      'finding': result['finding']['status'], 'claim_level': result['finding']['level']})
        print(f'{key:22s} {result["finding"]["status"]:32s} {result["headline"]}')
    (args.out / 'index.json').write_text(json.dumps({'ladders': index}, indent=1, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
