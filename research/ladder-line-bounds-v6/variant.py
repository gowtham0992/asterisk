"""Install the frozen experimental bounds-only variant in a research process, never in the app."""
def install(lp):
    lp.SYSTEM_V6 = lp.SYSTEM_V4 + """
CITATION BOUNDS
The input also includes documentation_line_counts: the exact number of lines in each documentation list.
For each citation use 1 <= start_line <= end_line <= documentation_line_counts[file].
These are bounds only, not evidence that any line establishes a unit. Keep the existing abstention rules.
"""
    lp.PROMPTS['v6']=lp.SYSTEM_V6
    original=lp.payload
    def payload(claim,files,share_examples=(),documentation=None,version=lp.PROMPT_VERSION):
        body=original(claim,files,share_examples,documentation,'v4' if version=='v6' else version)
        if version=='v6':body['documentation_line_counts']={name:len(lines) for name,lines in body['documentation'].items()}
        return body
    lp.payload=payload
