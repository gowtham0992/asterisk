import {heroFigure,plural} from './ladder-figure.mjs?v=ladder-1';
import {ladderView,referencedFiles,matchFiles,confirmable,isDocumentation,tableColumns,describeExpression,citedLines,receipt,tableRows,deriveValue,guessPartition,splitColumn,buildSpec,lineCount} from './ladder-view.mjs?v=release-review-1';
const $=(s,root=document)=>root.querySelector(s);
import {el,kicker,renderLadder,renderReviewContext} from './ladder-render.mjs?v=partition-review-1';
const EXAMPLE=['spec.json','split.csv','subjects.csv','README.md'];

async function gallery(){
 const list=$('#gallery-list'),panel=$('#gallery-panel'),cache=new Map();
 let entries;
 try{const response=await fetch('/static/ladders/index.json');if(!response.ok)throw new Error();entries=(await response.json()).ladders}
 catch{list.replaceChildren(el('p',{class:'gallery-loading'},'The benchmark ladders could not be loaded. Rebuild them with scripts/build_public_ladders.py.'));return}
 const tones={violation:'shared',held_out_pending_confirmation:'held'};
 const words={violation:'Not held out',held_out_pending_confirmation:'No shared values · confirm meaning',not_established:'Not established',insufficient:'Insufficient'};
 const buttons=entries.map((entry,i)=>el('button',{class:'gallery-item',type:'button',role:'tab',id:`tab-${entry.key}`,'aria-controls':'gallery-panel','aria-selected':'false',tabindex:'-1',onclick:()=>select(i,false,true),onkeydown:event=>{const step={ArrowDown:1,ArrowUp:-1}[event.key];if(step){event.preventDefault();select((i+step+entries.length)%entries.length,true,true)}}},
  el('span',{class:`tone-chip tone-${tones[entry.finding]||'unknown'}`},words[entry.finding]||entry.finding),el('strong',{},entry.title),el('span',{class:'gallery-line'},entry.headline.replace(/Held out:/g,'No shared values:'))));
 list.replaceChildren(...buttons);
 async function select(i,focus=false,chosen=false){
  buttons.forEach((b,j)=>{b.setAttribute('aria-selected',String(i===j));b.tabIndex=i===j?0:-1});if(focus)buttons[i].focus();
  panel.setAttribute('aria-labelledby',buttons[i].id);
  const key=entries[i].key;
  try{if(!cache.has(key)){const response=await fetch(`/static/ladders/${encodeURIComponent(key)}.json`);if(!response.ok)throw new Error();cache.set(key,await response.json())}
   if(buttons[i].getAttribute('aria-selected')==='true')renderLadder(panel,cache.get(key));}
  catch{panel.replaceChildren(el('p',{class:'gallery-loading'},'This ladder could not be loaded.'))}
  if(chosen)history.replaceState(null,'',`#${key}`);
 }
 const fromHash=()=>entries.findIndex(e=>`#${e.key}`===location.hash);
 select(Math.max(0,fromHash()));
 window.addEventListener('hashchange',()=>{const i=fromHash();if(i>=0)select(i)});
}

function checker(){
 const form=$('#check-form'),specInput=$('#spec-file'),dataInput=$('#data-files'),run=$('#check-run'),error=$('#check-error'),panel=$('#check-panel');
 let spec=null,picked=[];
 const say=(node,text,state='')=>{node.textContent=text;node.className='check-hint'+(state?` is-${state}`:'')};
 const fail=text=>{error.textContent=text;error.hidden=false};
 function refresh(){
  if(!spec){run.disabled=true;say($('#files-status'),picked.length?`${picked.length} file(s) chosen. Choose a spec to see which it needs.`:'The spec lists which files it needs.');return}
  const {files,missing,ambiguous}=matchFiles(spec,picked);
  if(ambiguous.length)say($('#files-status'),`More than one spec file matches the same chosen file: ${ambiguous.join(', ')}. Rename the files so each name is exact.`,'missing');
  else if(missing.length)say($('#files-status'),`Still needed: ${missing.join(', ')}.`,'missing');
  else say($('#files-status'),`Ready: ${files.map(f=>f.name).join(', ')}.`,'ready');
  run.disabled=!!(missing.length||ambiguous.length);
 }
 async function useSpec(file){
  spec=null;error.hidden=true;
  try{const parsed=JSON.parse(await file.text());if(!parsed||typeof parsed!=='object'||!Array.isArray(parsed.levels))throw new Error();spec=parsed;
   say($('#spec-status'),`${file.name} · claim at ${parsed.claim?.level||'?'} · ${parsed.levels.length} levels · needs ${referencedFiles(parsed).length} files.`,'ready')}
  catch{say($('#spec-status'),`${file.name} is not a ladder spec (asterisk-ladder/1 JSON).`,'missing')}
  refresh();
 }
 specInput.addEventListener('change',()=>{if(specInput.files[0])useSpec(specInput.files[0])});
 dataInput.addEventListener('change',()=>{picked=[...dataInput.files];error.hidden=true;refresh()});
 async function loadExample(clean){
  try{const folder=clean?'ladder-example-clean':'ladder-example';
   const texts=await Promise.all(EXAMPLE.map(async name=>{const r=await fetch(`/static/${folder}/${name}`);if(!r.ok)throw new Error();return new File([await r.text()],name,{type:'text/plain'})}));
   specInput.value='';dataInput.value='';picked=texts.slice(1);await useSpec(texts[0]);
   say($('#spec-status'),`Fictional ${clean?'subject-disjoint':'overlapping-subject'} example loaded. This is a supplied specification, not a model proposal.`,'ready');}
  catch{fail('The synthetic example could not be loaded.')}
 }
 $('#load-example').addEventListener('click',()=>loadExample(false));
 $('#load-clean-example').addEventListener('click',()=>loadExample(true));

 async function measure(body){
  const response=await fetch('/api/ladder',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-Asterisk-Request':'1'},body:JSON.stringify(body)});
  const data=await response.json().catch(()=>({detail:'The server did not respond. Check the connection and retry.'}));
  if(response.status===404)throw new Error('This Asterisk server was started before ladder checks existed. Restart it, then measure again.');
  if(!response.ok)throw new Error(typeof data.detail==='string'?data.detail:'Check the spec and files, then retry.');
  return data;
 }
 form.addEventListener('submit',async event=>{
  event.preventDefault();if(!spec)return;
  const {files,missing}=matchFiles(spec,picked);if(missing.length)return refresh();
  run.disabled=true;run.textContent='Measuring…';error.hidden=true;
  try{
   await fetch('/api/session',{credentials:'same-origin'});
   const body={spec,files:await Promise.all(files.map(async f=>({name:f.name,content:await f.file.text()})))};
   const show=async confirmed=>{
    const data=await measure({...body,confirmed});
    renderLadder(panel,data,level=>show([...confirmed,level]).catch(e=>fail(e.message)));
    const save=el('button',{class:'secondary',type:'button'},'Save to workspace');
    save.addEventListener('click',async()=>{
     save.disabled=true;save.textContent='Saving…';
     try{const record=await post('/api/ladder/receipts',{...body,confirmed});location.href='/#ladder/'+record.id}
     catch(e){fail(e.message);save.disabled=false;save.textContent='Save to workspace'}
    });
    panel.append(el('div',{class:'chain-actions'},save));
   };
   await show([]);panel.scrollIntoView({behavior:'smooth',block:'start'});
  }catch(e){fail(e.message)}
  finally{run.textContent='Measure on server';refresh()}
 });
}

// Sponsor marks where their services do the work: NVIDIA Nemotron proposes, Nebius runs it.
function sponsors(nvidia,nebius){
 return el('span',{class:'sponsor-line'},nvidia&&el('img',{src:'/static/brand/nvidia.svg',alt:'NVIDIA',width:'62',height:'18'}),nebius&&el('img',{src:'/static/brand/nebius.svg',alt:'Nebius',width:'58',height:'16'}));
}

async function post(path,body){
 await fetch('/api/session',{credentials:'same-origin'});
 const response=await fetch(path,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-Asterisk-Request':'1'},body:JSON.stringify(body)});
 const data=await response.json().catch(()=>({detail:'The server did not respond. Check the connection and retry.'}));
 if(response.status===404)throw new Error('This Asterisk server was started before this step existed. Restart it, then try again.');
 if(!response.ok)throw new Error(typeof data.detail==='string'?data.detail:'The request was not accepted. Check the inputs and retry.');
 return data;
}

function proposer(){
 const state={files:{},docs:new Set(),share:new Set(),confirmed:[],proposal:null,spec:null,result:null,replay:null};
 const claimInput=$('#propose-claim'),fileInput=$('#propose-files'),model=$('#propose-model'),previewButton=$('#propose-preview');
 const error=$('#propose-error'),inventory=$('#propose-inventory');
 const panels={payload:$('#propose-payload'),result:$('#propose-result'),ladder:$('#propose-ladder'),replay:$('#propose-replay')};
 const steps=['input','preview','propose','measure','replay','receipt'];
 const step=(active)=>steps.forEach((name,i)=>{const node=$('#step-'+name);node.className=i<steps.indexOf(active)?'is-done':i===steps.indexOf(active)?'is-active':''});
 const fail=text=>{error.textContent=text;error.hidden=false};
 const reset=(from)=>{const order=['payload','result','ladder','replay'];order.slice(order.indexOf(from)).forEach(k=>{panels[k].hidden=true;panels[k].replaceChildren()})};
 const body=()=>({claim:claimInput.value.trim(),files:Object.entries(state.files).map(([name,content])=>({name,content})),
  documentation:[...state.docs],share_examples:[...state.share].map(k=>JSON.parse(k)),model:model.value});
 const tableFiles=()=>Object.keys(state.files).filter(n=>!state.docs.has(n));
 function ready(){previewButton.disabled=!(claimInput.value.trim().length>=3&&state.docs.size>0&&tableFiles().length>0);$('#propose-manual').disabled=previewButton.disabled}
 $('#propose-manual').addEventListener('click',()=>builder());
 function renderInventory(){
  inventory.replaceChildren(el('p',{},'Mark which files are documentation. For tables, tick only identifier columns whose example values may be sent; every other column is sent as counts only.'),
   ...Object.keys(state.files).map(name=>{
    const doc=el('input',{type:'checkbox',id:'doc-'+name,...(state.docs.has(name)?{checked:'true'}:{})});
    doc.addEventListener('change',()=>{doc.checked?state.docs.add(name):state.docs.delete(name);reset('payload');step('input');renderInventory();ready()});
    const cols=state.docs.has(name)?null:el('div',{class:'inventory-columns'},tableColumns(name,state.files[name]).slice(0,60).map(col=>{
     const key=JSON.stringify([name,col]),box=el('input',{type:'checkbox',...(state.share.has(key)?{checked:'true'}:{})});
     box.addEventListener('change',()=>{box.checked?state.share.add(key):state.share.delete(key);reset('payload');step('input')});
     return el('label',{},box,' ',col);}));
    return el('div',{class:'inventory-file'},el('strong',{},name),el('label',{for:'doc-'+name},doc,' documentation'),cols);
   }));
  inventory.hidden=false;
 }
 async function useFiles(list){
  state.files={};state.docs=new Set();state.share=new Set();reset('payload');step('input');error.hidden=true;
  for(const file of list){if(file.size>16_000_000){fail(`${file.name} is larger than 16 MB.`);return}state.files[file.name]=await file.text();if(isDocumentation(file.name))state.docs.add(file.name)}
  renderInventory();ready();
  const names=Object.keys(state.files);
  $('#propose-drop-hint').textContent=names.length?`${names.length} file${names.length>1?'s':''}: ${names.join(', ')}`:'Preview uploads files to the Asterisk server; sending to Nebius is a separate step.';
  drop.classList.toggle('has-files',names.length>0);
 }
 fileInput.addEventListener('change',()=>useFiles([...fileInput.files]));
 const drop=$('#propose-drop');
 ['dragenter','dragover'].forEach(t=>drop.addEventListener(t,e=>{e.preventDefault();drop.classList.add('is-over')}));
 ['dragleave','drop'].forEach(t=>drop.addEventListener(t,e=>{e.preventDefault();drop.classList.remove('is-over')}));
 drop.addEventListener('drop',e=>{if(e.dataTransfer?.files?.length)useFiles([...e.dataTransfer.files])});
 claimInput.addEventListener('input',()=>{reset('payload');step('input');ready()});
 model.addEventListener('change',()=>{reset('payload');step('input')});
 $('#propose-example').addEventListener('click',async()=>{
  try{const names=['README.md','train.json','test.json'];
   const files=await Promise.all(names.map(async n=>{const r=await fetch('/static/ladder-example-propose/'+n);if(!r.ok)throw new Error();return new File([await r.text()],n)}));
   fileInput.value='';claimInput.value='No test patient appears in the training data.';await useFiles(files);
   ['train.json','test.json'].forEach(n=>state.share.add(JSON.stringify([n,'slide'])));renderInventory();ready();
  }catch{fail('The synthetic example could not be loaded.')}
 });
 previewButton.addEventListener('click',async()=>{
  error.hidden=true;reset('payload');
  try{
   const data=await post('/api/ladder/preview',body());
   const user=JSON.parse(data.messages[1].content);
   const send=el('button',{class:'primary',type:'button'},`Send to ${data.model_name} via Nebius Token Factory`);
   send.addEventListener('click',()=>propose(send));
   panels.payload.replaceChildren(kicker('Step 2 · Exactly what would be sent'),el('h3',{},'Not yet sent to Nebius. Your files are on the Asterisk server.'),
    el('div',{class:'chain-meta'},el('span',{},data.provider),el('span',{},data.model_name),el('span',{},`${data.characters.toLocaleString('en-US')} characters`),el('span',{},'SHA-256 '+data.payload_sha256.slice(0,16)+'…')),
    el('p',{},`Documentation text (${Object.keys(user.documentation).join(', ')}), column names with counts, and example values only for the ${state.share.size} column(s) you ticked. Other cell values are held by this Asterisk server and are not sent to the model. A Sandbox replay sends the supplied files separately, only when you request it.`),
    el('details',{},el('summary',{},'Show the full request'),el('pre',{},JSON.stringify(user,null,1))),
    el('div',{class:'chain-actions'},send));
   panels.payload.hidden=false;step('preview');
  }catch(e){fail(e.message)}
 });
 async function propose(button){
  button.disabled=true;button.textContent='Nemotron is reading the documentation…';error.hidden=true;reset('result');
  try{
   const data=await post('/api/ladder/propose',body());state.proposal=data;
   if(data.proposal_record_error)fail(data.proposal_record_error);
   const p=data.proposal,meta=el('div',{class:'chain-meta'},el('span',{},data.provider),el('span',{},data.model_name),el('span',{},`${data.seconds} s`),el('span',{},`${data.total_tokens.toLocaleString('en-US')} tokens`),data.attempts.length>1&&el('span',{},'repaired once after validation'));
   if(p.status==='abstain'){
    const define=el('button',{class:'primary',type:'button'},'Define the unit yourself');define.addEventListener('click',()=>builder());
    panels.result.replaceChildren(kicker('Step 3 · Nemotron abstained'),el('h3',{},'Nemotron would not guess this unit.'),meta,el('p',{},p.missing),
     el('p',{},'If the documentation or your own knowledge defines it, say how. Asterisk validates and measures your definition exactly as it would a model proposal, and the receipt records it as user-supplied or as an edit of the recorded proposal; authorship is not verified.'),
     el('div',{class:'chain-actions'},define));
   }else{
    state.spec=p.spec;
    const review=await post('/api/ladder/review',{spec:state.spec,files:body().files,confirmed:[]});
    const measureButton=el('button',{class:'primary',type:'button'},'Measure on server');measureButton.addEventListener('click',()=>measure([]));
    panels.result.replaceChildren(el('div',{class:'panel-head'},kicker('Step 3 · Proposed ladder · validated and dry-run'),sponsors(true,true)),el('h3',{},`Claim bound to "${p.spec.claim.level}"`),meta,
     el('ol',{class:'proposal-levels'},p.spec.levels.map(l=>el('li',{class:l.name===p.spec.claim.level?'is-claim':''},el('b',{},l.name),l.kind+(l.name===p.spec.claim.level?' · the claim level':''),el('em',{},describeExpression(l.expression)+(l.by_source?` (per-file overrides for ${Object.keys(l.by_source).join(', ')})`:'')+(l.missing?' · blanks counted as unmapped':''))))),
     renderReviewContext(review),
     ...citedLines(p.spec.citations,state.files).map(c=>el('blockquote',{class:'citation'},c.text,el('small',{},`${c.file}, lines ${c.start}–${c.end}`))),
     el('div',{class:'chain-actions'},measureButton,editButton()));
   }
   panels.result.hidden=false;step('propose');button.textContent='Sent';
  }catch(e){fail(e.message);button.disabled=false;button.textContent='Send again'}
 }
 function editButton(){const b=el('button',{class:'text-button',type:'button'},'Define it differently');b.addEventListener('click',()=>builder());return b}
 function builder(){
  try{
  reset('ladder');step('propose');
  const tables=tableFiles(),docs=[...state.docs];
  const cols=Object.fromEntries(tables.map(n=>[n,tableColumns(n,state.files[n])]));
  const rows=Object.fromEntries(tables.map(n=>[n,tableRows(n,state.files[n])]));
  for(const n of tables){if(rows[n].length>100000)throw Error('The builder supports at most 100,000 rows per table.');const split=splitColumn(cols[n]);if(split&&new Set(rows[n].map(r=>String(r[split]))).size>12)throw Error('The guided builder supports at most 12 partition labels. Use an explicit JSON specification for this table.');}
  const select=(options,value)=>{const s=el('select',{},options.map(o=>el('option',{value:o,...(o===value?{selected:'true'}:{})},o)));return s};
  const sourceRows=tables.map(n=>{
   const split=splitColumn(cols[n]);
   const role=select(['observations','lookup table only','ignore'],'observations');
   const sample=select(cols[n],cols[n].find(c=>c!==split)||cols[n][0]);
   const whole=select(['train','test'],/test|eval/i.test(n)?'test':'train');
   const mapping=split?[...new Set(rows[n].map(r=>String(r[split])))].slice(0,12).map(raw=>({raw,box:select(['train','test','excluded'],guessPartition(raw))})):[];
   return {name:n,split,role,sample,whole,mapping};
  });
  const first=sourceRows[0];
  const unitName=el('input',{type:'text',value:(claimInput.value.match(/\b(patient|subject|person|recording|site|case|lesion|frog|study)\b/i)||['','subject'])[1].toLowerCase(),maxlength:'40'});
  const unitCol=select(cols[first.name],first.sample.value);
  const base=el('input',{type:'checkbox'}),prefix=el('input',{type:'number',min:'0',max:'128',value:'0'});
  const sep=el('input',{type:'text',maxlength:'3',placeholder:'e.g. -',class:'narrow'}),fieldFrom=el('input',{type:'number',min:'1',max:'32',placeholder:'from'}),fieldTo=el('input',{type:'number',min:'1',max:'32',placeholder:'to'});
  const charFrom=el('input',{type:'number',min:'1',max:'512',placeholder:'from'}),charTo=el('input',{type:'number',min:'1',max:'512',placeholder:'to'});
  const lookTable=select(['— none —',...tables],'— none —'),lookKey=el('input',{type:'text',placeholder:'key column'}),lookValue=el('input',{type:'text',placeholder:'value column'});
  const meaning=el('input',{type:'text',maxlength:'400',placeholder:'e.g. Records from the same subject differ in the last digit only.'});
  const docSel=select(['— choose documentation —',...docs],'— choose documentation —'),start=el('input',{type:'number',min:'1',placeholder:'first line'}),end=el('input',{type:'number',min:'1',placeholder:'last line'});
  const preview=el('div',{class:'builder-preview'});
  function unitSpec(){const u={column:unitCol.value,basename:base.checked,prefix:Number(prefix.value)||0,meaning:meaning.value,
    field:sep.value?{separator:sep.value,from:Number(fieldFrom.value)||1,to:Number(fieldTo.value)||Number(fieldFrom.value)||1}:null,
    characters:Number(charFrom.value)?{from:Number(charFrom.value),to:Number(charTo.value)||Number(charFrom.value)}:null};
   if(lookTable.value!=='— none —')u.lookup={file:lookTable.value,key:lookKey.value.trim(),value:lookValue.value.trim()};return u}
  function refresh(){
   const u=unitSpec(),src=sourceRows.find(r=>r.role.value==='observations')||first;
   let lookup=null;
   if(u.lookup&&rows[u.lookup.file])lookup=new Map(rows[u.lookup.file].map(r=>[String(r[u.lookup.key]),String(r[u.lookup.value]??'')]));
   const sample=rows[src.name].slice(0,6).map(r=>{let v=deriveValue(r[u.column],u);if(lookup)v=v===null?null:(lookup.get(v)??null);return [String(r[u.column]??''),v]});
   const groups=new Set(rows[src.name].map(r=>{let v=deriveValue(r[u.column],u);if(lookup)v=v===null?null:(lookup.get(v)??null);return v}).filter(v=>v!==null));
   preview.replaceChildren(el('p',{},`${groups.size.toLocaleString('en-US')} distinct ${unitName.value||'unit'} values across ${rows[src.name].length.toLocaleString('en-US')} rows of ${src.name}`+(groups.size===rows[src.name].length?' — every row is its own unit, so zero overlap would prove nothing.':'.')),
    el('table',{class:'builder-table'},el('tr',{},el('th',{},u.column),el('th',{},unitName.value||'unit')),sample.map(([a,b])=>el('tr',{},el('td',{},a),el('td',{},b??'— none —')))));
  }
  [unitCol,base,prefix,sep,fieldFrom,fieldTo,charFrom,charTo,lookTable,lookKey,lookValue,unitName].forEach(x=>x.addEventListener('input',refresh));
  const use=el('button',{class:'primary',type:'button'},'Use this definition');
  use.addEventListener('click',async()=>{
   use.disabled=true;
   try{
   const sources=sourceRows.filter(r=>r.role.value==='observations').map(r=>({file:r.name,sample:{column:r.sample.value},
    partition:r.split?{column:r.split,map:Object.fromEntries(r.mapping.map(m=>[m.raw,m.box.value]))}:{value:r.whole.value}}));
   if(!sources.length){fail('Choose at least one table of observations.');return}
   if(!docs.includes(docSel.value)||!Number(start.value)||!Number(end.value)){fail('Choose the documentation and line range you reviewed.');return}
   state.spec=buildSpec({claim:claimInput.value.trim(),unitName:unitName.value,sources,unit:unitSpec(),citation:{file:docSel.value,start:start.value,end:end.value}});
   const review=await post('/api/ladder/review',{spec:state.spec,files:body().files,confirmed:[]});
   state.proposal=state.proposal?{...state.proposal,defined_by:'person'}:null;
   const measureButton=el('button',{class:'primary',type:'button'},'Measure on server');measureButton.addEventListener('click',()=>measure([]));
   panels.result.replaceChildren(kicker('Step 3 · Defined by you'),el('h3',{},`Claim bound to "${state.spec.claim.level}"`),
    el('ol',{class:'proposal-levels'},state.spec.levels.map(l=>el('li',{},el('b',{},l.name),l.kind+(l.name===state.spec.claim.level?' · the claim level':''),el('em',{},describeExpression(l.expression))))),
    renderReviewContext(review),
    ...citedLines(state.spec.citations,state.files).map(c=>el('blockquote',{class:'citation'},c.text,el('small',{},`${c.file}, lines ${c.start}–${c.end}`))),
    el('div',{class:'chain-actions'},measureButton,editButton()));
   step('propose');
   }catch(e){fail(e.message)}finally{use.disabled=false}
  });
  panels.result.replaceChildren(kicker('Step 3 · Define the unit yourself'),el('h3',{},'How is the claim\'s unit written in your files?'),
   el('div',{class:'builder'},
    el('fieldset',{},el('legend',{},'Tables'),...sourceRows.map(r=>el('div',{class:'builder-row'},el('strong',{},r.name),el('label',{},'Role ',r.role),el('label',{},'One observation = ',r.sample),
     r.split?el('span',{class:'builder-map'},`Partition by "${r.split}": `,...r.mapping.map(m=>el('label',{},`${m.raw} → `,m.box))):el('label',{},'All rows are ',r.whole)))),
    el('fieldset',{},el('legend',{},'The unit'),el('label',{},'Name ',unitName),el('label',{},'From column ',unitCol),el('label',{},base,' file name after the last /'),
     el('label',{},'split on ',sep,' and keep field ',fieldFrom,' to ',fieldTo),
     el('label',{},'then characters ',charFrom,' to ',charTo),
     el('label',{},'or the first ',prefix,' characters (0 = all)'),
     el('label',{},'then look it up in ',lookTable,lookKey,lookValue),el('label',{class:'wide'},'Why (optional) ',meaning)),
    el('fieldset',{},el('legend',{},'Evidence'),el('label',{},'Documentation ',docSel),el('label',{},'lines ',start,' to ',end)),
    preview),
   el('div',{class:'chain-actions'},use));
  panels.result.hidden=false;refresh();
  }catch(e){fail(e.message)}
 }
 async function measure(confirmed){
  error.hidden=true;reset('ladder');state.confirmed=confirmed;
  try{
   const data=await post('/api/ladder',{spec:state.spec,files:body().files,confirmed});state.result=data;state.replay=null;
   renderLadder(panels.ladder,data,level=>measure([...confirmed,level]));
   const replayButton=el('button',{class:'primary',type:'button'},'Replay in a Nebius Sandbox');replayButton.addEventListener('click',()=>replayChain(replayButton));
   panels.replay.replaceChildren(kicker('Step 5 · Independent recomputation'),el('h3',{},'Recompute in a fresh Nebius Sandbox.'),
    el('p',{},'Sends the engine source, the spec, your confirmations and the files to a disposable python:3.12-slim Sandbox. A matching replay and its inputs are saved privately in your workspace. Do not send personal or sensitive data to the Sandbox beta.'),
    el('div',{class:'chain-actions'},replayButton,saveButton(),downloadButton()));
   panels.replay.hidden=false;step('measure');
  }catch(e){fail(e.message)}
 }
 async function replayChain(button){
  button.disabled=true;button.textContent='Replaying in the Sandbox…';error.hidden=true;
  try{
   const data=await post('/api/ladder/replay',{spec:state.spec,files:body().files,confirmed:state.confirmed,proposal_id:state.proposal?.proposal_id||null});state.replay=data;
   const p=data.provenance;
   panels.replay.replaceChildren(el('div',{class:'panel-head'},kicker('Step 5 · Replayed in a Nebius Sandbox'),sponsors(false,true)),el('h3',{},'Matched the Asterisk server measurement exactly.'),
    el('div',{class:'chain-meta'},el('span',{},p.image),el('span',{},`${Number(p.seconds).toFixed(2)} s in the Sandbox`),el('span',{},'program '+p.program_sha256.slice(0,12)+'…'),el('span',{},'result '+p.result_sha256.slice(0,12)+'…')),
    el('p',{},'Same code, same inputs, independent infrastructure. This is evidence of reproducibility, not tamper-proofing.'),
    data.receipt_error&&el('p',{class:'check-error'},data.receipt_error),
    el('div',{class:'chain-actions'},saveButton(),downloadButton()));
   step('replay');
  }catch(e){fail(e.message);button.disabled=false;button.textContent='Retry the replay'}
 }
 function saveButton(){
  const button=el('button',{class:'secondary',type:'button'},state.replay?.receipt_id?'Open saved receipt':'Save to workspace');
  button.addEventListener('click',async()=>{
   if(state.replay?.receipt_id){location.href='/#ladder/'+state.replay.receipt_id;return}
   button.disabled=true;button.textContent='Saving…';
   try{
    const saved=await post('/api/ladder/receipts',{spec:state.spec,files:body().files,confirmed:state.confirmed,proposal_id:state.proposal?.proposal_id||null});
    location.href='/#ladder/'+saved.id;
   }catch(e){fail(e.message);button.disabled=false;button.textContent='Save to workspace'}
  });return button;
 }
 function downloadButton(){
  const b=el('button',{class:'secondary',type:'button'},'Download receipt (JSON)');
  b.addEventListener('click',()=>{
   const r=receipt({claim:claimInput.value.trim(),proposal:state.proposal,spec:state.spec,result:state.result,replay:state.replay,createdAt:new Date().toISOString()});
   const link=el('a',{href:URL.createObjectURL(new Blob([JSON.stringify(r,null,2)],{type:'application/json'})),download:'asterisk-ladder-receipt.json'});
   document.body.append(link);link.click();link.remove();step('receipt');
  });
  return b;
 }
}


async function experiment(){
 let data;
 try{const r=await fetch('/static/ladders/experiment.json');if(!r.ok)return;data=await r.json()}catch{return}
 const family=label=>/previous v2/.test(label)?null:/^Nemotron 3 Super/.test(label)?'super':/^Nemotron 3 Ultra/.test(label)?'ultra':/^Claude Sonnet/.test(label)?'sonnet':/^Single-column/.test(label)?'script':null;
 const names={super:'Nemotron 3 Super',ultra:'Nemotron 3 Ultra',sonnet:'Claude Sonnet',script:'Single-column script'};
 const notes={super:'ships in Asterisk',ultra:'option',sonnet:'general model, for comparison',script:'specified single-column baseline'};
 const sets=[...new Set(data.rows.map(r=>r.set[0]))];
 const cell={};for(const r of data.rows){const f=family(r.label);if(f)cell[f+r.set[0]]=r}
 const models=['super','ultra','sonnet'].filter(f=>sets.some(x=>cell[f+x]));
 const sum=(fs,key)=>fs.reduce((t,f)=>t+sets.reduce((u,x)=>u+(cell[f+x]?.[key]||0),0),0);
 const cases=sets.reduce((t,x)=>t+(cell['super'+x]?.of||0),0);
 const prev=data.rows.find(r=>/previous v2/.test(r.label)),now=cell['super'+sets.at(-1)];
 $('#experiment-lede').textContent=data.lede;
 const stat=(value,label,cls='')=>el('div',{class:'stat '+cls},el('span',{class:'stat-value'},value),el('span',{class:'stat-label'},label));
 $('#experiment-stats').replaceChildren(
  stat(String(sum(models,'false_reassurance')),`false "held out" from any model, across ${cases} evaluation cases`,'is-good'),
  stat(String(sum(['script'],'false_reassurance')),'false "held out" from a single-column check on the same cases','is-bad'),
  prev&&now?stat(`${prev.correct} → ${now.correct}`,`Nemotron Super on set ${sets.at(-1)} once proposals can say "characters 2–4" or "field 1"`):null);
 const head=el('tr',{},el('th',{scope:'col'},'Proposer'),...sets.map(x=>el('th',{scope:'col',class:'num'},`Set ${x}`)),el('th',{scope:'col',class:'num'},'Correct'),el('th',{scope:'col',class:'num'},'False “held out”'));
 const rows=[...models,'script'].map(f=>el('tr',{class:f==='super'?'is-product':''},
  el('th',{scope:'row'},names[f],el('small',{},notes[f])),
  ...sets.map(x=>{const r=cell[f+x];if(!r)return el('td',{class:'num'},'—');
   return f==='script'?el('td',{class:'num'+(r.false_reassurance?' is-bad':'')},r.false_reassurance?`${r.false_reassurance} false`:'0'):
    el('td',{class:'num'},`${r.correct}/${r.of}`,r.rule==='pass'?el('span',{class:'rule-pass',title:'Passed the pre-registered rule'},' ✓'):null)}),
  el('td',{class:'num total'},f==='script'?'—':`${sum([f],'correct')}/${cases}`),
  el('td',{class:'num total'+(sum([f],'false_reassurance')?' is-bad':'')},String(sum([f],'false_reassurance')))));
 $('#experiment-table').replaceChildren(el('thead',{},head),el('tbody',{},rows));
 $('#experiment-note').textContent=data.note+(prev?` Nemotron Super used the earlier v2 prompt on sets A–C and the current v4 prompt on set D; with v2 it scored ${prev.correct}/${prev.of} there. ✓ marks a pass under the pre-registered rule.`:'');
 $('#experiment').hidden=false;
}

heroFigure($('#hero-rungs'));checker();proposer();
Promise.allSettled([gallery(),experiment()]).then(()=>{
 const id=location.hash.slice(1);if(['propose','benchmarks','experiment'].includes(id))document.getElementById(id)?.scrollIntoView();
});
