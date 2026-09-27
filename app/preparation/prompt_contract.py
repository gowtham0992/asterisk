"""Executable language examples for the application; frozen study prompts stay intact."""
import json

EXAMPLES = [
    {
        'files': {
            'assignments.csv': 'capture,role\nc1,fit\nc2,score\nc3,unused\n',
            'units.csv': 'capture,unit\nc1,u7\nc2,u7\nc3,u9\n',
            'guide.txt': 'capture identifies an observation. unit identifies the physical unit.\n'
                         'assignments.csv assigns fit to training, score to evaluation, unused to exclusion.\n'
                         'units.csv maps capture to unit; its rows are identity links, not extra observations.\n',
        },
        'spec': {
            'status': 'extract',
            'sources': [{
                'file': 'assignments.csv', 'format': 'csv',
                'sample': {'column': 'capture'},
                'entity': {'lookup': {'file': 'units.csv', 'format': 'csv',
                           'key_column': 'capture', 'value_column': 'unit',
                           'on': {'column': 'capture'}}},
                'partition': {'column': 'role', 'map': {
                    'fit': 'train', 'score': 'test', 'unused': 'excluded'}},
            }],
            'citations': [{'file': 'guide.txt', 'start_line': 1, 'end_line': 3}],
        },
    },
    {
        'files': {
            'reference.json': '[{"path":"images/Q701-a.png"}]',
            'evaluation.json': '[{"path":"images/Q701-b.png"}]',
            'guide.txt': 'Each full path identifies one observation.\n'
                         'The first four characters of its filename identify the physical unit.\n'
                         'reference.json contains training observations; evaluation.json contains evaluation observations.\n',
        },
        'spec': {
            'status': 'extract',
            'sources': [{
                'file': name, 'format': 'json', 'sample': {'column': 'path'},
                'entity': {'column': 'path', 'basename': True, 'prefix': 4},
                'partition': {'value': side},
            } for name, side in [('reference.json', 'train'), ('evaluation.json', 'test')]],
            'citations': [{'file': 'guide.txt', 'start_line': 1, 'end_line': 3}],
        },
    },
]


def application_prompt(base):
    return base + '''
Application extraction contract:
- First distinguish observation tables from identity lookup tables. sources contains
  observation tables only. A lookup table belongs inside an expression; do not add
  it as a second observation source just to account for every supplied file.
- A constant partition accepts ONLY train or test. excluded is permitted ONLY as
  a value in a column's explicit map. Do not invent an excluded whole-file source.
- Prefer the documented observation identifier over row position when one exists.
  Subject cardinality alone does not establish the scientific unit.
- A filename transform needs documented meaning, not merely a plausible pattern.
  If that meaning is missing, abstain. Examples below teach syntax, never supply
  evidence or citations for the user's files. Use only their actual documentation.
Complete synthetic examples, checked against the same executor:
''' + json.dumps(EXAMPLES, ensure_ascii=False, separators=(',', ':'))
