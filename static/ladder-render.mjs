import {plural} from './ladder-figure.mjs?v=ladder-1';
import {ladderView,confirmable,bindingQuestions} from './ladder-view.mjs?v=mapping-diagnostics-1';
// Every value from a ladder or a file enters the DOM through textContent, never parsed markup.
function el(tag,attrs={},...children){
 const node=document.createElement(tag);
 for(const [k,v] of Object.entries(attrs)){
  if(k==='class')node.className=v;
  else if(k.startsWith('on'))node.addEventListener(k.slice(2),v);
  else if(k==='text')node.textContent=v;
  else if(v!==null&&v!==undefined&&v!==false)node.setAttribute(k,v);
 }
 for(const child of children.flat(Infinity))if(child!==null&&child!==undefined&&child!==false)node.append(child instanceof Node?child:document.createTextNode(String(child)));
 return node;
}
function builderField(name,control,hint=null){
 control.setAttribute('aria-label',name);
 return el('label',{class:'builder-field'},el('span',{class:'builder-field-name'},name),control,
  hint&&el('small',{class:'builder-field-hint'},hint));
}
const kicker=text=>el('p',{class:'product-kicker'},text);
function witnessItem(w){
 const side=(label,s)=>[el('b',{},label+': ',s.sample),...s.unit_source.map(ref=>el('small',{},`${ref.file} ${ref.at}`,el('br')))];
 return el('li',{},el('b',{},w.unit),...side('Training',w.train),...side('Evaluation',w.test));
}

function levelItem(row,level={}){
 const bar=el('span');if(row.percent!==null)bar.style.width=`${Math.min(100,Math.max(row.percent,row.percent>0?1.5:0))}%`;
 const measured=level.status==='measured'&&row.percent!==null;
 return el('li',{class:`ladder-row row-${row.tone}${row.isClaim?' is-claim':''}`},
  el('div',{class:'level-name'},row.name,el('span',{class:'level-kind'},row.kind),row.isClaim&&el('span',{class:'claim-badge'},'Your claim')),
  el('div',{class:'level-measure'},
   measured?el('p',{class:'level-headline'},el('span',{class:'level-count'},level.shared.toLocaleString('en-US')),
     el('span',{class:'level-of'},`of ${level.test_units.toLocaleString('en-US')} evaluation ${plural(row.name,level.test_units)} also in training`)):el('p',{class:'level-detail'},row.detail),
   measured&&el('div',{class:'level-bar',role:'img','aria-label':`${row.percent}% of evaluation ${row.name} values also occur in training`},bar),
   measured&&el('p',{class:'level-detail'},`${level.affected_test_rows.toLocaleString('en-US')} of ${level.test_rows.toLocaleString('en-US')} evaluation rows affected`,el('span',{class:'level-percent'},` · ${row.percent}%`))),
  el('div',{class:'level-state'},el('span',{class:`tone-chip tone-${row.tone}`},row.state)),
  (row.meaning||row.notes.length>0||row.witnesses.length>0)&&el('div',{class:'level-extra'},
   row.meaning&&el('p',{class:'level-meaning'},'Proposer’s note (unverified): '+row.meaning),
   ...row.notes.map(n=>el('p',{class:'level-note'},n)),
   row.witnesses.length>0&&el('details',{class:'witnesses'},el('summary',{},`Witnesses · first ${row.witnesses.length} shared ${row.name} values with their source rows`),el('ul',{class:'witness-list'},row.witnesses.map(witnessItem)))));
}

function renderCitationReview(review){
 if(!review)return null;
 return el('section',{class:'panel-meta'},el('h3',{},'Check the documentation behind each binding'),el('p',{},review.scope),
  ...review.requirements.map(r=>el('div',{},el('p',{},el('strong',{},r.description)),
   el('p',{class:r.missing_terms.length?'check-error':'hint'},r.missing_terms.length?'Missing cited field references: '+r.missing_terms.join(', '):'Field references appear in cited text. Meaning is not verified.'),
   el('details',{},el('summary',{},'Candidate passages · not verified support'),...r.candidates.map(c=>el('blockquote',{},el('pre',{style:'white-space:pre-wrap'},c.text+(c.truncated?' [line truncated]':'')),el('cite',{},`${c.file}, line ${c.line}`)))))));
}

function renderBindingQuestions(spec){
 return el('section',{class:'binding-questions'},kicker('Check the definition'),
  ...bindingQuestions(spec).map((q,i)=>el('div',{class:'binding-question'},el('span',{class:'binding-number'},String(i+1)),
   el('div',{},el('h3',{},q.question),...q.answers.map(a=>el('p',{},a))))),
  el('p',{class:'check-hint'},'These are recorded rules, not verified scientific meanings. Correct them before measuring.'));
}

function renderBindingFailures(file){
 if(!file.failures?.length)return null;
 return el('section',{class:'binding-failures'},el('h4',{},'Inspect unmapped rows'),
  el('p',{},`${file.unmapped.toLocaleString('en-US')} unmapped across this entire source; first ${file.failures.length} shown. Positions are data rows, excluding a CSV header. Excluded partitions are included; this is a local diagnostic, not a verdict.`),
  el('table',{class:'builder-table'},el('thead',{},el('tr',{},...['Data row','Source identifier','Extracted key','Why unmapped'].map(x=>el('th',{},x)))),
   el('tbody',{},file.failures.map(r=>el('tr',{},el('td',{'data-label':'Data row'},r.row),el('td',{'data-label':'Source identifier'},r.raw||'— missing —'),el('td',{'data-label':'Extracted key'},r.key??'— unavailable —'),el('td',{'data-label':'Why unmapped'},r.reason))))));
}

function renderBindingSamples(preview){
 if(!preview)return null;
 if(!preview.available)return el('p',{class:'check-hint'},preview.reason);
 const files=preview.files.map((p,i)=>{
  const table=el('table',{class:'builder-table'},
   el('thead',{},el('tr',{},el('th',{},'Source identifier'),el('th',{},preview.level))),
   el('tbody',{},p.examples.map(r=>el('tr',{},el('td',{},r.raw),el('td',{},r.value??'— unmapped —')))));
  return el('details',{...(i<2?{open:'true'}:{})},el('summary',{},p.file),
   Number.isInteger(p.rows)&&el('p',{},`${p.rows.toLocaleString('en-US')} source rows · ${p.unmapped.toLocaleString('en-US')} unmapped.`),
   table,renderBindingFailures(p));
 });
 return el('section',{class:'builder-preview binding-samples'},el('h3',{},'See the identity this rule produces'),
  el('p',{class:'hint'},'Local row-to-unit examples, not an independence verdict or verified meaning. First six rows of each source, including excluded rows. Check that these values retain the unit and namespace your claim needs.'),...files);
}

function renderReviewContext(context,preview=null){
 if(!context)return el('p',{},'This older result does not retain partition and derivation review details.');
 const p=context.population;
 return el('section',{class:'panel-meta'},el('h3',{},'Population and partition rules'),
  el('p',{},`${p.train} training · ${p.test} evaluation · ${p.excluded} excluded observations after deduplication.`),
  el('p',{},'The table counts raw source rows before deduplication.'),
  el('table',{class:'builder-table'},el('thead',{},el('tr',{},...['Source / column','Raw label → role','Rows'].map(x=>el('th',{},x)))),
   el('tbody',{},context.partitions.map(r=>el('tr',{},el('td',{},`${r.file} / ${r.column||'whole file'}`),el('td',{},`${r.label} → ${r.role}`),el('td',{},r.rows))))),
  el('h3',{},'How each level was derived'),
  el('ul',{},context.sources.map(r=>el('li',{},`Sample in ${r.file}: ${r.sample}; deduplicate: ${r.deduplicate}`)),
   context.levels.map(r=>el('li',{},`${r.name}: ${r.rule}`,Object.entries(r.overrides).map(([f,rule])=>`; ${f}: ${rule}`)))),
  renderBindingSamples(preview),el('h3',{},'Cited documentation'),el('p',{},'Supplied context, not automatic confirmation.'),
  ...(context.citations||[]).map(c=>el('blockquote',{},el('pre',{style:'white-space:pre-wrap'},c.quote),
   el('cite',{},`${c.file}, lines ${c.start_line}–${c.end_line}`))),renderCitationReview(context.citation_review));
}

function confirmBox(result,onConfirm){
 const c=onConfirm&&confirmable(result);if(!c)return null;
 if(!result.review_context)return el('p',{},'Measure again with the current app to review partition rules before confirming.');
 const id='confirm-'+c.level,box=el('input',{type:'checkbox',id});
 const go=el('button',{class:'primary',type:'button',disabled:'true',onclick:()=>onConfirm(c.level)},'Confirm and measure again');
 box.addEventListener('change',()=>{go.disabled=!box.checked});
 return el('div',{class:'confirm-box'},el('label',{for:id},box,' '+result.review_context.confirmation+(c.perSample?' Every sample has its own value; I have checked that this is still the intended identity.':'')),go);
}

function renderLadder(panel,result,onConfirm,preview=null){
 const view=ladderView(result),source=result.source;
 panel.replaceChildren(...[
  source&&el('div',{class:'panel-source'},kicker('Benchmark'),el('h3',{},source.title),el('p',{},source.summary),
   el('div',{class:'source-links'},el('a',{href:source.url,target:'_blank',rel:'noopener noreferrer'},'Dataset source ↗'),el('span',{},'Spec: ',el('code',{},source.spec)),source.licences.length>0&&el('span',{},source.licences.join(' · ')))),
  el('div',{class:'panel-claim'},kicker(`Claim · needs ${view.claimLevel} held out`),el('blockquote',{},view.claim)),
  el('div',{class:`panel-finding tone-${view.finding.tone}`},el('span',{class:'finding-label'},'Finding at '+view.claimLevel),el('h4',{},view.finding.title),el('p',{},view.finding.reason),el('details',{class:'result-assumptions',...(confirmable(result)?{open:'true'}:{})},el('summary',{},'Review the binding and partition assumptions'),renderReviewContext(result.review_context,preview)),view.finding.warning&&el('p',{class:'finding-warning'},view.finding.warning),(result.confirmed_levels||[]).length>0&&el('p',{class:'finding-confirmed'},'Confirmed by you: '+result.confirmed_levels.join(', ')),confirmBox(result,onConfirm)),
  el('div',{class:'ladder-axis','aria-hidden':'true'},el('span',{},'Level · finer to coarser'),el('span',{},'Evaluation units also in training')),
  el('ol',{class:'ladder-rows','aria-label':'Ladder levels, finest first'},view.rows.map(row=>levelItem(row,result.levels.find(l=>l.name===row.name)))),
  el('div',{class:'panel-meta'},el('p',{},view.population),...view.agreements.map(a=>el('p',{},a)),el('p',{},view.scope),
   el('details',{},el('summary',{},'Spec and input hashes (SHA-256)'),el('dl',{},el('dt',{},'spec'),el('dd',{},view.specHash),...view.inputs.flatMap(([name,hash])=>[el('dt',{},name),el('dd',{},hash)]))))].filter(Boolean));
 panel.hidden=false;
}


export {el,kicker,builderField,renderLadder,renderReviewContext,renderCitationReview,renderBindingQuestions,renderBindingSamples,renderBindingFailures};
