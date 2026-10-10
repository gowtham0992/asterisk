"""Research-only focused task. Promotion requires the frozen protocol to pass."""
from app import ladder_proposal as lp

SYSTEM = lp.SYSTEM_V4.split('\nEXAMPLE (fictional).', 1)[0].replace(
    '"levels":[LEVEL, ...],     2-8, finest first',
    '"levels":[LEVEL, LEVEL],   exactly two: observation first, then the unit named in the claim') + '''

SOURCE SAMPLE GRAMMAR (distinct from a level expression)
SAMPLE = {"column":<column>, optional "basename":true, optional "prefix":<int 1-128>}
       | {"row":true}
       | {"lookup":{"file":<table>,"format":<format>,"key_column":<column>,"value_column":<column>,"on":SAMPLE}}
SOURCE.sample must use SAMPLE, never field or characters. Keep an entire text-list line as column "value" when needed; derive its unit in LEVEL.expression.

FOCUSED CLAIM TASK
Return only the observation and the exact claimed unit. Do not add unrelated attributes or other levels.
Read the definition, not just the column names or cardinality. A per-observation identifier cannot substitute for the generating unit requested by the claim.
A group token local to an action, site, or other namespace must retain the documented namespace. A stated filename pattern defines a derivation; a pattern in examples alone does not.
Use the actual recorded assignments. Do not invent label meanings or rebuild a split from the unit being tested.
Use by_source when two source files expose the same unit through differently named columns.
If the unit definition, required identity mapping, partition meaning, or supported extraction operation is absent, abstain and name that missing evidence. Negative documentation takes precedence over a suggestive field name.
Cite the exact defining and partition lines. Never calculate or predict the verdict.
'''


def install():
    lp.PROMPTS['v8'] = SYSTEM
