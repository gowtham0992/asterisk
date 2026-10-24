"""Build only the static product introduction; never publish or copy application state."""
import argparse
import html
import json
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


def public_url(value, allow_local=False):
    url = urlsplit(value)
    local = allow_local and url.scheme == 'http' and url.hostname in ('localhost', '127.0.0.1', '::1')
    if (url.scheme != 'https' and not local) or not url.hostname or url.username or url.password:
        raise ValueError('Use an absolute HTTPS URL without credentials (or explicitly allow localhost for preview).')
    if any(c.isspace() or ord(c) < 32 for c in value) or '\\' in value:
        raise ValueError('URL contains unsupported characters.')
    return value


def build(output, workspace_url, source_url=None, allow_local=False):
    workspace_url = public_url(workspace_url, allow_local)
    if source_url:
        source_url = public_url(source_url)
    # Only a fresh directory can become a Pages artifact. Never inherit stale,
    # unrelated files from a previous build or a caller's source directory.
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError('Output directory must be empty; choose a fresh build directory.')
    measurement = json.loads((ROOT/'static/ladders/wsibench-report.json').read_text())
    levels = {level['name']: level for level in measurement['levels']}
    values = {'WORKSPACE_URL': workspace_url, 'SLIDES': levels['slide']['shared'],
              'PATIENTS': levels['patient']['shared'], 'AFFECTED': levels['patient']['affected_test_rows'],
              'ROWS': levels['patient']['test_rows']}
    witness = levels['patient']['witnesses'][0]
    values.update({'WITNESS_UNIT': witness['unit'], 'WITNESS_TRAIN': witness['train']['sample'],
                   'WITNESS_TEST': witness['test']['sample'],
                   'WITNESS_TRAIN_REF': ', '.join(ref['file']+' '+ref['at'] for ref in witness['train']['unit_source']),
                   'WITNESS_TEST_REF': ', '.join(ref['file']+' '+ref['at'] for ref in witness['test']['unit_source']),
                   'PATIENT_QUOTE': (ROOT/'examples/ladders/docs/tcga-barcode.md').read_text().splitlines()[1]})
    page = (ROOT/'public_site/index.html').read_text()
    for key, value in values.items():
        page = page.replace('{{'+key+'}}', html.escape(str(value), quote=True))
    source_link = '<a href="'+html.escape(source_url, quote=True)+'">Source code</a>' if source_url else ''
    page = page.replace('{{SOURCE_LINK}}', source_link)
    if '{{' in page:
        raise ValueError('Unfilled template field.')
    output.mkdir(parents=True, exist_ok=True)
    (output/'index.html').write_text(page)
    (output/'site.css').write_bytes((ROOT/'public_site/site.css').read_bytes())
    (output/'evidence.json').write_text(json.dumps(measurement, indent=2)+'\n')
    (output/'.nojekyll').touch()
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--workspace-url', required=True)
    parser.add_argument('--source-url')
    parser.add_argument('--allow-localhost', action='store_true')
    args = parser.parse_args()
    try:
        print(build(args.output, args.workspace_url, args.source_url, args.allow_localhost))
    except ValueError as error:
        parser.error(str(error))
