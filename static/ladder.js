import {heroFigure,plural} from './ladder-figure.mjs?v=ladder-1';
import {ladderView,referencedFiles,matchFiles,confirmable,isDocumentation,tableColumns,describeExpression,receipt,tableRows,deriveValue,guessPartition,splitColumn,buildSpec,lineCount,readSelectedFiles,partitionLabels,bindingSeed,preserveBinding,bindingPreview,reviewBindingPreview} from './ladder-view.mjs?v=correction-fields-1';
const $=(s,root=document)=>root.querySelector(s);
import {el,kicker,builderField,renderLadder,renderReviewContext,renderBindingQuestions} from './ladder-render.mjs?v=correction-fields-1';
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

async function providerAllowance(){
 try{
  await fetch('/api/session',{credentials:'same-origin'});
  const r=await fetch('/api/ladder/allowance',{credentials:'same-origin'});if(!r.ok)return;
  const data=await r.json();let panel=$('#provider-allowance');
  if(!panel){panel=el('p',{id:'provider-allowance',class:'product-note',role:'status'});$('#propose-form').append(panel)}
  panel.textContent=data.mode==='judge'?`Dedicated judge access · ${data.remaining_calls} reserved calls remain through ${data.expires?new Date(data.expires).toLocaleDateString(): 'the configured expiry'}. No daily session cap. A proposal reserves up to two calls; replay reserves one.`:
   data.remaining_calls===null?'Local installation.':`Live allowance: ${data.remaining_calls} reserved calls remain today. Manual measurement and saved receipts do not use this allowance.`;
 }catch{}
}

async function post(path,body){
 await fetch('/api/session',{credentials:'same-origin'});
 const response=await fetch(path,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-Asterisk-Request':'1'},body:JSON.stringify(body)});
 const data=await response.json().catch(()=>({detail:'The server did not respond. Check the connection and retry.'}));
 if(response.status===404)throw new Error('This Asterisk server was started before this step existed. Restart it, then try again.');
 if(path==='/api/ladder/propose'||path==='/api/ladder/replay')providerAllowance();
 if(!response.ok)throw new Error(typeof data.detail==='string'?data.detail:'The request was not accepted. Check the inputs and retry.');
 return data;
}

function proposer(){
 const state={files:{},docs:new Set(),share:new Set(),confirmed:[],proposal:null,spec:null,result:null,replay:null};
 const claimInput=$('#propose-claim'),fileInput=$('#propose-files'),model=$('#propose-model'),previewButton=$('#propose-preview');
 const error=$('#propose-error'),inventory=$('#propose-inventory');
 const panels={payload:$('#propose-payload'),result:$('#propose-result'),ladder:$('#propose-ladder'),replay:$('#propose-replay')};
 const stageNames=['claim','review','result'];
 const step=active=>{
  const stage=['input','preview'].includes(active)?0:active==='propose'?1:2;
  stageNames.forEach((name,i)=>{const node=$('#journey-'+name);node.className=i<stage?'is-done':i===stage?'is-active':'';if(i===stage)node.setAttribute('aria-current','step');else node.removeAttribute('aria-current')});
  $('#input-disclosure').open=stage===0;
  $('#input-summary').textContent=Object.keys(state.files).length?`${Object.keys(state.files).length} files · ${claimInput.value.trim()||'Add a claim'}`:'Start a new check';
 };
 const fail=text=>{error.textContent=text;error.hidden=false;$('#input-disclosure').open=true;error.scrollIntoView({block:'nearest'})};
 const reset=(from)=>{const order=['payload','result','ladder','replay'];order.slice(order.indexOf(from)).forEach(k=>{panels[k].hidden=true;panels[k].replaceChildren()})};
 let inputRevision=0,workflowRevision=0;
 const invalidate=()=>{inputRevision++;workflowRevision++;state.spec=null;state.proposal=null;state.result=null;state.replay=null;state.confirmed=[];reset('payload');step('input')};
 const body=()=>({claim:claimInput.value.trim(),files:Object.entries(state.files).map(([name,content])=>({name,content})),
  documentation:[...state.docs],share_examples:[...state.share].map(k=>JSON.parse(k)),model:model.value});
 const tableFiles=()=>Object.keys(state.files).filter(n=>!state.docs.has(n));
 function ready(){previewButton.disabled=!(claimInput.value.trim().length>=3&&state.docs.size>0&&tableFiles().length>0);$('#propose-manual').disabled=previewButton.disabled}
 $('#propose-manual').addEventListener('click',()=>builder());
 function renderInventory(){
  inventory.replaceChildren(el('p',{},'Review each file role. Text filename lists are suggested as data; prose is suggested as documentation. You can change either. For data, select only identifier columns whose example values may be sent. No example values are selected automatically.'),
   ...Object.keys(state.files).map(name=>{
    const doc=el('input',{type:'checkbox',id:'doc-'+name,...(state.docs.has(name)?{checked:'true'}:{})});
    doc.addEventListener('change',()=>{doc.checked?state.docs.add(name):state.docs.delete(name);invalidate();renderInventory();ready()});
    const cols=state.docs.has(name)?null:el('div',{class:'inventory-columns'},tableColumns(name,state.files[name]).slice(0,60).map(col=>{
     const key=JSON.stringify([name,col]),box=el('input',{type:'checkbox',...(state.share.has(key)?{checked:'true'}:{})});
     box.addEventListener('change',()=>{box.checked?state.share.add(key):state.share.delete(key);invalidate()});
     return el('label',{},box,' ',col);}));
    const textFile=/\.txt$/i.test(name),lines=textFile?state.files[name].split(/\r?\n/):[];
    return el('div',{class:'inventory-file'},el('strong',{},name),el('label',{for:'doc-'+name},doc,' Use as documentation (full text)'),
     textFile?el('p',{class:'hint'},state.docs.has(name)?'Documentation is sent as numbered text. If this is a split list, uncheck this option to read one data row per line.':'Data list: each nonempty line is a row in the value column. A trailing class label remains part of the line; review the extraction before measuring.'):null,
     textFile?el('details',{},el('summary',{},'Preview text on this device'),el('pre',{tabindex:'0'},lines.slice(0,6).join('\n').slice(0,2400)),el('p',{class:'hint'},'First six lines, up to 2,400 characters. This preview makes no upload.')):null,cols);
   }));
  inventory.hidden=false;
 }
 let selectionGeneration=0;
 async function useFiles(list){
  const generation=++selectionGeneration;
  previewButton.disabled=true;$('#propose-manual').disabled=true;error.hidden=true;
  try{
   const files=await readSelectedFiles(list);
   if(generation!==selectionGeneration)return;
   state.files=files;state.docs=new Set(Object.keys(files).filter(name=>isDocumentation(name,files[name])));state.share=new Set();
   invalidate();renderInventory();ready();
   const names=Object.keys(files);
   $('#propose-drop-hint').textContent=names.length?`${names.length} file${names.length>1?'s':''}: ${names.join(', ')}`:'Preview uploads files to the Asterisk server; sending to Nebius is a separate step.';
   drop.classList.toggle('has-files',names.length>0);
  }catch(e){if(generation===selectionGeneration){fail(e.message);ready()}}
 }
 fileInput.addEventListener('change',()=>useFiles([...fileInput.files]));
 const drop=$('#propose-drop');
 ['dragenter','dragover'].forEach(t=>drop.addEventListener(t,e=>{e.preventDefault();drop.classList.add('is-over')}));
 ['dragleave','drop'].forEach(t=>drop.addEventListener(t,e=>{e.preventDefault();drop.classList.remove('is-over')}));
 drop.addEventListener('drop',e=>{if(e.dataTransfer?.files?.length)useFiles([...e.dataTransfer.files])});
 claimInput.addEventListener('input',()=>{invalidate();ready()});
 model.addEventListener('change',()=>{invalidate()});
 $('#propose-real').addEventListener('click',async()=>{
  const operation=++selectionGeneration;const revision=inputRevision;const button=$('#propose-real');button.disabled=true;
  try{
   await fetch('/api/session',{credentials:'same-origin'});
   const r=await fetch('/api/ladder/benchmark-inputs',{credentials:'same-origin'});const data=await r.json();
   if(!r.ok)throw new Error(data.detail||'Benchmark inputs could not be loaded.');
   if(operation!==selectionGeneration||revision!==inputRevision)return;
   fileInput.value='';claimInput.value=data.claim;
   await useFiles(data.files.map(f=>new File([f.content],f.name)));
   ['train.json','test.json'].forEach(n=>state.share.add(JSON.stringify([n,'image'])));renderInventory();ready();
   $('#propose-drop-hint').textContent=data.notice+' Source rows: '+data.provenance['train.json'].rows+' training, '+data.provenance['test.json'].rows+' evaluation. Clinical conversations and question IDs excluded.';
  }catch(e){if(operation===selectionGeneration)fail(e.message)}finally{button.disabled=false}
 });
 $('#propose-example').addEventListener('click',async()=>{
  try{const names=['README.md','train.json','test.json'];
   const files=await Promise.all(names.map(async n=>{const r=await fetch('/static/ladder-example-propose/'+n);if(!r.ok)throw new Error();return new File([await r.text()],n)}));
   fileInput.value='';claimInput.value='No test patient appears in the training data.';await useFiles(files);
   ['train.json','test.json'].forEach(n=>state.share.add(JSON.stringify([n,'slide'])));renderInventory();ready();
  }catch{fail('The synthetic example could not be loaded.')}
 });
 previewButton.addEventListener('click',async()=>{
  error.hidden=true;reset('payload');const revision=inputRevision,operation=++workflowRevision,request=body();previewButton.disabled=true;
  try{
   const data=await post('/api/ladder/preview',request);if(revision!==inputRevision||operation!==workflowRevision)return;
   const user=JSON.parse(data.messages[1].content);
   const send=el('button',{class:'primary',type:'button'},`Send to ${data.model_name} via Nebius Token Factory`);
   send.addEventListener('click',()=>propose(send));
   panels.payload.replaceChildren(kicker('Define · Review the outbound request'),el('h3',{},'Not yet sent to Nebius. Your files are on the Asterisk server.'),
    el('div',{class:'chain-meta'},el('span',{},data.provider),el('span',{},data.model_name),el('span',{},`${data.characters.toLocaleString('en-US')} characters`),el('span',{},'SHA-256 '+data.payload_sha256.slice(0,16)+'…')),
    el('p',{},`Documentation text (${Object.keys(user.documentation).join(', ')}), column names with counts, and example values only for the ${state.share.size} column(s) you ticked. Other cell values are held by this Asterisk server and are not sent to the model. A Sandbox replay sends the supplied files separately, only when you request it.`),
    el('details',{},el('summary',{},'Show the full request'),el('pre',{},JSON.stringify(user,null,1))),
    el('div',{class:'chain-actions'},send));
   panels.payload.hidden=false;step('preview');
  }catch(e){if(revision===inputRevision&&operation===workflowRevision)fail(e.message)}finally{ready()}
 });
 async function propose(button){
  const revision=inputRevision,operation=++workflowRevision,request=body();
  button.disabled=true;button.textContent='Nemotron is reading the documentation…';error.hidden=true;reset('result');
  try{
   const data=await post('/api/ladder/propose',request);if(revision!==inputRevision||operation!==workflowRevision)return;state.proposal=data;
   if(data.proposal_record_error)fail(data.proposal_record_error);
   panels.payload.hidden=true;const p=data.proposal,meta=el('div',{class:'chain-meta'},el('span',{},data.provider),el('span',{},data.model_name),el('span',{},`${data.seconds} s`),el('span',{},`${data.total_tokens.toLocaleString('en-US')} tokens`),data.attempts.length>1&&el('span',{},'repaired once after validation'));
   if(p.status==='abstain'){
    const define=el('button',{class:'primary',type:'button'},'Define the unit yourself');define.addEventListener('click',()=>builder());
    panels.result.replaceChildren(kicker('Review · Nemotron abstained'),el('h3',{},'Nemotron would not guess this unit.'),meta,el('p',{},p.missing),
     el('p',{},'If the documentation or your own knowledge defines it, say how. Asterisk validates and measures your definition exactly as it would a model proposal, and the receipt records it as user-supplied or as an edit of the recorded proposal; authorship is not verified.'),
     el('div',{class:'chain-actions'},define));
   }else{
    state.spec=p.spec;
    const review=await post('/api/ladder/review',{spec:state.spec,files:request.files,confirmed:[],documentation:[...state.docs]});if(revision!==inputRevision||operation!==workflowRevision)return;
    const measureButton=el('button',{class:'primary',type:'button'},'Measure on server');measureButton.addEventListener('click',()=>measure([]));
    panels.result.replaceChildren(el('div',{class:'panel-head'},kicker('Review · Proposed ladder · validated and dry-run'),sponsors(true,true)),el('h3',{},`Claim bound to "${p.spec.claim.level}"`),meta,
     el('ol',{class:'proposal-levels'},p.spec.levels.map(l=>el('li',{class:l.name===p.spec.claim.level?'is-claim':''},el('b',{},l.name),l.kind+(l.name===p.spec.claim.level?' · the claim level':''),el('em',{},describeExpression(l.expression)+(l.by_source?` (per-file overrides for ${Object.keys(l.by_source).join(', ')})`:'')+(l.missing?' · blanks counted as unmapped':''))))),
     renderBindingQuestions(state.spec),citationEditor(review),
     el('div',{class:'chain-actions'},measureButton,editButton()));
   }
   panels.result.hidden=false;step('propose');panels.result.setAttribute('tabindex','-1');panels.result.focus({preventScroll:true});panels.result.scrollIntoView({behavior:'smooth',block:'start'});button.textContent='Sent';
  }catch(e){if(revision===inputRevision&&operation===workflowRevision){fail(e.message);button.disabled=false;button.textContent='Send again'}}
 }
 function citationEditor(initial){
  const holder=el('section',{});let review=initial,page=0;
  const names=review.citation_review?.documents.map(d=>d.file)||[...state.docs];
  const choose=el('select',{},names.map(n=>el('option',{value:n},n)));
  const start=el('input',{type:'number',min:'1',value:'1'}),end=el('input',{type:'number',min:'1',value:'1'});
  const text=el('pre',{style:'white-space:pre-wrap;overflow-wrap:anywhere'}),notice=el('p',{role:'status'});
  const previous=el('button',{type:'button',class:'secondary'},'Previous documentation lines'),next=el('button',{type:'button',class:'secondary'},'Next documentation lines');
  function show(){const lines=(state.files[choose.value]||'').split('\n').slice(0,lineCount(state.files[choose.value]));page=Math.min(page,Math.max(0,Math.ceil(lines.length/40)-1));text.textContent=lines.slice(page*40,(page+1)*40).map((s,i)=>`${page*40+i+1}  ${s}`).join('\n');previous.disabled=page===0;next.disabled=(page+1)*40>=lines.length}
  choose.addEventListener('change',()=>{page=0;show()});previous.addEventListener('click',()=>{page--;show()});next.addEventListener('click',()=>{page++;show()});
  const add=el('button',{type:'button',class:'secondary'},'Add reviewed citation');
  function draw(){holder.replaceChildren(renderReviewContext(review,reviewBindingPreview(state.spec,state.files)),el('details',{},el('summary',{},'Read full documentation and add a citation'),
   el('p',{},'Read the meaning, including denials or limitations. Adding a citation changes the specification, clears any prior result or confirmation, and requires a new local measurement. It makes no model call.'),
   el('label',{},'Citation document ',choose),text,el('div',{class:'chain-actions'},previous,next),
   el('label',{},'First citation line ',start),el('label',{},'Last citation line ',end),add,notice))}
  add.addEventListener('click',async()=>{
   const citation={file:choose.value,start_line:Number(start.value),end_line:Number(end.value)};
   if(!names.includes(citation.file)||!Number.isInteger(citation.start_line)||!Number.isInteger(citation.end_line)||citation.start_line<1||citation.end_line<citation.start_line||citation.end_line-citation.start_line>=40||citation.end_line>lineCount(state.files[citation.file])){notice.textContent='Choose an existing documentation range of 1–40 lines.';return}
   if(state.spec.citations.some(c=>JSON.stringify(c)===JSON.stringify(citation))){notice.textContent='That range is already cited.';return}
   if(state.spec.citations.length>=16){notice.textContent='At most 16 citations are supported. Define the specification differently to replace a range.';return}
   const revision=inputRevision,operation=++workflowRevision,newSpec={...state.spec,citations:[...state.spec.citations,citation]};add.disabled=true;
   try{
    const updated=await post('/api/ladder/review',{spec:newSpec,files:body().files,confirmed:[],documentation:[...state.docs]});
    if(revision!==inputRevision||operation!==workflowRevision)return;
    state.spec=newSpec;state.result=null;state.confirmed=[];state.replay=null;state.bundleReceipt=null;reset('ladder');
    review=updated;notice.textContent='Citation added. Meaning remains unverified; measure the reviewed specification again.';draw();step('propose');
   }catch(e){if(revision===inputRevision&&operation===workflowRevision)notice.textContent=e.message}
   finally{add.disabled=false}
  });draw();show();return holder;
 }
 function editButton(){const b=el('button',{class:'text-button',type:'button'},'Correct this binding');b.addEventListener('click',()=>builder());return b}
 function completeEditor(original,revision,operation){
  const text=el('textarea',{rows:'22','aria-label':'Complete ladder definition',class:'complete-definition'},JSON.stringify(original,null,2));
  const reviewButton=el('button',{type:'button',class:'primary'},'Validate corrected definition');
  reviewButton.addEventListener('click',async()=>{
   reviewButton.disabled=true;
   try{const next=JSON.parse(text.value),review=await post('/api/ladder/review',{spec:next,files:body().files,confirmed:[],documentation:[...state.docs]});
    if(revision!==inputRevision||operation!==workflowRevision)return;
    state.spec=next;state.result=null;state.confirmed=[];state.replay=null;state.bundleReceipt=null;
    state.proposal=state.proposal?{...state.proposal,defined_by:'person'}:null;
    const go=el('button',{type:'button',class:'primary'},'Measure on server');go.addEventListener('click',()=>measure([]));
    panels.result.replaceChildren(kicker('Review · Defined by you'),renderBindingQuestions(next),citationEditor(review),el('div',{class:'chain-actions'},go,editButton()));
   }catch(e){if(revision===inputRevision&&operation===workflowRevision)fail(e.message)}finally{reviewButton.disabled=false}
  });
  panels.result.replaceChildren(kicker('Review · Correct the complete definition'),renderBindingQuestions(original),
   el('p',{},'This definition uses rules beyond the guided form. All levels, source rules and citations are retained here. Editing and validation make no model call; a new measurement and confirmation are required.'),text,reviewButton);
  panels.result.hidden=false;panels.result.setAttribute('tabindex','-1');panels.result.focus({preventScroll:true});
 }
 function builder(){
  try{
  const revision=inputRevision,operation=++workflowRevision;reset('ladder');step('propose');
  const original=state.spec?structuredClone(state.spec):null,seed=bindingSeed(original);
  if(original&&!seed){completeEditor(original,revision,operation);return}
  const tables=tableFiles(),docs=[...state.docs];
  const cols=Object.fromEntries(tables.map(n=>[n,tableColumns(n,state.files[n])]));
  const rows=Object.fromEntries(tables.map(n=>[n,tableRows(n,state.files[n])]));
  for(const n of tables){if(rows[n].length>100000)throw Error('The builder supports at most 100,000 rows per table.');}
  const select=(options,value)=>{const s=el('select',{},options.map(o=>el('option',{value:o,...(o===value?{selected:'true'}:{})},o)));return s};
  const sourceRows=tables.map(n=>{
   const prior=seed?.sources.find(s=>s.file===n),split=prior?.partition.column||splitColumn(cols[n]);
   const role=select(['observations','lookup table only','ignore'],seed?(prior?'observations':'lookup table only'):'observations');
   const sample=select(cols[n],prior?.sample.column||cols[n].find(c=>c!==split)||cols[n][0]);
   const whole=select(['train','test','excluded'],prior?.partition.value||(/test|eval/i.test(n)?'test':'train'));
   const partition=select(['— whole file —',...cols[n]],prior?.partition.value?'— whole file —':split||'— whole file —');
   const mappingPanel=el('span',{class:'builder-map'});
   const source={name:n,split:null,role,sample,whole,partition,mapping:[],mappingPanel,mappingError:null};
   function updatePartition(){
    source.split=partition.value==='— whole file —'?null:partition.value;source.mappingError=null;source.mapping=[];
    try{
     source.mapping=source.split?partitionLabels(rows[n],source.split).map(({raw,count})=>({raw,count,box:select(['— choose role —','train','test','excluded'],prior?.partition.column===source.split&&prior.partition.map?.[raw]?prior.partition.map[raw]:/^(train|training|learn|learning|dev|val|valid|validation|test|testing|eval|evaluation)$/i.test(raw.trim())?guessPartition(raw):'— choose role —')})):[];
     mappingPanel.replaceChildren(...source.mapping.map(m=>el('label',{},`${JSON.stringify(m.raw)} (${m.count} rows) → `,m.box)));
    }catch(e){source.mappingError=e.message;mappingPanel.replaceChildren(el('span',{},e.message))}
    whole.disabled=!!source.split;
   }
   partition.addEventListener('change',updatePartition);updatePartition();return source;
  });
  const first=sourceRows.find(r=>r.role.value==='observations')||sourceRows[0];
  const unitName=el('input',{type:'text',value:seed?.name||(claimInput.value.match(/\b(patient|subject|person|recording|site|case|lesion|frog|study)\b/i)||['','subject'])[1].toLowerCase(),maxlength:'40'});
  const unitCol=select([...new Set(tables.flatMap(n=>cols[n]))],seed?.unit.column||first.sample.value);
  const base=el('input',{type:'checkbox',...(seed?.unit.basename?{checked:'true'}:{})}),prefix=el('input',{type:'number',min:'0',max:'128',value:String(seed?.unit.prefix||0)});
  const sep=el('input',{type:'text',maxlength:'3',placeholder:'e.g. -',class:'narrow'}),fieldFrom=el('input',{type:'number',min:'1',max:'32',placeholder:'from'}),fieldTo=el('input',{type:'number',min:'1',max:'32',placeholder:'to'});
  const charFrom=el('input',{type:'number',min:'1',max:'512',placeholder:'from'}),charTo=el('input',{type:'number',min:'1',max:'512',placeholder:'to'});
  const lookTable=select(['— none —',...tables],'— none —'),lookKey=el('input',{type:'text',placeholder:'key column'}),lookValue=el('input',{type:'text',placeholder:'value column'});
  const meaning=el('input',{type:'text',maxlength:'400',placeholder:'e.g. Records from the same subject differ in the last digit only.'});
  const docSel=select(['— choose documentation —',...docs],'— choose documentation —'),start=el('input',{type:'number',min:'1',placeholder:'first line'}),end=el('input',{type:'number',min:'1',placeholder:'last line'});
  if(seed){sep.value=seed.unit.field?.separator||'';fieldFrom.value=seed.unit.field?.from||'';fieldTo.value=seed.unit.field?.to||'';charFrom.value=seed.unit.characters?.from||'';charTo.value=seed.unit.characters?.to||'';lookTable.value=seed.unit.lookup?.file||'— none —';lookKey.value=seed.unit.lookup?.key||'';lookValue.value=seed.unit.lookup?.value||'';meaning.value=seed.meaning;docSel.value=seed.citation?.file||'— choose documentation —';start.value=seed.citation?.start_line||'';end.value=seed.citation?.end_line||''}
  const documentPanel=el('div',{class:'builder-preview'});let documentPage=0;
  function showDocument(){
   const text=state.files[docSel.value];
   if(text===undefined){documentPanel.replaceChildren(el('p',{},'Choose a document to read its numbered lines before citing it.'));return}
   const lines=text.split('\n').slice(0,lineCount(text)),pages=Math.max(1,Math.ceil(lines.length/40));
   documentPage=Math.min(documentPage,pages-1);
   const previous=el('button',{type:'button',class:'secondary',...(documentPage===0?{disabled:'true'}:{})},'Previous lines');
   const next=el('button',{type:'button',class:'secondary',...(documentPage===pages-1?{disabled:'true'}:{})},'Next lines');
   previous.addEventListener('click',()=>{documentPage--;showDocument()});next.addEventListener('click',()=>{documentPage++;showDocument()});
   documentPanel.replaceChildren(el('p',{},`${docSel.value} · ${lines.length} lines · page ${documentPage+1} of ${pages}. Choose the lines defining the unit and partition; no meaning is confirmed automatically.`),
    el('pre',{},lines.slice(documentPage*40,(documentPage+1)*40).map((line,i)=>`${documentPage*40+i+1}  ${line}`).join('\n')),
    el('div',{class:'chain-actions'},previous,next));
  }
  docSel.addEventListener('change',()=>{documentPage=0;showDocument()});showDocument();
  const preview=el('div',{class:'builder-preview'});
  function unitSpec(){const u={column:unitCol.value,basename:base.checked,prefix:Number(prefix.value)||0,meaning:meaning.value,
    field:sep.value?{separator:sep.value,from:Number(fieldFrom.value)||1,to:Number(fieldTo.value)||Number(fieldFrom.value)||1}:null,
    characters:Number(charFrom.value)?{from:Number(charFrom.value),to:Number(charTo.value)||Number(charFrom.value)}:null};
   if(lookTable.value!=='— none —')u.lookup={file:lookTable.value,key:lookKey.value.trim(),value:lookValue.value.trim()};return u}
  function refresh(){
   const previews=bindingPreview(sourceRows.filter(r=>r.role.value==='observations').map(r=>r.name),unitSpec(),rows);
   preview.replaceChildren(el('h3',{},'Preview the link from each row to its subject'),
    el('p',{},'Local examples only. Conflicting or missing lookup values remain unmapped; server validation and measurement decide the result.'),
    ...previews.map(p=>el('section',{},el('p',{},`${p.file}: ${p.distinct.toLocaleString('en-US')} distinct ${unitName.value||'unit'} values across ${p.rows.toLocaleString('en-US')} rows; ${p.unmapped.toLocaleString('en-US')} unmapped.`+(p.distinct===p.rows&&p.rows?' Each row in this file has a different identity. Check that these values identify the subject, rather than just the sample.':'')),
     el('table',{class:'builder-table'},el('tr',{},el('th',{},unitCol.value),el('th',{},unitName.value||'unit')),p.examples.map(r=>el('tr',{},el('td',{},r.raw),el('td',{},r.value??'— unmapped —')))))));
  }
  sourceRows.forEach(r=>[r.role,r.sample,r.partition,r.whole].forEach(x=>x.addEventListener('change',refresh)));
  [unitCol,base,prefix,sep,fieldFrom,fieldTo,charFrom,charTo,lookTable,lookKey,lookValue,unitName].forEach(x=>x.addEventListener('input',refresh));
  const use=el('button',{class:'primary',type:'button'},'Review corrected definition');
  use.addEventListener('click',async()=>{
   use.disabled=true;
   try{
   for(const r of sourceRows.filter(r=>r.role.value==='observations')){if(r.mappingError)throw Error(r.mappingError);if(r.mapping.some(m=>m.box.value==='— choose role —'))throw Error(`Choose training, evaluation or excluded for every label in ${r.name}.`)}
   const sources=sourceRows.filter(r=>r.role.value==='observations').map(r=>({file:r.name,sample:{column:r.sample.value},
    partition:r.split?{column:r.split,map:Object.fromEntries(r.mapping.map(m=>[m.raw,m.box.value]))}:{value:r.whole.value}}));
   if(!sources.length){fail('Choose at least one table of observations.');return}
   if(!docs.includes(docSel.value)||!Number(start.value)||!Number(end.value)){fail('Choose the documentation and line range you reviewed.');return}
   const next=preserveBinding(original,buildSpec({claim:claimInput.value.trim(),unitName:unitName.value,sources,unit:unitSpec(),citation:{file:docSel.value,start:start.value,end:end.value}}));
   const review=await post('/api/ladder/review',{spec:next,files:body().files,confirmed:[],documentation:[...state.docs]});if(revision!==inputRevision||operation!==workflowRevision)return;
   state.spec=next;state.result=null;state.confirmed=[];state.replay=null;state.bundleReceipt=null;
   state.proposal=state.proposal?{...state.proposal,defined_by:'person'}:null;
   const measureButton=el('button',{class:'primary',type:'button'},'Measure on server');measureButton.addEventListener('click',()=>measure([]));
   panels.result.replaceChildren(kicker('Review · Defined by you'),el('h3',{},`Claim bound to "${state.spec.claim.level}"`),
    el('ol',{class:'proposal-levels'},state.spec.levels.map(l=>el('li',{},el('b',{},l.name),l.kind+(l.name===state.spec.claim.level?' · the claim level':''),el('em',{},describeExpression(l.expression))))),
    renderBindingQuestions(state.spec),citationEditor(review),
    el('div',{class:'chain-actions'},measureButton,editButton()));
   step('propose');
   }catch(e){if(revision===inputRevision&&operation===workflowRevision)fail(e.message)}finally{use.disabled=false}
  });
  panels.result.replaceChildren(kicker('Review · Define the unit yourself'),el('h3',{},'How is the claim\'s unit written in your files?'),
   el('div',{class:'builder'},
    el('fieldset',{},el('legend',{},'1 · Choose the observation and partition'),...sourceRows.map(r=>el('div',{class:'builder-row'},el('strong',{},r.name),
     builderField(`File role · ${r.name}`,r.role),builderField(`Observation identifier · ${r.name}`,r.sample),
     builderField(`Partition column · ${r.name}`,r.partition),builderField(`Whole-file role · ${r.name}`,r.whole),r.mappingPanel))),
    el('fieldset',{},el('legend',{},'2 · Define the identity that must be unseen'),
     builderField('Identity name',unitName,'For example: patient, lesion or recording group.'),builderField('Identity source column',unitCol),
     el('details',{class:'builder-transforms',...(seed?.unit.basename||seed?.unit.field||seed?.unit.characters||seed?.unit.prefix?{open:'true'}:{})},
      el('summary',{},'Extract part of an identifier (optional)'),
      el('p',{class:'check-hint'},'Applied in this order: file name, separated fields, then character range or prefix. Field and character positions start at 1. Check the resulting values below.'),
      el('div',{class:'builder-transform-grid'},el('label',{class:'builder-basename'},base,' Use only the file name after the last /'),
       builderField('Field separator',sep,'Leave blank to keep the entire value.'),builderField('First field',fieldFrom),builderField('Last field',fieldTo),
       builderField('First character',charFrom),builderField('Last character',charTo),builderField('Prefix length',prefix,'0 keeps all characters. A character range takes precedence.'))),
     builderField('Reason for this identity (optional)',meaning)),
    el('fieldset',{},el('legend',{},'3 · Link identities through a mapping table (optional)'),
     el('p',{class:'check-hint builder-intro'},'Keep “none” if each observation already contains its identity. Otherwise the extracted value above must match the mapping key.'),
     builderField('Mapping table',lookTable),builderField('Mapping key column',lookKey),builderField('Mapped identity column',lookValue)),
    preview,
    el('fieldset',{},el('legend',{},'4 · Cite the definition you reviewed'),builderField('Documentation file',docSel),builderField('First cited line',start),builderField('Last cited line',end)),
    documentPanel),
   el('div',{class:'chain-actions'},use));
  panels.result.hidden=false;refresh();panels.result.setAttribute('tabindex','-1');panels.result.focus({preventScroll:true});panels.result.scrollIntoView({behavior:'smooth',block:'start'});
  }catch(e){fail(e.message)}
 }
 async function measure(confirmed){
  const revision=inputRevision,operation=++workflowRevision;error.hidden=true;reset('ladder');state.confirmed=confirmed;
  try{
   const data=await post('/api/ladder',{spec:state.spec,files:body().files,confirmed});if(revision!==inputRevision||operation!==workflowRevision)return;state.result=data;state.replay=null;
   renderLadder(panels.ladder,data,level=>measure([...confirmed,level]),reviewBindingPreview(state.spec,state.files));
   if(!panels.result.querySelector('.completed-review')){const content=[...panels.result.childNodes];panels.result.replaceChildren(el('details',{class:'completed-review'},el('summary',{},'Reviewed definition · '+state.spec.claim.level),...content))}
   panels.ladder.scrollIntoView({behavior:'smooth',block:'start'});
   const replayButton=el('button',{class:'primary',type:'button'},'Replay in a Nebius Sandbox');replayButton.addEventListener('click',()=>replayChain(replayButton));
   panels.replay.replaceChildren(kicker('Inspect · Independent recomputation'),el('h3',{},'Recompute in a fresh Nebius Sandbox.'),
    el('p',{},'Sends the engine source, the spec, your confirmations and the files to a disposable python:3.12-slim Sandbox. A matching replay and its inputs are saved privately in your workspace. Do not send personal or sensitive data to the Sandbox beta.'),
    el('div',{class:'chain-actions'},replayButton,saveButton(),downloadButton(),bundleButton()));
   panels.replay.hidden=false;step('measure');
  }catch(e){if(revision===inputRevision&&operation===workflowRevision)fail(e.message)}
 }
 async function replayChain(button){
  const revision=inputRevision,operation=++workflowRevision;button.disabled=true;button.textContent='Replaying in the Sandbox…';error.hidden=true;
  try{
   const data=await post('/api/ladder/replay',{spec:state.spec,files:body().files,confirmed:state.confirmed,proposal_id:state.proposal?.proposal_id||null});if(revision!==inputRevision||operation!==workflowRevision)return;state.replay=data;
   const p=data.provenance;
   panels.replay.replaceChildren(el('div',{class:'panel-head'},kicker('Inspect · Replayed in a Nebius Sandbox'),sponsors(false,true)),el('h3',{},'Matched the Asterisk server measurement exactly.'),
    el('div',{class:'chain-meta'},el('span',{},p.image),el('span',{},`${Number(p.seconds).toFixed(2)} s in the Sandbox`),el('span',{},'program '+p.program_sha256.slice(0,12)+'…'),el('span',{},'result '+p.result_sha256.slice(0,12)+'…')),
    el('p',{},'Same code, same inputs, independent infrastructure. This is evidence of reproducibility, not tamper-proofing.'),
    ...(data.receipt_error?[el('p',{class:'check-error'},data.receipt_error)]:[]),
    el('div',{class:'chain-actions'},saveButton(),downloadButton(),bundleButton()));
   step('replay');
  }catch(e){if(revision===inputRevision&&operation===workflowRevision){fail(e.message);button.disabled=false;button.textContent='Retry the replay'}}
 }
 function saveButton(){
  const button=el('button',{class:'secondary',type:'button'},state.replay?.receipt_id?'Open saved receipt':'Save to workspace');
  button.addEventListener('click',async()=>{
   if(state.replay?.receipt_id){location.href='/#ladder/'+state.replay.receipt_id;return}
   const currentKey=JSON.stringify({spec:state.spec,files:body().files,confirmed:state.confirmed,proposal_id:state.proposal?.proposal_id||null});
   if(state.bundleReceipt?.key===currentKey){location.href='/#ladder/'+state.bundleReceipt.id;return}
   button.disabled=true;button.textContent='Saving…';
   try{
    const revision=inputRevision,operation=++workflowRevision;const saved=await post('/api/ladder/receipts',{spec:state.spec,files:body().files,confirmed:state.confirmed,proposal_id:state.proposal?.proposal_id||null});
    if(revision===inputRevision&&operation===workflowRevision)location.href='/#ladder/'+saved.id;
   }catch(e){fail(e.message);button.disabled=false;button.textContent='Save to workspace'}
  });return button;
 }
 function bundleButton(){
  const b=el('button',{class:'secondary',type:'button',disabled:true},'Download evidence + inputs (ZIP)');
  const consent=el('input',{type:'checkbox',onchange:event=>{b.disabled=!event.target.checked}});
  b.addEventListener('click',async()=>{
   if(!consent.checked)return;
   const revision=inputRevision,operation=workflowRevision;
   b.disabled=true;b.textContent='Preparing evidence…';
   try{
    const payload={spec:state.spec,files:body().files,confirmed:state.confirmed,proposal_id:state.proposal?.proposal_id||null};
    const key=JSON.stringify(payload);
    let rid=state.replay?.receipt_id||(state.bundleReceipt?.key===key?state.bundleReceipt.id:null);
    if(!rid){const saved=await post('/api/ladder/receipts',payload);rid=saved.id;if(revision!==inputRevision||operation!==workflowRevision)return;state.bundleReceipt={key,id:rid}}
    const response=await fetch(`/api/ladder/receipts/${rid}/export?format=zip`,{credentials:'same-origin'});
    if(!response.ok){const data=await response.json().catch(()=>({}));throw Error(data.detail||'Evidence download failed. The saved receipt remains available.')}
    const blob=await response.blob();if(revision!==inputRevision||operation!==workflowRevision)return;
    const url=URL.createObjectURL(blob),link=el('a',{href:url,download:`asterisk-evidence-${rid}.zip`});
    document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);step('receipt');
   }catch(e){if(revision===inputRevision&&operation===workflowRevision)fail(e.message)}
   finally{b.disabled=false;b.textContent='Download evidence + inputs (ZIP)'}
  });return el('details',{},el('summary',{},'Include original inputs in an evidence ZIP'),el('p',{class:'hint'},'Includes every uploaded source file, including columns not sent to the model. Saves a private receipt without a paid call. Share only with authorized recipients.'),el('label',{},consent,' I want to include the uploaded source files.'),b);
 }
 function downloadButton(){
  const b=el('button',{class:'secondary',type:'button'},'Download measurement JSON');
  b.addEventListener('click',()=>{
   const r=receipt({claim:claimInput.value.trim(),proposal:state.proposal,spec:state.spec,result:state.result,replay:state.replay,createdAt:new Date().toISOString()});
   const link=el('a',{href:URL.createObjectURL(new Blob([JSON.stringify(r,null,2)],{type:'application/json'})),download:'asterisk-ladder-receipt.json'});
   document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(link.href),1000);step('receipt');
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

function updateView(){
 const hash=location.hash.slice(1),view=hash==='experiment'?'evidence':hash==='benchmarks'||/^(wsibench-|ptbxl|esc50-|urbansound8k-)/.test(hash)?'benchmarks':'workspace';
 document.body.dataset.view=view;
 for(const link of document.querySelectorAll('.product-nav nav a')){const selected=link.getAttribute('href')===(view==='workspace'?'#propose':view==='benchmarks'?'#benchmarks':'#experiment');if(selected)link.setAttribute('aria-current','page');else link.removeAttribute('aria-current')}
}
updateView();window.addEventListener('hashchange',updateView);
heroFigure($('#hero-rungs'));checker();proposer();
Promise.allSettled([gallery(),experiment()]).then(()=>{
 const id=location.hash.slice(1);if(['propose','benchmarks','experiment'].includes(id))document.getElementById(id)?.scrollIntoView();
});

providerAllowance();
