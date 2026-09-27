"""One provider operation. Credentials arrive over stdin, never command arguments."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]


def main():
    request=json.load(sys.stdin);p=request['payload']
    if request['action']=='complete':
        from openai import OpenAI
        with OpenAI(base_url='https://api.tokenfactory.nebius.com/v1/',api_key=p['key'],max_retries=0) as client:
            response=client.chat.completions.create(model=p['model'],messages=p['messages'],max_tokens=p['maximum'],temperature=0,timeout=p['timeout'])
            result=response.model_dump(mode='json')
    elif request['action']=='replay':
        sys.path.insert(0,str(ROOT))
        from app.probes import ProbeSandbox
        source=(ROOT/'evaluation/extraction-v1/executor.py').read_text()
        code=source+'\nfrom pathlib import Path\nfiles={p.name:p.read_bytes().decode("utf-8") for p in Path(".").iterdir() if p.is_file()}\nspec=json.loads('+repr(json.dumps(p['spec']))+')\nr=extract(spec,files)\nprint(json.dumps({"extraction_hash":sha(canonical(r))}))\n'
        result=ProbeSandbox(p['key'],p['project'],p['image'])(code,p['files'])
    else:raise ValueError('Unsupported worker action')
    sys.stdout.write(json.dumps(result,allow_nan=False))


if __name__=='__main__':main()
