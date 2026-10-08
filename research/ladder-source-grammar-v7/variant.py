"""Research-only reminder; never selected by the shipping application."""
def install(lp):
    lp.PROMPTS['v7'] = lp.SYSTEM_V4 + '''
SOURCE SAMPLE AND CLAIM CHECK
- sources[].sample identifies one observation using only column, optional basename/prefix, row:true, or one lookup. Never put field or characters in a source sample; these operators are for levels[].expression only.
- A lines source exposes the entire original line as column value. A trailing class label is part of that line. You may keep that complete value as its observation key and derive the documented unit separately in a level expression.
- claim.level names the exact generating unit requested by the claim, not the filename or observation merely because it is easiest to parse. A repeated group token local to each action/site/class must retain that documented namespace.
- Before returning, check that each source sample follows its narrower grammar, each claimed unit is supported by the cited documentation, and every transform matches the requested unit. If a necessary boundary or mapping is absent, abstain.
'''
