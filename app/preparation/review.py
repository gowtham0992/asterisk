"""Offline observation-policy review prototype. No provider calls or confirmation.

Explicit developer-supplied policies demonstrate the review surface; this does
not infer policy correctness or produce an accepted scientific receipt.
"""
import copy
import html
import importlib.util
import json
from collections import Counter
from .repetition_diagnostic import annotate_repetition_error,DUPLICATE_ERROR
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
s = importlib.util.spec_from_file_location('frozen_extraction', ROOT/'evaluation/extraction-v1/executor.py')
executor = importlib.util.module_from_spec(s)
s.loader.exec_module(executor)
CORRECTABLE_ERRORS = {'Duplicate sample or conflicting cross-partition sample',
    'Unmapped sample; coverage incomplete', 'Conflicting duplicate lookup identity'}


def population(extraction):
    counts = Counter(row['partition'] for row in extraction['lineage'])
    return {name: counts[name] for name in ('train', 'test', 'excluded')}


def cited_text(citation, files):
    if not isinstance(citation, dict) or set(citation) != {'file','start_line','end_line'}:
        raise ValueError('Invalid policy citation')
    name, first, last = citation['file'], citation['start_line'], citation['end_line']
    if not isinstance(name,str) or name not in files or type(first) is not int or type(last) is not int:
        raise ValueError('Invalid policy citation')
    lines = files[name].splitlines()
    if not 1 <= first <= last <= len(lines) or last-first >= 40:
        raise ValueError('Invalid policy citation range')
    quote = '\n'.join(lines[first-1:last])
    if len(quote) > 8000:
        raise ValueError('Policy citation too large')
    return {**citation, 'quote': quote}


def source_changes(before, after):
    """Compare original source occurrences, not mutable derived sample IDs."""
    if before is None:
        return {'available':False, 'reason':'Original proposal blocked; no before-values were established.'}
    def index(extraction):
        result = {}
        for row in extraction['lineage']:
            values = {key:row[key] for key in ('sample','entity','partition')}
            for ref in row['occurrences']:
                key = executor.canonical(ref)
                if key in result:
                    raise ValueError('Repeated source occurrence in comparison')
                result[key] = (ref,values)
        return result
    original, revised = index(before), index(after)
    if original.keys() != revised.keys():
        raise ValueError('Source occurrence coverage changed during review')
    counts = {'sample':0,'entity':0,'partition':0}
    examples, changed = [], 0
    for key,(ref,old) in original.items():
        new = revised[key][1]
        fields = [name for name in counts if old[name] != new[name]]
        if fields:
            changed += 1
            for name in fields: counts[name] += 1
            if len(examples) < 20:
                examples.append({'source':ref,'before':old,'after':new,'changed_fields':fields})
    return {'available':True,'source_records':len(original),'changed_records':changed,
            'changed_fields':counts,'examples':examples,'example_limit':20}


def prepare(spec, files, policies, *, review_version=3):
    if review_version not in (2,3):
        raise ValueError('Unsupported review version')
    # A duplicate-policy blocker must not prevent an explicit correction.
    # Preserve the failed proposal and never invent its uncomputed counts.
    original_error = None
    try:
        proposed = executor.extract(spec, files)
    except executor.ExtractionError as exc:
        if str(exc) not in CORRECTABLE_ERRORS:
            raise
        proposed = None
        original_error = str(exc)
    names = {source['file'] for source in spec['sources']}
    if not isinstance(policies,dict) or set(policies) != names:
        raise ValueError('An explicit observation decision is required for every source')
    revised = copy.deepcopy(spec)
    decisions = []
    for source in revised['sources']:
        policy = policies[source['file']]
        required = {'sample','repeats','evidence'}
        if not isinstance(policy,dict) or not required <= set(policy) or set(policy)-required-{'entity','partition'}:
            raise ValueError('Each decision needs sample, repeats, and evidence; only entity and partition may also be revised')
        if policy['repeats'] not in ('distinct','collapse'):
            raise ValueError('Choose distinct observations or collapse retransmissions')
        if not isinstance(policy['evidence'],list) or not 1 <= len(policy['evidence']) <= 20:
            raise ValueError('Cite the observation and repetition policy')
        citations = [cited_text(c,files) for c in policy['evidence']]
        if policy['sample'] == {'row':True} and policy['repeats'] == 'collapse':
            raise ValueError('Unique row identity cannot collapse retransmissions')
        source['sample'] = copy.deepcopy(policy['sample'])
        source['deduplicate'] = policy['repeats'] == 'collapse'
        # The unchanged closed-language executor validates expressions and every
        # partition assignment. No code or unchecked transform enters the path.
        changes = {key:copy.deepcopy(policy[key]) for key in ('entity','partition') if key in policy}
        source.update(changes)
        decisions.append({'file':source['file'],'sample':copy.deepcopy(policy['sample']),
                          'repeats':policy['repeats'],'evidence':citations, **changes})
    rejection = None
    try:
        extracted = executor.extract(revised, files)
    except executor.ExtractionError as exc:
        if str(exc) != DUPLICATE_ERROR:
            raise
        rejection = str(exc)
    if rejection is not None:
        # Drop the failed executor's traceback before allocating its diagnostic.
        raise annotate_repetition_error(executor.ExtractionError(rejection),revised,files,executor)
    report = {'schema_version':review_version, 'state':'review_only', 'confirmation':None,
              'scope':('Observation and binding review only; no scientific verdict or confirmed scientific binding.'
                       if any('entity' in d or 'partition' in d for d in decisions)
                       else 'Observation accounting review only; no scientific verdict or confirmed binding.'),
              'original_spec_hash':executor.sha(executor.canonical(spec)),
              'original_spec':copy.deepcopy(spec), 'original_error':original_error, 'input_hashes':extracted['input_hashes'],
              'decisions':decisions, 'proposed_population':population(proposed) if proposed else None,
              'reviewed_population':population(extracted),
              'collapsed_observations':[{'sample':row['sample'],'partition':row['partition'],
                  'occurrences':row['occurrences']} for row in extracted['lineage'] if len(row['occurrences'])>1],
              'extraction':extracted}
    if review_version >= 3:
        report['source_changes'] = source_changes(proposed, extracted)
    report['review_hash'] = executor.sha(executor.canonical(report))
    return report


def render(review, files):
    """Standalone read-only review; no scripts, external resources or telemetry."""
    if review['input_hashes'] != {name:executor.sha(value) for name,value in files.items()}:
        raise ValueError('Review inputs changed; prepare a new review')
    body = {key:value for key,value in review.items() if key != 'review_hash'}
    if executor.sha(executor.canonical(body)) != review.get('review_hash'):
        raise ValueError('Review content changed; prepare a new review')
    esc = lambda value: html.escape(str(value), quote=True)
    before = review['proposed_population'] or {name:'—' for name in ('train','test','excluded')}
    blocked = '<p class="note">Original proposal blocked: '+esc(review['original_error'])+'. No original counts are available.</p>' if review.get('original_error') else ''
    totals = ''.join(f'<div><span>{esc(name.title())} observations</span><strong>{before[name]} <i>→</i> {review["reviewed_population"][name]}</strong></div>' for name in ('train','test','excluded'))
    decisions = []
    for decision in review['decisions']:
        expression = decision['sample']
        binding = 'Every source record is a distinct observation' if expression == {'row':True} else ('Observation identity: '+expression['column'] if set(expression)=={'column'} else 'Observation identity: '+json.dumps(expression,ensure_ascii=False))
        policy = 'Collapse repeated observation IDs; preserve every source occurrence.' if decision['repeats']=='collapse' else 'Keep distinct observations; repeated IDs are rejected.'
        edits = ''.join(f'<p>{esc(key.title())}: <code>{esc(json.dumps(decision[key],ensure_ascii=False))}</code></p>' for key in ('entity','partition') if key in decision)
        quotes = ''.join(f'<blockquote>{esc(c["quote"])}<cite>{esc(c["file"])} · lines {c["start_line"]}–{c["end_line"]}</cite></blockquote>' for c in decision['evidence'])
        decisions.append(f'<section><p class="eyebrow">{esc(decision["file"])}</p><h2>{esc(binding)}</h2><p>{esc(policy)}</p>{edits}{quotes}</section>')
    repeats = []
    for row in review['collapsed_observations']:
        refs = []
        for ref in row['occurrences']:
            location = ref.get('pointer', f'lines {ref.get("line_start")}–{ref.get("line_end")}')
            refs.append(f'<li>{esc(ref["file"])} · {esc(location)}</li>')
        repeats.append(f'<article><h3>{esc(row["sample"])}</h3><p>{len(refs)} source records → 1 observation · {esc(row["partition"])}</p><ul>{"".join(refs)}</ul></article>')
    documents = ''.join(f'<details><summary>{esc(name)}</summary><pre>{esc(content)}</pre></details>' for name,content in files.items())
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Asterisk · Observation review prototype</title><style>
*{box-sizing:border-box}body{margin:0;background:#f6f5ef;color:#233b31;font:16px/1.6 system-ui,sans-serif}main{max-width:1060px;margin:auto;padding:40px 28px 80px}header{display:flex;justify-content:space-between;gap:20px;border-bottom:1px solid #c3cabd;padding-bottom:24px}header b{font-size:25px;letter-spacing:-1px}.badge,.eyebrow{font:12px/1.5 monospace;letter-spacing:1px;text-transform:uppercase}.badge{padding:8px 12px;border:1px solid #697c65;align-self:center}h1{font:clamp(38px,6vw,68px)/1.04 Georgia,serif;letter-spacing:-2px;max-width:820px;margin:44px 0 20px}h2{font:28px/1.25 Georgia,serif;overflow-wrap:anywhere}h3{margin:0;font:22px/1.3 monospace}.intro{max-width:700px;font-size:18px;color:#46584d}.numbers{display:grid;grid-template-columns:repeat(3,1fr);border-block:1px solid #bcc6b7;margin:32px 0}.numbers>div{padding:24px 16px}.numbers span{display:block;font-size:13px}.numbers strong{display:block;font:46px/1.2 Georgia,serif;margin-top:8px}.numbers i{font:22px system-ui;color:#697c65}section{padding:20px 0;border-bottom:1px solid #c3cabd}blockquote{border-left:3px solid #7a915c;padding:16px 22px;margin:24px 0;background:#eceddf;white-space:pre-wrap}cite{display:block;font:12px monospace;margin-top:12px}article{padding:20px;border:1px solid #c3cabd;margin:16px 0;background:#fffefa}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#fffefa;padding:16px;font-size:13px}summary{cursor:pointer;padding:12px 0}summary:focus-visible{outline:3px solid #647c35;outline-offset:4px}.note{padding:20px;background:#e8ebdf}.hash{font:12px/1.6 monospace;overflow-wrap:anywhere}footer{margin-top:36px;font-size:14px}@media(max-width:540px){main{padding:24px 18px 50px}header{flex-wrap:wrap}.numbers{grid-template-columns:1fr}.numbers>div{padding:14px 4px;display:flex;justify-content:space-between;align-items:center;gap:12px}.numbers strong{font-size:34px;margin:0}h1{letter-spacing:-1px}}
</style></head><body><main><header><b>asterisk *</b><span class="badge">Experimental · Not confirmed</span></header><p class="eyebrow">Observation policy / local developer preview</p><h1>One record isn’t always<br>one observation.</h1><p class="intro">Before checking a split, decide what one observation means. This review compares the proposed extraction with an explicitly supplied policy. It does not decide which interpretation is scientifically correct.</p>'''+blocked+'''<div class="numbers">'''+totals+'''</div><p>Counts: original proposal → reviewed draft. Excluded observations stay outside the train/test comparison.</p>'''+''.join(decisions)+'''<section><h2>Records combined by this policy</h2>'''+(''.join(repeats) or '<p>No records are combined.</p>')+'''</section><section><h2>Read the original inputs</h2><p>All supplied text is shown below. Citations locate evidence; they do not certify its meaning.</p>'''+documents+'''</section><footer><p class="note">Read-only prototype. The alternative was supplied by the developer. No human confirmation, model call, Sandbox execution, or scientific verdict occurs on this page.</p><p class="hash">Review hash: '''+esc(review['review_hash'])+'''</p></footer></main></body></html>'''
