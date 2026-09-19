import {createInvestigations} from './investigations.js';
const $ = (s, root=document) => root.querySelector(s);
const main = $('#main');
let config = {}, files = [], current = null, busy = false, generation = 0, revisionSource = null;
// All artifact/model text enters the DOM through textContent, never parsed markup.
function el(tag, attrs={}, ...children) {
 const node=document.createElement(tag);
 for(const [k,v] of Object.entries(attrs)) {
  if(k==='class')node.className=v;
  else if(k.startsWith('on'))node.addEventListener(k.slice(2),v);
  else if(k==='text')node.textContent=v;
  else if(v!==null && v!==undefined)node.setAttribute(k,v);
 }
 for(const child of children.flat(Infinity))if(child!==null && child!==undefined)node.append(child instanceof Node?child:document.createTextNode(String(child)));
 return node;
}
const label=t=>el('span',{class:'small-label'},t);
const btn=(text,fn,cls='primary')=>el('button',{class:cls,type:'button',onclick:fn},text);
function toast(text){$('#toast').textContent=text;$('#toast').hidden=false;setTimeout(()=>$('#toast').hidden=true,5000)}
async function api(path,method='GET',body){
 const response=await fetch('/api'+path,{method,headers:{'Content-Type':'application/json','X-Asterisk-Request':'1'},...(body?{body:JSON.stringify(body)}:{})});
 if(!response.ok){let data;try{data=await response.json()}catch{data={detail:'The server did not respond. Check the connection and retry.'}}throw new Error(typeof data.detail==='string'?data.detail:'Check the input and try again.');}
 return response.json();
}
async function history(){
 const rows=await api('/audits');$('#audit-count').textContent=rows.length;
 $('#history').replaceChildren(...(rows.length?rows.map(a=>el('button',{class:'history-item'+(current?.id===a.id?' selected':''),onclick:()=>navigate(a.id)},a.title,el('small',{},(a.revision_kind?(a.revision_kind==='rule'?'Rule revision · ':'Input revision · '):'')+(a.state==='complete'?'Evidence ready':a.state)))):[el('p',{class:'history-empty'},'Your work will appear here.')]));
}
function navigate(id=''){if(busy){toast('A check is running. Let it finish before changing audits.');return}location.hash=id?'audit/'+id:'';if(!id)investigations.route('#investigate');}
function showError(error){let node=$('#form-error')||$('#audit-error');if(node){node.hidden=false;node.textContent=error.message}else toast(error.message)}
function field(id,title,kind,placeholder,value='') {const input=el(kind,{id,name:id,placeholder,...(kind==='input'?{type:'text',maxlength:'120'}:{maxlength:'2000'}),required:'true'});input.value=value;return el('div',{class:'field'},el('label',{for:id},title),input)}
function renderFiles(){const list=$('#files');if(!list)return;list.replaceChildren(...files.map((f,i)=>el('div',{class:'file-chip'},f.name,btn('×',()=>{files.splice(i,1);renderFiles()},'text-button'))));for(const b of list.querySelectorAll('button'))b.setAttribute('aria-label','Remove '+b.parentNode.firstChild.textContent)}
async function addFiles(event){try{const picked=[...event.target.files];const merged=new Map(files.map(f=>[f.name,f]));for(const f of picked){if(f.size>1500000)throw new Error('Each file must be smaller than 1.5 MB.');if(!/^[A-Za-z0-9][A-Za-z0-9_.-]*\.(csv|md|txt)$/.test(f.name))throw new Error('Use CSV, Markdown, or text files with simple filenames.');merged.set(f.name,{name:f.name,content:await f.text()})}const next=[...merged.values()];if(next.length>8)throw new Error('Use at most eight files.');if(next.reduce((n,f)=>n+new TextEncoder().encode(f.content).length,0)>4000000)throw new Error('Total input size must not exceed 4 MB.');files=next;renderFiles()}catch(e){showError(e)}event.target.value=''}
function renderNew(seed=null, source=null){
 current=null;revisionSource=source;generation++;files=seed?.files||[];$('#page-name').textContent=source?'Revise inputs':'New audit';
 const hero=el('section',{class:'hero'},el('div',{},el('div',{class:'eyebrow'},'Evidence before confidence'),el('h1',{},'A strong result.',el('br'),el('em',{},'Under what conditions?')),el('p',{class:'lede'},'Turn a research claim into a check you can inspect. Asterisk traces the data, tests the boundary, and makes the evidence visible.')),el('div',{class:'specimen-graphic','aria-hidden':'true'},el('span',{class:'star'},'✱'),el('span',{class:'graphic-corner'},'FIG. 01'),el('span',{class:'graphic-label'},'EXAMINE THE EXCEPTION')));
 const examples=el('div',{class:'examples'},...[
 ['overlap','01','The hidden overlap','Different images. The same specimens.'],['clean','02','An independent split','A control that should stay clear.'],['missing','03','The missing evidence','Know when the data cannot answer.']
 ].map(([kind,n,t,d])=>el('button',{class:'example',onclick:async()=>{try{const seed=await api('/examples/'+kind);renderNew(seed);$('#title').focus()}catch(e){toast(e.message)}}},el('span',{class:'number'},n),el('span',{class:'arrow','aria-hidden':'true'},'↗'),el('h3',{},t),el('p',{},d))));
 const upload=el('label',{class:'upload-label',for:'upload'},el('strong',{},'Add your research artifacts'),el('span',{},source?'Upload a matching filename to replace its copied contents.':'CSV split + metadata files, with a README or data dictionary'),el('input',{id:'upload',type:'file',multiple:'true',accept:'.csv,.md,.txt',onchange:addFiles}));
 const form=el('form',{onsubmit:submit},el('div',{class:'panel-head'},el('h2',{},source?'Update the claim and evidence':'Start with the claim'),el('span',{class:'step-label'},'01 / 03')),el('div',{class:'form-body'},el('div',{class:'form-row'},field('title','Experiment name','input','e.g. Specimen classification',seed?.title||''),field('claim','What should the model generalize to?','textarea','e.g. Specimens not seen during training.',seed?.claim||'')),upload,el('div',{id:'files',class:'file-list'}),el('div',{class:'error',id:'form-error',role:'alert',hidden:'true'})),el('div',{class:'form-footer'},el('p',{class:'disclosure'},config.executor==='nebius-sandbox'?'Proposing sends documentation and five preview rows per CSV to Nebius. Accepting the check sends all input files to a Nebius Sandbox. During the beta, do not upload personal or sensitive data.':'When you continue, documentation and five preview rows per CSV are sent to Nebius. Full tables are checked locally. Use data you are authorized to share.'),el('button',{type:'submit',class:'primary'},'Propose a check',el('span',{'aria-hidden':'true'},'↗'))));
 main.replaceChildren(...(source?[el('div',{class:'revision-banner'},'Revising inputs from audit '+source.slice(0,8)+'. The original is preserved. Submit to save a new audit.')]:[]),...(source?[el('h1',{},'Update the evidence.')]:[hero,el('div',{class:'section-line'},el('span',{},'Explore a worked example'),el('span',{},'Original synthetic datasets · Live model')),examples]),el('section',{class:'panel'},form),el('div',{class:'below-note'},el('span',{},'Inspectable evidence'),el('span',{},'Explicit unknowns'),el('span',{},'Reproducible checks')));
 renderFiles();history().catch(e=>toast(e.message));
}
async function submit(event){event.preventDefault();if(busy)return;if(!files.length){showError(new Error('Choose an example or add your data and documentation first.'));return}const data={title:$('#title').value.trim(),claim:$('#claim').value.trim(),files};const submit=event.target.querySelector('button[type=submit]');submit.disabled=true;try{current=await api(revisionSource?'/audits/'+revisionSource+'/with-inputs':'/audits','POST',data);window.history.replaceState(null,'','#audit/'+current.id);await proposeCurrent()}catch(e){showError(e)}finally{submit.disabled=false}}
function sidePanel(a){return el('aside',{class:'side-panel'},el('h3',{},'Source artifacts'),...a.files.map(f=>el('div',{class:'source-file'},el('b',{},f.name),el('span',{},f.rows?`${f.rows.toLocaleString()} rows · ${f.columns.length} columns`:`${f.bytes.toLocaleString()} bytes · Documentation`))),el('p',{class:'hint'},'Original inputs are preserved. Counts use all rows, not the model preview.'),a.execution_provenance?el('div',{},el('hr'),label('Check execution'),el('p',{},a.execution_provenance.runtime==='nebius-sandbox'?'Nebius Sandbox · verified against local replay':'Local deterministic check'),a.execution_provenance.image?el('p',{class:'hint'},a.execution_provenance.image+' · '+a.execution_provenance.seconds+'s'):null):null,a.inference?el('div',{},el('hr'),label('Inference provenance'),el('p',{class:'mono'},a.inference.model),el('p',{class:'hint'},`${a.inference.seconds}s · ${a.inference.tokens?.toLocaleString()||'—'} tokens · ${a.inference.attempts||1} attempt(s)`)):null)}
function flow(state,loading){let step=loading||state==='draft'?0:state==='review'||state==='insufficient'?1:2;return el('div',{class:'flow'},...['01  Read the evidence','02  Review the rule','03  Inspect the result'].map((s,i)=>el('div',{class:'flow-step '+(step===i?'active':step>i?'done':'')},s)))}
function citations(rule){return rule.citations.map(c=>el('div',{class:'evidence-quote'},label('Grounded in your documentation'),el('blockquote',{},'“'+c.quote+'”'),el('cite',{},c.file+' · Exact quote verified')))}
function ruleCard(a,review=true){const r=a.reviewed_rule||a.proposal.rule;const notes=a.proposal.rule;const mapping=el('div',{class:'mapping'},el('div',{},el('small',{},r.split_file),el('code',{},r.sample_column)),el('span',{'aria-hidden':'true'},'→'),el('div',{},el('small',{},r.mapping_file||r.split_file),el('code',{},(r.mapping_sample_column||r.sample_column)+' → '+r.entity_column)));
 return el('section',{class:'panel'},el('div',{class:'rule-card'},label(a.reviewed_rule?'Researcher-revised rule':review?'Proposed independence rule':'Accepted independence rule'),el('h2',{},'Keep '+r.unit+' identities separate.'),el('p',{class:'rule-description'},'This checks whether the selected training and evaluation rows share recorded entity IDs. It does not establish model accuracy or prove generalization.'),mapping,el('div',{class:'rule-data'},el('div',{},label('Training labels'),el('b',{},r.train_values.join(', '))),el('div',{},label('Evaluation labels'),el('b',{},r.test_values.join(', '))),el('div',{},label('Partition column'),el('b',{},r.partition_column)),el('div',{},label('Entity column'),el('b',{},r.entity_column)))),citations(r),el('p',{class:'limitation'},'Scope: recorded entity IDs and the selected labels only. This does not detect duplicate content, undocumented identity links, or preprocessing leakage.'),el('details',{},el('summary',{},'Unverified model notes'),el('div',{class:'detail-content'},el('p',{},'These generated notes may contain unsupported assumptions. Verify them against the source documents; they do not change the executable rule.'),el('p',{},notes.explanation),notes.limitations.length?el('ul',{},...notes.limitations.map(note=>el('li',{},note))):null)),review&&config.legacy_audits_enabled?el('div',{class:'rule-actions'},el('p',{},'Does this rule match your intended claim? Accepting checks every row. Local execution is the default.'),config.sandbox_available?el('label',{},el('input',{type:'checkbox',id:'remote-consent'}),' Run this audit in Nebius Sandbox. I confirm sending all its input files; they contain no personal or sensitive data.'):null,btn('Accept rule & run check ↗',runCurrent)):null)}
function resultCard(a){const r=a.result,rule=a.reviewed_rule||a.proposal.rule;const titles={overlap:'The boundary does not hold.',clear:'No entity overlap found.',incomplete:'The evidence is incomplete.'};const desc={overlap:`${r.affected_test_rows} evaluation rows share ${rule.unit} identities with training.`,clear:'The recorded entity IDs are separate under the accepted rule.',incomplete:'Some samples could not be mapped. A clear result cannot be established.'};const banner=el('div',{class:'status-banner '+r.status},el('span',{class:'status-label'},r.status==='overlap'?'Overlap verified':r.status==='clear'?'Check passed · Scoped result':'Additional evidence needed'),el('h2',{},titles[r.status]),el('p',{},desc[r.status]));
 const metrics=el('div',{class:'metrics'},...[[r.shared_entities,'Shared entities'],[r.affected_percent+'%','Evaluation rows affected'],[r.mapping_coverage_percent+'%','Mapping coverage']].map(([n,t])=>el('div',{class:'metric'},el('strong',{},n),el('span',{},t))));
 const track=el('div',{class:'bar-track','aria-label':r.affected_percent+' percent of evaluation rows affected'},el('div',{class:'bar-fill'}),el('div',{class:'bar-rest'}));track.children[0].style.flex=String(r.affected_test_rows);track.children[1].style.flex=String(r.test_rows-r.affected_test_rows);
 const bar=el('div',{class:'overlap-bar'},label('Evaluation partition'),track,el('div',{class:'bar-labels'},el('span',{},r.affected_test_rows+' affected'),el('span',{},r.test_rows+' total rows')));
 const rows=r.witnesses.map(w=>el('tr',{},el('td',{},w.entity),el('td',{},w.train.sample,el('small',{},'Split row '+w.train.split_row+' · Mapping row '+w.train.mapping_row)),el('td',{},w.test.sample,el('small',{},'Split row '+w.test.split_row+' · Mapping row '+w.test.mapping_row))));
 const witnesses=rows.length?[el('div',{class:'witness-title'},el('h3',{},'Follow the evidence'),el('span',{},'UP TO 30 WITNESS PAIRS')),el('div',{class:'table-wrap'},el('table',{},el('thead',{},el('tr',{},el('th',{},'Shared entity'),el('th',{},'Training sample'),el('th',{},'Evaluation sample'))),el('tbody',{},rows)))]:el('div',{class:'empty-result'},r.status==='clear'?'No shared entity witnesses. This checks entity overlap only; it does not certify the entire experiment.':'No overlap found among mapped rows. Resolve the missing mappings before interpreting the result.');
 return el('section',{class:'panel'},banner,metrics,bar,witnesses,r.status==='overlap'?el('div',{class:'next-step'},label('Recommended next step'),el('h3',{},'Split by '+rule.unit+', then evaluate again.'),el('p',{},'Assign each entity to one partition before selecting its samples. Preserve the original experiment and report the new split composition; a changed score alone would not isolate the effect of leakage.')):null,r.missing_count?el('p',{class:'error'},`${r.missing_count} unmapped rows remain. Any overlap count is a lower bound; inspect the evidence export for sample IDs.`):null,el('p',{class:'limitation'},`${r.train_rows} training rows · ${r.test_rows} evaluation rows · ${r.ignored_rows} rows outside selected labels. ${r.scope}`),el('details',{},el('summary',{},'Input fingerprints & reproducibility'),el('div',{class:'detail-content'},...Object.entries(r.hashes).map(([name,hash])=>el('p',{class:'mono'},name,el('br'),hash)),a.execution_provenance?el('p',{class:'mono'},'Checker SHA-256',el('br'),a.execution_provenance.engine_sha256):el('p',{},'Legacy audit: checker compatibility will be verified at export.'),el('p',{},'Export the evidence bundle and run python3 verify.py to check file integrity and replay this result.'))));}
function renderAudit(a,loading=false){current=a;$('#page-name').textContent=loading?'Reading evidence':a.state==='complete'?'Audit evidence':'Review audit';const actions=el('div',{class:'actions'});if(a.state==='complete')actions.append(el('a',{class:'secondary',href:'/api/audits/'+a.id+'/export'},'↓ Export evidence'));if(!loading&&config.legacy_audits_enabled){actions.append(btn('Revise inputs',()=>{location.hash='revise/'+a.id},'secondary'));if(['review','complete'].includes(a.state))actions.append(btn('Revise rule',()=>renderRuleEditor(a),'secondary'));actions.append(btn('Delete audit',deleteCurrent,'text-button'));}
 let content;
 if(loading)content=el('section',{class:'panel loading-panel','aria-live':'polite'},el('span',{class:'loader','aria-hidden':'true'},'✱'),el('h2',{},'Reading between the rows.'),el('p',{},'Nemotron is examining your claim, documentation, and table schemas. The proposed rule will cite the evidence it relies on.'),el('span',{class:'small-label'},'Live inference · Usually under a minute'));
 else if(!config.legacy_audits_enabled&&a.state!=='complete'&&a.state!=='review')content=el('section',{class:'panel detail-content'},el('h2',{},'Historical audit · read-only'),el('p',{},'This workflow is retired. Its saved state is preserved; use a new split receipt for a new check.'));
 else if(a.state==='draft')content=el('section',{class:'panel loading-panel'},el('h2',{},'Your artifacts are saved.'),el('p',{},'Request a proposal to connect the claim to an executable check.'),btn('Propose the rule ↗',proposeCurrent));
 else if(a.state==='insufficient')content=el('section',{class:'panel'},el('div',{class:'status-banner incomplete'},label('No verdict issued'),el('h2',{},'A question before a conclusion.'),el('p',{},'The supplied evidence does not support a complete check.')),el('ul',{class:'questions'},a.proposal.questions.map(q=>el('li',{},q))),el('div',{class:'rule-actions'},el('p',{},'Keep these inputs and add the missing documentation or mapping in a linked revision.'),btn('Add missing evidence',()=>{location.hash='revise/'+a.id}, 'secondary')));
 else if(a.state==='review')content=ruleCard(a);
 else content=el('div',{},resultCard(a),el('details',{class:'panel'},el('summary',{},'Review the accepted rule & citations'),el('div',{class:'detail-content'},ruleCard(a,false))));
 main.replaceChildren(...(!config.legacy_audits_enabled?[el('p',{class:'revision-banner'},'Historical audit · read-only. This record uses the earlier evidence format and does not establish current-workflow confirmation or fresh replay.')]:[]),el('div',{class:'audit-heading'},el('div',{},el('div',{class:'eyebrow'},'Audit / '+a.id.slice(0,8)),el('h1',{},a.title)),actions),...(a.revision?[el('div',{class:'revision-banner'},label(a.revision.kind==='rule'?'Researcher rule revision':'Input revision'),el('p',{},a.revision.note),el('div',{class:'actions'},el('a',{href:'#audit/'+a.revision.parent_id},'Open original audit'),el('button',{id:'compare-revision',type:'button',class:'secondary',onclick:()=>showComparison(a)},'Compare with original')),a.revision.kind==='rule'?el('p',{class:'hint'},'Inference provenance and model notes are inherited from the original proposal. This revision made no model call.'):null)]:[]),el('div',{class:'claim-box'},label('The research claim'),el('p',{},a.claim)),flow(a.state,loading),el('div',{class:'error',id:'audit-error',role:'alert',hidden:'true'}),el('div',{class:'audit-grid'},el('div',{class:'main-column'},content),sidePanel(a)));
 history().catch(e=>toast(e.message));
}
function renderRuleEditor(a){
 const rule=structuredClone(a.reviewed_rule||a.proposal.rule);
 const tables=a.files.filter(f=>f.columns),docs=a.files.filter(f=>f.text!==undefined);
 const controls={};
 function textControl(key,title,value,multiline=false){
  const input=el(multiline?'textarea':'input',{id:'edit-'+key,required:'true',maxlength:multiline?'1000':'100',...(multiline?{rows:'3'}:{type:'text'})});input.value=value;controls[key]=input;
  return el('div',{class:'field'},el('label',{for:input.id},title),input);
 }
 function selectControl(key,title,options,value){
  const input=el('select',{id:'edit-'+key,required:key==='mapping_file'?null:'true'});controls[key]=input;
  for(const [v,t] of options)input.append(el('option',{value:v},t));input.value=value??'';
  return el('div',{class:'field'},el('label',{for:input.id},title),input);
 }
 const tableOptions=tables.map(f=>[f.name,f.name]);
 const fields=el('div',{class:'revision-fields'},
  textControl('unit','Independent entity',rule.unit),
  selectControl('split_file','Split file',tableOptions,rule.split_file),
  selectControl('sample_column','Sample ID column',[],''),
  selectControl('partition_column','Partition column',[],''),
  selectControl('mapping_file','Entity mapping file',[['','Same as split file'],...tableOptions],rule.mapping_file),
  selectControl('mapping_sample_column','Mapping sample ID column',[],''),
  selectControl('entity_column','Entity ID column',[],''),
  textControl('train_values','Training labels · one per line',rule.train_values.join('\n'),true),
  textControl('test_values','Evaluation labels · one per line',rule.test_values.join('\n'),true));
 function updateColumns(initial=false){
  for(const key of ['sample_column','partition_column','mapping_sample_column','entity_column']){
   const file=['sample_column','partition_column'].includes(key)?controls.split_file.value:(controls.mapping_file.value||controls.split_file.value);
   const cols=tables.find(f=>f.name===file)?.columns||[];const input=controls[key];const previous=initial?(rule[key]||rule.sample_column):input.value;
   input.replaceChildren(...cols.map(c=>el('option',{value:c},c)));if(cols.includes(previous))input.value=previous;
  }
 }
 updateColumns(true);controls.split_file.addEventListener('change',()=>updateColumns());controls.mapping_file.addEventListener('change',()=>updateColumns());
 const quoteFields=el('div',{class:'revision-citations'});let quoteCount=0;
 function addCitation(c={file:docs[0]?.name,quote:''}){
  if(quoteFields.children.length>=6){toast('Use at most six citations.');return}
  const n=++quoteCount,file=el('select',{id:'quote-file-'+n,required:'true'},...docs.map(d=>el('option',{value:d.name},d.name)));file.value=c.file;
  const quote=el('textarea',{id:'quote-text-'+n,required:'true',minlength:'12',maxlength:'1000',rows:'3'});quote.value=c.quote;
  const row=el('div',{class:'citation-editor'},el('label',{for:file.id},'Source document'),file,el('label',{for:quote.id},'Exact supporting quote'),quote,btn('Remove citation',()=>row.remove(),'text-button'));quoteFields.append(row);
 }
 rule.citations.forEach(addCitation);
 const reason=textControl('note','Why are you changing this rule?','',true);controls.note.minLength=8;
 const error=el('div',{id:'form-error',class:'error',role:'alert',hidden:'true'});
 const saveButton=el('button',{class:'primary',type:'submit'},'Save revision for review');
 const cancel=btn('Cancel',()=>renderAudit(a),'secondary');
 const form=el('form',{class:'rule-editor',onsubmit:async event=>{
  event.preventDefault();if(busy)return;error.hidden=true;
  const revised={...rule,unit:controls.unit.value.trim(),split_file:controls.split_file.value,sample_column:controls.sample_column.value,partition_column:controls.partition_column.value,mapping_file:controls.mapping_file.value||null,mapping_sample_column:controls.mapping_sample_column.value,entity_column:controls.entity_column.value,
   train_values:controls.train_values.value.split('\n').map(v=>v.trim()).filter(Boolean),test_values:controls.test_values.value.split('\n').map(v=>v.trim()).filter(Boolean),
   citations:[...quoteFields.children].map(row=>({file:row.querySelector('select').value,quote:row.querySelector('textarea').value})),explanation:'Researcher revised the executable rule; see the revision note.',limitations:[]};
  if(!revised.citations.length){showError(new Error('Add at least one supporting citation.'));return}
  busy=true;saveButton.disabled=true;cancel.disabled=true;saveButton.textContent='Validating revision…';
  try{const saved=await api('/audits/'+a.id+'/with-rule','POST',{rule:revised,note:controls.note.value.trim()});window.history.pushState(null,'','#audit/'+saved.id);renderAudit(saved)}catch(e){showError(e)}finally{busy=false;saveButton.disabled=false;cancel.disabled=false;saveButton.textContent='Save revision for review';}
 }},el('div',{class:'form-body'},fields,el('h3',{},'Evidence for your correction'),el('p',{class:'hint'},'Quotes must appear in a supplied document. Add or replace documentation through Revise inputs if needed.'),quoteFields,btn('Add citation',()=>addCitation(),'secondary'),el('details',{},el('summary',{},'Read source documents'),...docs.map(d=>el('div',{class:'detail-content'},el('h3',{},d.name),el('pre',{class:'source-text'},d.text)))),reason,error),el('div',{class:'form-footer'},el('p',{class:'disclosure'},'Saving creates a separate revision. You will review it before running the check. Unsaved edits are discarded if you leave this form.'),el('div',{class:'actions'},cancel,saveButton)));
 $('#page-name').textContent='Revise rule';main.replaceChildren(el('div',{class:'eyebrow'},'Researcher correction'),el('h1',{},'Make the rule explicit.'),el('section',{class:'panel'},form));controls.unit.focus();
}
async function showComparison(a){
 const button=$('#compare-revision');if(button){button.disabled=true;button.textContent='Loading changes…'}
 try{
  const data=await api('/audits/'+a.id+'/comparison');if(current?.id!==a.id)return;
  const fieldNames={unit:'Entity name',split_file:'Split file',sample_column:'Sample ID',partition_column:'Partition column',mapping_file:'Mapping file',mapping_sample_column:'Mapping sample ID',entity_column:'Entity ID',train_values:'Training labels',test_values:'Evaluation labels',citations:'Supporting citations',status:'Result',shared_entities:'Shared entities',affected_test_rows:'Affected evaluation rows',test_rows:'Evaluation rows',mapping_coverage_percent:'Mapping coverage (%)',missing_count:'Unmapped rows'};
  const value=v=>v===null||v===undefined?'Not available':Array.isArray(v)?v.map(x=>typeof x==='object'?x.file+': “'+x.quote+'”':x).join('\n'):String(v);
  const table=(rows)=>el('div',{class:'table-wrap comparison-table'},el('table',{},el('thead',{},el('tr',{},el('th',{},'Measure'),el('th',{},'Original'),el('th',{},'Revision'))),el('tbody',{},...rows.map(r=>el('tr',{},el('th',{scope:'row'},fieldNames[r.field]||r.field),el('td',{},value(r.before)),el('td',{},value(r.after)))))));
  const panel=el('section',{class:'panel comparison-panel'},el('div',{class:'panel-head'},el('h2',{},'What changed'),btn('Close comparison',()=>{panel.remove();button.focus()},'text-button')),
   el('div',{class:'detail-content'},el('p',{},'Original: '+data.parent.title),el('p',{},'Revision: '+data.child.title),el('p',{class:'limitation'},'This comparison describes recorded checks. It does not measure a change in model accuracy or establish the cause of any difference.'),
    !data.both_complete?el('p',{class:'comparison-notice'},'One or both audits has no completed result. Not available means no measurement, not zero.'):null,
    data.contract_changed?el('p',{class:'comparison-notice'},'The executable rule changed. These findings answer different scoped checks.'):null,
    data.rule_status==='added'?el('p',{class:'comparison-notice'},'A supported rule is now available. The original audit had no supported rule.'):null,
    el('h3',{},'Findings'),table(data.metrics),el('h3',{},'Research claim'),data.claim.before===data.claim.after?el('p',{},'Unchanged.'):table([{field:'Claim',...data.claim}]),
    el('h3',{},'Files'),el('ul',{class:'comparison-files'},...data.files.map(f=>el('li',{},el('b',{},f.name),el('span',{},f.change)))),
    el('h3',{},'Rule and evidence'),data.rule_changes.length?table(data.rule_changes):el('p',{},'No rule or citation changes.')));
  $('#revision-comparison')?.remove();panel.id='revision-comparison';$('.revision-banner').after(panel);panel.setAttribute('tabindex','-1');panel.focus();
 }catch(e){showError(e)}finally{if(button){button.disabled=false;button.textContent='Compare with original'}}
}
async function proposeCurrent(){if(busy||!current)return;busy=true;const id=current.id;renderAudit(current,true);try{const data=await api('/audits/'+id+'/propose','POST',{});renderAudit(data)}catch(e){renderAudit(current);showError(e)}finally{busy=false;if(location.hash!=='#audit/'+id)await route()}}
async function runCurrent(){if(busy)return;busy=true;const remote=!!$('#remote-consent')?.checked;const button=$('.rule-actions .primary');if(button){button.disabled=true;button.textContent='Checking all rows…'}try{renderAudit(await api('/audits/'+current.id+'/execute','POST',{remote,confirm_upload:remote}))}catch(e){showError(e);if(button){button.disabled=false;button.textContent='Accept rule & run check ↗'}}finally{busy=false}}
async function deleteCurrent(){if(busy)return;if(!confirm('Delete this audit and its local input record? Export any evidence you want to keep first.'))return;try{await api('/audits/'+current.id,'DELETE');navigate();await history()}catch(e){showError(e)}}
async function route(){const routeVersion=++generation;if(await investigations.route(location.hash))return;if(routeVersion!==generation)return;const revision=location.hash.match(/^#revise\/([a-f0-9]{24})$/);if(revision&&!config.legacy_audits_enabled){await investigations.route('#investigate');toast('Historical audits are read-only. Create a new split receipt.');return}if(revision){const g=++generation;try{const seed=await api('/audits/'+revision[1]+'/inputs');if(g===generation){renderNew(seed,revision[1]);$('#title').focus()}}catch(e){if(g===generation){renderNew();toast(e.message)}}return}const match=location.hash.match(/^#audit\/([a-f0-9]{24})$/);const g=++generation;if(match){try{const a=await api('/audits/'+match[1]);if(g===generation)renderAudit(a)}catch(e){if(g===generation){renderNew();toast(e.message)}}}else if(config.legacy_audits_enabled)renderNew();else await investigations.route('#investigate')}
const investigations=createInvestigations({el,btn,api,main,label,toast});
$('#new-audit')?.addEventListener('click',()=>navigate());window.addEventListener('hashchange',()=>{if(!busy)route()});
$('.brand').addEventListener('click',e=>{e.preventDefault();navigate()});
document.addEventListener('keydown',e=>{if(e.key.toLowerCase()==='n'&&!e.ctrlKey&&!e.metaKey&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName)){e.preventDefault();navigate()}});
try{config=await api('/session');$('#connection').textContent=config.configured?'Nebius key configured':'Add a Nebius key';await route();await history()}catch(e){main.replaceChildren(el('div',{class:'error'},e.message),btn('Retry connection',()=>location.reload()));$('#connection').textContent='Connection unavailable'}
