"""One provider operation. Credentials arrive over stdin, never command arguments."""
import json
import sys


def main():
    request=json.load(sys.stdin);p=request['payload']
    if request['action']=='complete':
        from openai import OpenAI
        with OpenAI(base_url='https://api.tokenfactory.nebius.com/v1/',api_key=p['key'],max_retries=0) as client:
            response=client.chat.completions.create(model=p['model'],messages=p['messages'],max_tokens=p['maximum'],temperature=0,timeout=p['timeout'])
            result=response.model_dump(mode='json')
    else:raise ValueError('Unsupported worker action')
    sys.stdout.write(json.dumps(result,allow_nan=False))


if __name__=='__main__':main()
