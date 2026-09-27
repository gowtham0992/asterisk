"""The page's guided builder (static/ladder-view.mjs) must emit specs the Python engine accepts and measures."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from app.ladder import measure

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = """
import {buildSpec} from '%s';
const args = JSON.parse(process.argv[2]);
console.log(JSON.stringify(buildSpec(args)));
"""


@pytest.mark.skipif(shutil.which('node') is None, reason='node is not installed')
def test_a_builder_spec_is_measured_by_the_engine(tmp_path):
    script = tmp_path / 'build.mjs'
    script.write_text(SCRIPT % (ROOT / 'static' / 'ladder-view.mjs').as_uri())
    args = {'claim': 'No test subject appears in the training data.', 'unitName': 'Subject',
            'sources': [{'file': 'split.csv', 'sample': {'column': 'record'}, 'partition': {'column': 'split', 'map': {'train': 'train', 'test': 'test'}}}],
            'unit': {'column': 'record', 'prefix': 5}, 'citation': {'file': 'ltst.md', 'start': 1, 'end': 1}}
    out = subprocess.run(['node', str(script), json.dumps(args)], capture_output=True, text=True, timeout=30, check=True).stdout
    spec = json.loads(out)
    files = {'split.csv': 'record,split\ns20011,train\ns20012,test\ns20021,train\ns30031,test\n',
             'ltst.md': 'Records obtained from the same subject have names that differ in the last digit only.\n'}
    result = measure(spec, files)
    assert result['finding']['status'] == 'violation' and result['finding']['level'] == 'subject'
    assert result['levels'][1]['shared'] == 1
