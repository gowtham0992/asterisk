import os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'.data/probe-pilot'
def credentials():
    values={}
    for line in (ROOT/'.env').read_text().splitlines() if (ROOT/'.env').exists() else []:
        if '=' in line and not line.lstrip().startswith('#'):
            key,value=line.split('=',1);values[key.strip()]=value.strip().strip('"').strip("'")
    values.update({k:v for k,v in os.environ.items() if k.startswith('NEBIUS_')})
    return values['NEBIUS_API_KEY'],values.get('NEBIUS_PROJECT_ID') or values['NEBIUS_AI_PROJECT']
