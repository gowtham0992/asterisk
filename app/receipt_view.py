"""Offline, escaped evidence presentation. No external assets or executable inputs."""
from .evaluation_intent import describe
import hashlib
import html
import json
from pathlib import Path
from .witness import inspect_witness
from .receipt_context import review_context, binding_scope
from .receipt_verification import assess_receipt


def esc(value):
    return html.escape(str(value), quote=True)


def section(title, content, anchor=None):
    target = ' id="'+esc(anchor)+'" tabindex="-1"' if anchor else ''
    return '<section'+target+'><h2>'+esc(title)+'</h2>'+content+'</section>'


def render_receipt(result, files):
    expected = result.get('input_hashes')
    actual = {n: hashlib.sha256(t.encode()).hexdigest() for n,t in files.items()}
    intact = bool(expected) and expected == actual
    verdict = result.get('verdict') or {}
    decision = verdict.get('verdict', 'incomplete') if intact else 'unverifiable'
    assessment=assess_receipt(result,files) if intact else {'matches':False,'reason':'Input hashes differ'}
    if intact and result.get('engine_version')=='primitive-v4' and not assessment['matches']:
        decision='inconsistent'
    titles = {'inconsistent':'The retained receipt is inconsistent.','violation':'Recorded identities appear on both sides.',
              'clear':'No recorded overlap within the confirmed binding.',
              'clear_pending_confirmation':'No overlap recorded. Identity meaning needs confirmation.',
              'insufficient':'The evidence cannot establish separation.',
              'incomplete':'No completed verdict.', 'unverifiable':'The inputs do not match the saved receipt.'}
    context = review_context(result, files)
    confirmation = result.get('binding_confirmation') or result.get('preflight_confirmation') or {}
    body = '<header><p class="eyebrow">✱ ASTERISK / PORTABLE RECEIPT</p><h1>'+esc(titles.get(decision,'Historical result'))+'</h1><p>'+esc(result.get('original_claim') or result.get('claim',''))+'</p></header>'
    body += section('Read this first', '<p>This file opens offline. It contains source evidence; share it only with authorized recipients.</p><p><strong>'+('Input hashes matched when this view was generated.' if intact else 'Input integrity failed; no definitive conclusion is displayed.')+'</strong> This is an unsigned presentation, not an authenticity certificate. To recompute, obtain and verify a matching Asterisk release separately from this receipt. From that trusted installation directory, run <code>python -m asterisk verify /absolute/path/to/extracted-receipt</code>. This checks bytes, measurements and decision consistency without credentials or executing bundled Python. Do not run the command from inside the received bundle. An unsigned bundle can have its inputs, checker and manifest replaced together; its own verifier is not independent evidence of authenticity.</p>', anchor='verification')
    if decision=='inconsistent':
        body += section('Verification failed','<p>'+esc(assessment['reason'])+'</p><p>No definitive conclusion is supported. The fields below are retained history, not verified evidence. Re-run the check against the original files.</p>')
    diagnostic=context.get('identity_diagnostics',{})
    if diagnostic.get('identity_count'):
        body += section('Review similar-looking identity values', '<p>'+esc(diagnostic['message'])+'</p><p>'+esc(diagnostic['scope'])+'</p><pre>'+esc(json.dumps(diagnostic['examples'],ensure_ascii=True,indent=2))+'</pre>')
    body += section('Intended evaluation', '<p>'+esc(describe(result.get('evaluation_intent')))+'</p>')
    body += section('The recorded assumption', '<p>'+esc(confirmation.get('text','No confirmed identity binding is recorded.'))+'</p><p>Recorded actor: <code>'+esc(confirmation.get('origin','unrecorded'))+'</code> · '+esc(confirmation.get('confirmed_at','No timestamp'))+'</p><p>Confirmation records an assumption. It does not independently establish what an identifier means.</p>', anchor='assumption')
    from .preparation.receipt_context import retained_preparation
    preparation = retained_preparation(files)
    if preparation:
        if preparation.get('error'):
            prepared_body = '<p>'+esc(preparation['error'])+'</p>'
        else:
            prepared_body = '<p>The retained extraction recomputes to the supplied tables. This establishes the recorded transformation, not the scientific meaning of its identifiers.</p><p>Preparation reviewer: '+esc(preparation['actor'])+'</p>'
            model = preparation.get('model_proposal')
            if model:
                prepared_body += '<p>Input preparation used a recorded model proposal: '+esc(model['model'])+' · '+esc(model['provider'])+'. Application code measured the overlap. This retained record is not provider-authenticated proof.</p><p>Proposal payload SHA-256: <code>'+esc(model['payload_hash'])+'</code></p>'
            else:
                prepared_body += '<p>No model proposal is recorded for these prepared inputs.</p>'
            prepared_body += '<details><summary>Source columns, lookup and partition rules</summary><pre>'+esc(json.dumps(preparation['spec'],ensure_ascii=False,indent=2))+'</pre></details>'
            prepared_body += '<p>Showing '+str(len(preparation['passages']))+' of '+str(preparation['passage_count'])+' retained source passages. Read their meaning before accepting the binding.</p>'
            for passage in preparation['passages']:
                prepared_body += '<blockquote>'+esc(passage['quote'])+'</blockquote><p>Inside preparation-review.json: '+esc(passage['file'])+' · lines '+str(passage['first'])+'–'+str(passage['last'])+'</p>'
        body += section('How source files became these tables', prepared_body)
    from .preparation.projection import receipt_projection
    projected, projection_issues = receipt_projection(files)
    if projected or projection_issues:
        disclosure = '<p>These are client-reported preparation records, not scientific evidence or anonymization. The listed projected hashes, headers and counts match the supplied projected sources. Original files were not received or authenticated. Witness line numbers refer to supplied projected files; projection can change physical line numbers.</p>'
        for item in projected:
            disclosure += '<details><summary>'+esc(item['file'])+' · '+esc(item['records'])+' records</summary><p>Included fields: '+esc(', '.join(item['included']))+'</p><p>Withheld fields (client-reported): '+esc(', '.join(item['withheld']) or 'none')+'</p><p>Original SHA-256 (client-reported): <code>'+esc(item['original_sha256'])+'</code></p><p>Projected SHA-256: <code>'+esc(item['projected_sha256'])+'</code></p></details>'
        disclosure += ''.join('<p>'+esc(issue)+'</p>' for issue in projection_issues)
        body += section('Files before the check', disclosure, anchor='projection')
    docs = {n:t for n,t in files.items() if n.lower().endswith(('.md','.txt'))}
    if docs:
        body += section('Read the supplied identity definitions', '<p>Review these definitions and scope restrictions before accepting the binding. Supplied documentation is context, not an automatic confirmation.</p>'+''.join('<details><summary>'+esc(n)+'</summary><pre>'+esc(t)+'</pre></details>' for n,t in docs.items()))
    if context['documentation']:
        body += section('Passages mentioning the selected identifiers', '<p>Exact excerpts selected by column-name matches. Read their meaning, including any denial or scope restriction; no identity confirmation is inferred. Showing '+str(len(context['documentation']))+' of '+str(context['documentation_total'])+' passages. Full documents are above.</p>'+''.join('<blockquote>'+esc(c['quote'])+'</blockquote><p>'+esc(c['file'])+' · lines '+str(c['start_line'])+'–'+str(c['end_line'])+'</p>' for c in context['documentation']))
    labels = context['partition_labels']
    labels = {role: [json.dumps(value, ensure_ascii=True) for value in values] for role, values in labels.items()}
    body += section('Selected columns and their meaning', '<p>A binding is your choice of columns and what their identifiers represent. A partition is a group of rows assigned a label.</p><p>Training labels: '+esc(', '.join(labels['train']))+' · Evaluation labels: '+esc(', '.join(labels['test']))+'</p>')
    blocked = False
    measurement_links = []
    leading_measurements = []
    if intact:
        for number, (mid, record) in enumerate(result.get('primitive_measurements',{}).items(), 1):
            if record.get('primitive') != 'entity_overlap':continue
            output = record.get('output') or {}
            if record.get('input_hashes') != actual:
                body += section('Measurement unavailable','<p>The measurement input hashes do not match.</p>');continue
            args = record.get('arguments') or {}
            measurement_anchor = 'measurement-'+str(number)
            measurement_links.append((measurement_anchor, 'Measurement '+str(number)))
            binding = '<p>Sample identifier: <code>'+esc(args.get('split_file'))+'.'+esc(args.get('sample_column'))+'</code> → <code>'+esc(args.get('mapping_file'))+'.'+esc(args.get('mapping_sample_column'))+'</code>. Identity: <code>'+esc(args.get('entity_column'))+'</code>. Partition labels: <code>'+esc(args.get('partition_column'))+'</code>.</p>'
            if output.get('available') is not True:
                blocked = True
                same_column = args.get('sample_column') and args.get('sample_column') == args.get('partition_column')
                diagnosis = '<p>The sample identifier and partition label use the same column. Review the column binding before changing the data.</p>' if same_column else ''
                body += section('Check blocked', '<p>No overlap measurement is available because the check was blocked.</p><p>'+esc(output.get('error') or 'The saved measurement is unavailable.')+'</p>'+binding+diagnosis+'<p>Next: review the selected columns and required inputs, then run a new check. Preserve this record as the failed attempt.</p>', anchor=measurement_anchor)
                continue
            metrics = '<div class="metrics">'+''.join('<div><strong>'+esc(output.get(k,'Unavailable'))+'</strong><span>'+esc(t)+'</span></div>' for k,t in [('shared_entities','shared identities'),('affected_test_rows','evaluation rows affected'),('test_rows','total evaluation rows'),('mapping_coverage_percent','mapping coverage (%)'),('ignored_rows','excluded rows'),('train_entities','distinct training identities'),('test_entities','distinct evaluation identities')])+'</div>'
            try:
                scope = binding_scope(files, args)
                excluded = ', '.join(json.dumps(v, ensure_ascii=True) for v in scope['excluded_labels']) or 'none'
                identity = scope['selected_identity']
                scope_text = '<p>'+esc(str(output.get('ignored_rows','Unavailable'))+' rows excluded (labels: '+excluded+')')+'</p><p>'+esc(str(identity['distinct'])+' distinct mapped identities across '+str(identity['samples'])+' selected samples.')+'</p>'
                if identity['warning']:
                    scope_text += '<p><strong>'+esc(identity['warning'])+'</strong></p>'
            except (KeyError, ValueError, TypeError):
                scope_text = '<p>Selected identity counts and excluded labels could not be reconstructed from the retained binding.</p>'
            measurement_section = section('Retained measurement · verification failed' if decision=='inconsistent' else 'What was measured',binding+metrics+scope_text+'<p>This compares exact, case-sensitive recorded identities across the selected training and evaluation labels. It does not detect duplicate content, discover undocumented links between identities, or measure predictive performance. Whether the identifiers represent the intended research unit depends on the reviewed column meaning.</p><details><summary>Original measurement scope · retained verbatim</summary><p>'+esc(output.get('scope','Measurement scope unavailable.'))+'</p><p>Older checker versions used medical-image examples in this wording. The original text is preserved as part of the measurement record.</p></details>'+'<details><summary>Exact columns and labels</summary><pre>'+esc(json.dumps(record.get('arguments'),indent=2))+'</pre></details>', anchor=measurement_anchor)
            if decision=='inconsistent':
                body += measurement_section
            else:
                leading_measurements.append(measurement_section)
            coverage = output.get('coverage') or {}
            if coverage:
                rows = ''.join('<li>'+title+': '+esc(coverage[side]['mapped'])+' of '+esc(coverage[side]['rows'])+' rows mapped; '+esc(coverage[side]['rows']-coverage[side]['mapped'])+' missing.</li>' for side,title in [('train','Training'),('test','Evaluation')] if side in coverage)
                note = '<p>Missing identities on either side can hide overlap, including among mapped evaluation rows. Zero observed overlap does not establish separation. Supply the missing identity mappings and run a new check.</p>' if output.get('missing_count') else '<p>Every selected row has an identity mapping. The meaning of that identity still depends on the binding.</p>'
                body += section('Coverage by partition', '<ul>'+rows+'</ul>'+note)
            witnesses = []
            for i,w in enumerate(output.get('witnesses',[])):
                try:view=inspect_witness(record,files,i)
                except (ValueError,LookupError,TypeError):
                    witnesses.append('<p>Witness '+str(i+1)+' could not be verified against the retained rows.</p>');continue
                sides=[]
                for side,title in [('train','Training'),('test','Evaluation')]:
                    sources=[]
                    for source in ('split','mapping'):
                        row=view['sides'][side][source]
                        fields=''.join('<div'+(' class="key"' if c in row['highlights'] else '')+'><dt>'+esc(c)+'</dt><dd>'+esc(row['values'][c])+'</dd></div>' for c in row['columns'])
                        sources.append('<h4>'+esc(row['file'])+' · CSV row '+str(row['csv_row'])+'</h4><dl>'+fields+'</dl>')
                    sides.append('<div><h3>'+title+' sample '+esc(view['sides'][side]['sample'])+'</h3>'+''.join(sources)+'</div>')
                witnesses.append('<details><summary>Identity '+esc(w['entity'])+' · inspect checker-input rows</summary><div class="sides">'+''.join(sides)+'</div></details>')
            body += section('Follow a witness',('<p>'+str(len(witnesses))+' retained witness pairs. Counts above use the full tables. Rows below come from the files supplied to this check; if those files were prepared, they are not raw upstream records. The preparation record retains the source transformation.</p>'+''.join(witnesses)) if witnesses else '<p>No witness pairs were retained. Zero observed overlap alone is not proof of separation when mapping coverage is incomplete.</p>', anchor='witnesses-'+str(number))
            measurement_links.append(('witnesses-'+str(number), 'Witness rows '+str(number)))
    unknowns = list({v.casefold():v for v in verdict.get('limitations',[])+verdict.get('missing_evidence',[])}.values())
    if blocked:
        body += section('About the retained interpretation', '<p>The requests below are preserved from the original run. They may misdiagnose which column failed. The blocking error applies to the configured sample column shown above; it does not establish that a different identifier column is duplicated.</p>')
    if blocked:
        body += section('Original interpretation', '<details><summary>Original interpretation · may be incorrect</summary><ul>'+''.join('<li>'+esc(v)+'</li>' for v in unknowns)+'</ul></details>')
        unknowns = ['The intended sample-to-identity join and its coverage were not established by this attempt. Review the selected columns before modifying source data.']
    body += section('What remains unknown','<ul>'+''.join('<li>'+esc(v)+'</li>' for v in unknowns)+'</ul><p>Exact recorded IDs only. This does not measure duplicate content, undocumented links, preprocessing leakage or the effect on accuracy.</p>', anchor='limits')
    replay=result.get('primitive_replays') or []
    records=result.get('primitive_measurements') or {}
    replay_ok=assessment['matches'] and bool(records) and all(any(r.get('measurement_id')==mid and r.get('matches') is True for r in replay) for mid in records)
    replay_text = 'The retained record reports a matching replay for every measurement.' if replay_ok else 'A complete matching replay is not recorded.'
    if blocked:
        replay_text = ('The retained record reports matching outputs, including a blocked check.' if replay_ok else 'A complete matching replay is not recorded.')+' Repeatability of an error does not establish separation.'
    body += section('Repeatability', '<p>'+replay_text+' Replay means repeating the check in a separate execution environment. This viewer does not start a new execution. The primitive implementation hash covers the five measurement modules, not the host renderer or this HTML. An unsigned manifest checks byte consistency, not authorship. Repeatability does not establish scientific validity.</p>')
    if result.get('setup_observation'):
        body += section('Setup record','<details><summary>Initial proposal, confirmed fields and review timing</summary><pre>'+esc(json.dumps(result['setup_observation'],indent=2))+'</pre></details>')
    body += section('Source citations · documentation or data',''.join('<details><summary>'+esc(c.get('file',''))+' · cited passage</summary><blockquote>'+esc(c.get('quote',''))+'</blockquote><p>'+esc(c['display_scope'])+'</p></details>' for c in context['citations']))
    body += section('Original files and hashes','<p>CSV row references count logical records, including the header as row 1. A quoted multiline cell is one record.</p>'+''.join('<details><summary>'+esc(n)+'</summary><p class="hash">SHA-256 '+esc(actual[n])+'</p><pre>'+esc(t)+'</pre></details>' for n,t in files.items()))
    body += section('Reviewer worksheet','<p>Write these answers before discussing the expected result. Keep your notes with the evidence ZIP. No response is sent anywhere.</p><ol><li>What exact condition was checked, or attempted?</li><li>Inspect a witness if one is available: a pair of rows from the selected training labels ('+esc(', '.join(labels['train']))+') and evaluation labels ('+esc(', '.join(labels['test']))+') sharing an identity. Otherwise explain why the check has no witness.</li><li>What assumption links the identifier to the research claim?</li><li>What remains unknown? What would you do next?</li></ol><p>Use the separate review worksheet for timed notes, or print this receipt to annotate it.</p>', anchor='review')
    links = measurement_links + [('assumption', 'Identity assumption'), ('limits', 'Limits'), ('verification', 'Verify the receipt'), ('review', 'Review questions')]
    navigation = '<nav class="receipt-navigation" aria-label="Receipt sections"><p class="eyebrow">INSPECT THIS RECEIPT</p><div>'+''.join('<a href="#'+anchor+'">'+esc(title)+' <span aria-hidden="true">↓</span></a>' for anchor,title in links)+'</div></nav>'
    body = body.replace('</header>', '</header>'+navigation+''.join(leading_measurements), 1)
    css=(Path(__file__).resolve().parent.parent/'static/receipt.css').read_text()
    policy="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"
    return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="'+esc(policy)+'"><title>Asterisk — portable receipt</title><style>'+css+'</style></head><body><main>'+body+'</main></body></html>'


def render_worksheet(result):
    import base64
    root=Path(__file__).resolve().parent.parent/'static'
    page=(root/'review.html').read_text()
    script=(root/'review.js').read_text()
    digest=base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()
    policy="default-src 'none'; style-src 'unsafe-inline'; script-src 'sha256-"+digest+"'; base-uri 'none'; form-action 'none'"
    page=page.replace('<link rel="stylesheet" href="receipt.css">','<style>'+(root/'receipt.css').read_text()+'</style>')
    page=page.replace('<script src="review.js" defer></script>','<meta http-equiv="Content-Security-Policy" content="'+esc(policy)+'">')
    reference=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    page=page.replace('<body>','<body data-receipt-reference="'+reference+'">')
    return page.replace('</body>','<script>'+script+'</script></body>')
