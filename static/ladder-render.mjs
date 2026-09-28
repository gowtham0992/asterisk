import {plural} from './ladder-figure.mjs?v=ladder-1';
import {ladderView,confirmable} from './ladder-view.mjs?v=release-review-1';
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

function renderReviewContext(context){
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
  el('h3',{},'Cited documentation'),el('p',{},'Supplied context, not automatic confirmation.'),
  ...(context.citations||[]).map(c=>el('blockquote',{},el('pre',{style:'white-space:pre-wrap'},c.quote),
   el('cite',{},`${c.file}, lines ${c.start_line}–${c.end_line}`))));
}

function confirmBox(result,onConfirm){
 const c=onConfirm&&confirmable(result);if(!c)return null;
 if(!result.review_context)return el('p',{},'Measure again with the current app to review partition rules before confirming.');
 const id='confirm-'+c.level,box=el('input',{type:'checkbox',id});
 const go=el('button',{class:'primary',type:'button',disabled:'true',onclick:()=>onConfirm(c.level)},'Confirm and measure again');
 box.addEventListener('change',()=>{go.disabled=!box.checked});
 return el('div',{class:'confirm-box'},el('label',{for:id},box,' '+result.review_context.confirmation+(c.perSample?' Every sample has its own value; I have checked that this is still the intended identity.':'')),go);
}

function renderLadder(panel,result,onConfirm){
 const view=ladderView(result),source=result.source;
 panel.replaceChildren(...[
  source&&el('div',{class:'panel-source'},kicker('Benchmark'),el('h3',{},source.title),el('p',{},source.summary),
   el('div',{class:'source-links'},el('a',{href:source.url,target:'_blank',rel:'noopener noreferrer'},'Dataset source ↗'),el('span',{},'Spec: ',el('code',{},source.spec)),source.licences.length>0&&el('span',{},source.licences.join(' · ')))),
  el('div',{class:'panel-claim'},kicker(`Claim · needs ${view.claimLevel} held out`),el('blockquote',{},view.claim)),
  renderReviewContext(result.review_context),
  el('div',{class:`panel-finding tone-${view.finding.tone}`},el('span',{class:'finding-label'},'Finding at '+view.claimLevel),el('h4',{},view.finding.title),el('p',{},view.finding.reason),view.finding.warning&&el('p',{class:'finding-warning'},view.finding.warning),(result.confirmed_levels||[]).length>0&&el('p',{class:'finding-confirmed'},'Confirmed by you: '+result.confirmed_levels.join(', ')),confirmBox(result,onConfirm)),
  el('div',{class:'ladder-axis','aria-hidden':'true'},el('span',{},'Level · finer to coarser'),el('span',{},'Evaluation units also in training')),
  el('ol',{class:'ladder-rows','aria-label':'Ladder levels, finest first'},view.rows.map(row=>levelItem(row,result.levels.find(l=>l.name===row.name)))),
  el('div',{class:'panel-meta'},el('p',{},view.population),...view.agreements.map(a=>el('p',{},a)),el('p',{},view.scope),
   el('details',{},el('summary',{},'Spec and input hashes (SHA-256)'),el('dl',{},el('dt',{},'spec'),el('dd',{},view.specHash),...view.inputs.flatMap(([name,hash])=>[el('dt',{},name),el('dd',{},hash)]))))].filter(Boolean));
 panel.hidden=false;
}


export {el,kicker,renderLadder,renderReviewContext};
