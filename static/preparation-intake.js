import {loadDermaBenchmark} from './benchmark-source.mjs';
import {inspectJSON,projectJSON} from './json-projection.mjs';
import {inspectCSV,projectCSV,projectionRecord,projectionCompanion} from './csv-projection.mjs';
import {uploadSummaryView} from './preparation-upload-summary.mjs';
import {localColumnSamples} from './preparation-local-preview.mjs';
import {trackUnsaved} from './preparation-unsaved.mjs';
import {createDraftSaver} from './preparation-save.mjs';
import {policyEditor} from './preparation-policy.js?v=repeat-excerpts-2';
export function nativePreparation({el,btn,api,onSaved,isCurrent,onManual,initial={},proposalConfigured=null,draftCapacity=null,loadBenchmark=loadDermaBenchmark}) {
 const root=el('section',{class:'preparation-page preparation-native'});
 const availability=el('p',{class:'preparation-experimental',role:'note'},proposalConfigured===false
  ?'Model proposals are unavailable on this server. You can inspect fields locally and use manual CSV setup. No model call will be offered.'
  :proposalConfigured===true?'Model proposals are configured. You will review the exact upload before authorizing a request; budget and provider availability are checked when you submit.'
  :'Model availability could not be checked. Local field inspection still works; the upload preview will show whether a proposal can be requested.');
 if(proposalConfigured===false)availability.append(' ',el('a',{href:'/static/about.html#enable-preparation',target:'_blank',rel:'noopener noreferrer'},'Enable proposals on your installation (new tab)'));
 const unsaved=trackUnsaved(root);
 let ticket=null,busy=false,attempted=false,manualFiles=null,localReview=null,benchmarkFiles=null;
 const fieldReview=el('section',{hidden:true,tabindex:'-1',class:'preparation-file-roles'});
 const saveDraft=createDraftSaver(api);
 const steps=['Choose files','Review upload','Review interpretation'].map((label,i)=>el('li',{},el('span',{class:'preparation-step-number'},String(i+1).padStart(2,'0')),el('span',{},label)));
 const progress=el('ol',{class:'preparation-steps','aria-label':'Preparation progress'},...steps);
 function stage(index){steps.forEach((step,i)=>{if(i===index)step.setAttribute('aria-current','step');else step.removeAttribute('aria-current');step.dataset.state=i<index?'past':i===index?'current':'next'})}
 stage(0);
 const title=el('input',{id:'native-title',required:'true',maxlength:'120',placeholder:'e.g. ECG patient split'});
 const claim=el('textarea',{id:'native-claim',required:'true',minlength:'10',maxlength:'3000',rows:'3',placeholder:'What should be absent from training at evaluation time?'});
 title.value=typeof initial.title==='string'?initial.title:'';claim.value=typeof initial.claim==='string'?initial.claim:'';
 if(title.value||claim.value)queueMicrotask(()=>{if(root.isConnected)unsaved.changed()});
 const unit=el('input',{id:'native-unit',maxlength:'120',placeholder:'e.g. individual frogs, speakers, specimens'});
 unit.value=initial.evaluation_intent?.target==='unseen_entities'?initial.evaluation_intent.unit||'':'';
 const evaluationIntent=()=>unit.value.trim()?{target:'unseen_entities',unit:unit.value.trim()}:null;
 const files=el('input',{id:'native-files',type:'file',accept:'.csv,.json,.md,.txt',multiple:'true',required:'true'});
 const roles=el('fieldset',{hidden:'true',class:'preparation-file-roles'},el('legend',{},'Which files explain the dataset?')),roleList=el('div');roles.append(el('p',{},'Mark documentation to include up to 100 numbered lines. Data files contribute profiles and source examples. Inspect the exact payload before any model upload.'),roleList);
 const benchmarkStatus=el('p',{class:'hint','aria-live':'polite'});
 const benchmark=btn('Load real benchmark files',async()=>{
  if(busy)return;
  if(benchmarkFiles||files.files.length){message('Files are already selected. Keep this setup, or start a new preparation to load the benchmark.',true);return}
  setBusy(true);message('Downloading the pinned public files and checking their hashes…');
  try{
   const loaded=await loadBenchmark();if(!isCurrent())return;
   benchmarkFiles=loaded;files.required=false;
   if(!title.value)title.value='DermaMNIST original split';
   if(!claim.value)claim.value='Lesions in the test partition should be absent from training; validation is excluded.';
   resetFiles(loaded);unsaved.changed();
   benchmarkStatus.textContent='Loaded locally: '+loaded.map(file=>file.name).join(', ')+'. Choose your own files to replace this example.';
   message('Pinned source hashes match. Inspect fields next. No Asterisk upload or model call has occurred.');
  }catch(error){if(isCurrent())message(error.message,true)}finally{setBusy(false);if(isCurrent()&&benchmarkFiles)submit.focus()}
 },'secondary');
 const benchmarkChoice=el('details',{class:'preparation-retention'},el('summary',{},'Try a real public benchmark'),el('p',{},'Load the original DermaMNIST split and HAM10000 metadata directly from a pinned public GitHub source. GitHub receives this download request. Files are read on this device; no model is called.'),el('p',{},'The metadata includes age, sex and other personal attributes. In the next step, include only image_id and split from the split table, and image_id and lesion_id from the metadata. Review and include benchmark-context.txt as documentation. No fields or permissions are preselected.'),benchmark,benchmarkStatus);
 const storage=el('input',{id:'native-storage',type:'checkbox'});
 const storageConsent=el('label',{class:'preparation-consent',hidden:true},storage,el('span',{},'Store the selected table fields and explicitly approved complete documentation files on this Asterisk server. Nebius needs separate consent.'));
 const status=el('p',{role:'status','aria-live':'polite'}),payload=el('section',{hidden:'true',class:'preparation-upload-preview',tabindex:'-1'}),editor=el('section',{hidden:'true'});
 const upload=el('input',{type:'checkbox'});
 const submit=el('button',{type:'submit',class:'primary'},'Inspect fields on this device');
 const request=btn('Request extraction proposal',async()=>{
  if(busy||attempted||!ticket?.provider_available||!upload.checked)return;
  attempted=true;remember(ticket.ticket_id);recover.hidden=false;setBusy(true);message('Requesting one proposal. No automatic retry will be made.');
  try{
   const result=await api('/preparations/proposals/'+ticket.ticket_id+'/submit','POST',{payload_hash:ticket.payload_hash,confirm_upload:true});
   if(!isCurrent())return;
   showResult(result);
  }catch(error){if(isCurrent()){
   if(error.preparationNotStarted===true){attempted=false;remember(null);recover.hidden=true;}
   message(error.message,true);
  }}finally{upload.checked=false;setBusy(false)}
 });

 const manual=btn('Use these CSV files in manual split setup',()=>{
  if(busy||manual.hidden||!manualFiles||!onManual)return;
  const seed={title:title.value,claim:claim.value,evaluation_intent:evaluationIntent(),files:manualFiles.map(file=>({...file})),_manual:true};
  unsaved.saved();onManual(seed);
 },'secondary');
 manual.hidden=true;
 const manualHelp=el('details',{class:'preparation-source preparation-manual-help'},el('summary',{},'When should I use manual setup?'),el('p',{class:'hint'},'For CSV files already containing sample IDs, subject IDs and split labels. This copies the reviewed files into manual column setup; withheld CSV columns stay omitted. A JSON record of selected fields and file hashes travels with the setup. It does not repair missing evidence, transform JSON, confirm a binding or call a model.'));manualHelp.hidden=true;
 const recoveryKey='asterisk-preparation-attempt';
 function remember(id){try{if(id)sessionStorage.setItem(recoveryKey,id);else sessionStorage.removeItem(recoveryKey)}catch{}}
 const recover=btn('Recover previous response',async()=>{
  if(busy)return;manualFiles=null;manual.hidden=true;manualHelp.hidden=true;setBusy(true);message('Checking the saved response. No model request is being made.');
  try{
   let id;try{id=sessionStorage.getItem(recoveryKey)}catch{}
   if(!id&&attempted)id=ticket?.ticket_id;
   if(!id)throw Error('No previous attempt is recorded in this tab.');
   const saved=await api('/preparations/proposals/'+encodeURIComponent(id));
   if(!isCurrent())return;
   if(saved.state!=='completed'){message('No completed response is stored yet. The attempt may still be running or may have stopped. Check again; this action never retries the model.');return;}
   ticket={ticket_id:id};attempted=true;
   if(saved.manual_inputs){
    const retained=saved.manual_inputs;
    claim.value=retained.claim;
    unit.value=retained.evaluation_intent?.target==='unseen_entities'?retained.evaluation_intent.unit||'':'';
    manualFiles=Object.entries(retained.files).map(([name,content])=>({name,content}));
    const companion=projectionCompanion(retained.files,retained.projection||[]);if(companion)manualFiles.push(companion);
    manual.hidden=!onManual||!manualFiles.some(file=>/\.csv$/i.test(file.name));manualHelp.hidden=manual.hidden;
    payload.replaceChildren(el('h2',{},'Your reviewed files are still available.'),el('p',{},'These are the files retained from this attempt, with the same selected fields. Continuing manually does not retry the model or change its recorded response.'),manualHelp,manual);
    payload.hidden=false;stage(1);
   }
   showResult(saved.result);
  }catch(error){if(isCurrent())message(error.message,true)}finally{setBusy(false)}
 },'secondary');
 try{recover.hidden=!sessionStorage.getItem(recoveryKey)}catch{recover.hidden=true}
 function showResult(result){
   if(result.status==='rejected'){message('The model returned a proposal that the local checker could not execute. No extraction was accepted. Review the source documentation or use the supported manual CSV setup. No automatic retry was made.',true);return;}
   if(result.status==='blocked'){message('This attempt was blocked before contacting Nebius. No model call was made. Check the existing budget and provider configuration before creating another preview.',true);return;}
   if(result.status==='failed'){message('The previous attempt failed. A remote charge may have occurred; this recovery did not retry it.',true);return;}
   if(result.status==='insufficient'){message('The model could not propose an extraction: '+result.missing.join('; '),true);return;}
   unsaved.changed();
   const policies=Object.fromEntries(result.spec.sources.map(source=>[source.file,{sample:source.sample,entity:source.entity,partition:source.partition,repeats:source.deduplicate?'collapse':'distinct',evidence:result.spec.citations}]));
   const data={title:title.value||'Recovered preparation',proposed:true,sources:result.sources,record:{inputs:result.files,original_spec:result.spec,policies,model_proposal:result.model_proposal}};
   const description=el('p',{class:'hint'},'The model proposed these choices. Review the observation, subject, partition and evidence fields; nothing is confirmed. Preview before saving a draft.');
   const issue=typeof result.proposal_issue==='string'&&result.proposal_issue?el('section',{class:'preparation-proposal-issue',role:'note'},el('h3',{},'The starting proposal was blocked.'),el('p',{},result.proposal_issue),el('p',{class:'hint'},'The local checker rejected the model’s starting choices. Review the source evidence and preview your corrections below before saving. A successful preview remains unconfirmed. No new model request is needed.')):null;
   editor.replaceChildren(el('p',{class:'eyebrow'},'03 / Your interpretation'),el('h2',{},'Review what the files mean.'),description,...(issue?[issue]:[]),policyEditor({data,api,
    previewPolicy:policies=>api('/preparations/review-proposal','POST',{files:result.files,spec_text:JSON.stringify(result.spec),policies,model_proposal:result.model_proposal}),
    savePolicy:async record=>{
     const saved=await saveDraft(data.title,record);
     // Cleanup is independent: a saved draft must never appear to have failed
     // because deleting its temporary proposal failed. Expiry remains the fallback.
     try{await api('/preparations/proposals/'+ticket.ticket_id,'DELETE')}catch{}
     remember(null);return saved;
    },
    onSaved:saved=>{unsaved.saved();if(isCurrent())onSaved(saved.id)}
   }));stage(2);editor.hidden=false;recover.hidden=true;form.hidden=true;payload.hidden=true;message('Proposal received. Its interpretation still needs your review.');editor.setAttribute('tabindex','-1');editor.focus();
 }
 request.disabled=true;
 function message(text,error=false){status.textContent=text;status.className=error?'error':'hint';if(error){status.tabIndex=-1;status.focus()}}
 function setBusy(value){busy=value;manual.disabled=value;root.setAttribute('aria-busy',String(value));recover.disabled=value;for(const field of form.querySelectorAll('input,textarea,button'))field.disabled=value||field.dataset?.projectionBlocked==='true';upload.disabled=value;request.disabled=value||attempted||!ticket?.provider_available||!upload.checked;}
 function invalidate(){stage(0);manualFiles=null;manual.hidden=true;manualHelp.hidden=true;ticket=null;attempted=false;payload.hidden=true;upload.checked=false;request.disabled=true;}
 let previousTicket=null;
 const form=el('form',{class:'preparation-import',novalidate:true},el('div',{class:'preparation-section-heading'},el('p',{class:'eyebrow'},'01 / The source material'),el('h2',{},'Dataset details'),el('p',{class:'hint'},'Use the tables you already have, plus documentation explaining their identities and split.')),el('div',{class:'field'},el('label',{for:title.id},'Preparation name'),title),el('div',{class:'field'},el('label',{for:claim.id},'Your evaluation claim'),claim),el('div',{class:'field'},el('label',{for:unit.id},'Who or what should be unseen?'),unit,el('p',{class:'hint'},'Optional: name the unit that should be absent from training. This choice travels with your saved preparation and pre-fills the split check. It does not confirm which column represents that unit.')),el('div',{class:'field'},el('label',{for:files.id},'Dataset files and documentation'),el('p',{class:'hint'},'CSV up to 10 MB · JSON up to 32 MB locally · Upload after projection: 16 MB total'),files,benchmarkChoice,el('details',{class:'preparation-retention'},el('summary',{},'Which file layouts work?'),el('p',{},'CSV: a header row followed by observations. JSON: an array of records; select the scalar fields to include. Text: simple lists with one identifier per line, or documentation explaining your files.'),el('p',{},'Raw sensor streams, whitespace feature matrices, multi-line records, archives and notebooks need preparation outside Asterisk. Changing their extension does not convert them. Export an observation table and preserve its link to the original rows; do not discard the subject identity or split labels.'),el('p',{},'For example, an image ID identifies an observation; a patient or specimen ID identifies the unit whose overlap you want to check. Include the documentation that explains that distinction.'))),roles,fieldReview,
  storageConsent,el('details',{class:'preparation-retention'},el('summary',{},'How long are my files kept?'),el('p',{},'Temporary previews expire after one hour; their stored files are removed on later cleanup or discard. Saving a reviewed draft retains its files until you delete it.')),submit);
 form.addEventListener('input',()=>{unsaved.changed();if(ticket)previousTicket=ticket.ticket_id;invalidate()});
 function resetFiles(selected){form.noValidate=true;localReview=null;fieldReview.hidden=true;storageConsent.hidden=true;storage.checked=false;submit.textContent='Inspect fields on this device';invalidate();roles.hidden=!selected.length;roleList.replaceChildren(...selected.map(file=>{const box=el('input',{type:'checkbox',value:file.name});return el('label',{class:'preparation-consent'},box,el('span',{},file.name))}))}
 files.addEventListener('change',()=>{benchmarkFiles=null;files.required=true;benchmarkStatus.textContent='';resetFiles([...files.files]);unsaved.changed()});
 upload.addEventListener('change',()=>{request.disabled=busy||attempted||!ticket?.provider_available||!upload.checked});
 form.addEventListener('submit',async event=>{
  event.preventDefault();if(busy)return;if(localReview&&!storage.checked){message('Confirm storage of the reviewed files before preparing the server preview.',true);return;}
  if(ticket)previousTicket=ticket.ticket_id;invalidate();setBusy(true);message(localReview?'Preparing the reviewed upload…':'Reading files on this device. No upload is being made…');
  try{
   if(!localReview){
   const selected=benchmarkFiles||[...files.files];if(!selected.length||selected.length>80||selected.some(f=>f.size>(/\.json$/i.test(f.name)?32_000_000:10_000_000))||selected.reduce((sum,f)=>sum+f.size,0)>64_000_000)throw Error('Choose 1–80 files: JSON up to 32 MB locally, other files up to 10 MB, 64 MB total locally. Projected uploads remain limited to 10 MB each and 16 MB total.');
   const unsupported=selected.filter(file=>! /^[A-Za-z0-9][A-Za-z0-9_. -]{0,159}\.(csv|json|md|txt)$/i.test(file.name));
   if(unsupported.length)throw Error('These files are not supported: '+unsupported.map(file=>file.name).join(', ')+'. Nothing was read or uploaded. Use CSV tables with headers, JSON arrays of records, or supported text files. Use simple filenames without folders or parentheses. Renaming a raw data file does not convert its contents; see “Which file layouts work?” below.');
   const originals=Object.create(null);for(const file of selected){if(Object.hasOwn(originals,file.name))throw Error('Two selected files have the same name. Rename one before continuing.');try{originals[file.name]=new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(await file.arrayBuffer())}catch{throw Error(file.name+': export this file as valid UTF-8.')}}

   if(!isCurrent())return;
   const entries=Object.entries(originals).map(([name,content])=>({name,content,table:/\.csv$/i.test(name)?inspectCSV(content):/\.json$/i.test(name)?inspectJSON(content):null,choices:[],approved:false}));
   fieldReview.replaceChildren(el('h3',{},'Choose what leaves this device.'),el('p',{},'Nothing has been uploaded. Select only the columns needed for observation IDs, subject IDs and partitions. Names alone cannot establish that a field is safe; identifiers can still be sensitive. Records and selected scalar values are preserved. Nested JSON fields must be withheld.'));
   for(const entry of entries){
    const section=el('fieldset',{},el('legend',{},entry.name));
    if(entry.table){
     section.append(el('p',{class:'hint'},entry.table.recordCount+' records · No columns selected by default. Unchecked columns stay on this device.'));
     section.append(el('p',{class:'hint'},'Examples below are the first three records, displayed only on this device. They are not a safety check of every row. Long values are shortened.'));
     entry.table.headers.forEach((name,index)=>{const box=el('input',{type:'checkbox','aria-label':'Include '+name+' from '+entry.name});const blocked=entry.table.blocked?.includes(name);box.disabled=!!blocked;if(blocked)box.title='Nested field: withheld from projection';box.dataset.projectionBlocked=blocked?'true':'false';box.addEventListener('change',()=>{entry.choices[index]=box.checked;storage.checked=false});section.append(el('label',{class:'preparation-consent preparation-column-choice'},box,el('span',{},el('strong',{},name+(blocked?' · nested field, withheld':'')),el('span',{class:'preparation-local-samples'},...localColumnSamples(entry.table,index).map(value=>el('code',{},value))))))});
    }else{
     const box=el('input',{type:'checkbox'});box.addEventListener('change',()=>{entry.approved=box.checked;storage.checked=false});
     section.append(el('p',{class:'hint'},'Review this documentation locally; it will be sent whole or omitted.'),el('details',{class:'preparation-source'},el('summary',{},'Preview documentation on this device'),el('pre',{tabindex:'0'},entry.content.slice(0,4000)),el('p',{class:'hint'},entry.content.length>4000?'Showing the first 4,000 characters. Inspect the full file locally before including it; inclusion sends the complete file.':'Complete file shown.')),el('label',{class:'preparation-consent'},box,el('span',{},'Include this complete file')));
    }
    fieldReview.append(section);
   }
   localReview=entries;form.noValidate=false;fieldReview.hidden=false;storageConsent.hidden=false;storage.checked=false;submit.textContent='Review the upload payload';fieldReview.focus();message('Local inspection ready. Choose fields and files, then approve server storage. No request has been made.');return;
   }
   const contents=Object.create(null),projection=[];
   for(const entry of localReview){
    if(entry.table){const result=(entry.table.format==='json'?projectJSON:projectCSV)(entry.table,entry.choices.flatMap((chosen,i)=>chosen?[i]:[]));contents[entry.name]=result.content;projection.push(await projectionRecord(entry.name,entry.content,result));}
    else if(entry.approved)contents[entry.name]=entry.content;
   }
   const sizes=Object.values(contents).map(text=>new TextEncoder().encode(text).length);
   if(!sizes.length||sizes.some(size=>size>10_000_000)||sizes.reduce((a,b)=>a+b,0)>16_000_000)throw Error('Reviewed files exceed the upload limits: 10 MB per file and 16 MB total. Select fewer fields.');
   if(!isCurrent())return;
   if(previousTicket){await api('/preparations/proposals/'+previousTicket,'DELETE');previousTicket=null;}
   ticket=await api('/preparations/proposal-preview','POST',{files:contents,projection,claim:claim.value,evaluation_intent:evaluationIntent(),documentation:[...roleList.querySelectorAll('input:checked')].map(input=>input.value).filter(name=>Object.hasOwn(contents,name)),store_inputs:true});
   if(!isCurrent())return;
   availability.textContent=ticket.provider_available?'Model proposals are available for this reviewed payload. Authorize the request below when ready.':'Model proposals are unavailable for this preview. Your reviewed files remain available for manual CSV setup.';
   manualFiles=Object.entries(contents).map(([name,content])=>({name,content}));
   const companion=projectionCompanion(contents,projection);if(companion)manualFiles.push(companion);
   manual.hidden=!onManual||!manualFiles.some(file=>/\.csv$/i.test(file.name));manualHelp.hidden=manual.hidden;
   payload.replaceChildren(el('p',{class:'eyebrow'},'02 / Before the model call'),el('h2',{},'Inspect what would leave Asterisk.'),el('p',{},ticket.provider_available?'One request to '+ticket.model+'. Estimated reservation: $'+ticket.estimated_reservation_usd.toFixed(4)+'. Billing is not verified.':'Preview only: the budgeted preparation provider is not configured. No model upload is available.'),el('p',{class:'hint'},ticket.notice),uploadSummaryView(el,ticket),...(ticket.client_projection?.length?[el('section',{},el('h3',{},'Your field projection'),...ticket.client_projection.map(item=>el('p',{},item.file+': sending '+item.included.join(', ')+'; withheld '+(item.withheld.join(', ')||'none')+'. '+item.records+' records retained.')),el('p',{class:'hint'},'Original hashes and withheld field names are browser-reported. The server checks projected bytes, headers and record counts only. This is not anonymization.'))]:[]),el('details',{class:'preparation-source'},el('summary',{},'Exact messages, source hashes and limits'),el('pre',{tabindex:'0'},JSON.stringify(ticket,null,2))),el('label',{class:'preparation-consent'},upload,el('span',{},'I reviewed this exact payload and authorize sending it to Nebius for one extraction proposal. This does not confirm the proposed interpretation.')),request,manualHelp,manual,
    btn('Edit files or claim',()=>{if(busy)return;previousTicket=ticket?.ticket_id;invalidate();form.hidden=false;title.focus();message('Your inputs are retained. Review a new upload preview after editing.');},'secondary'),
    btn('Discard this preview',async()=>{if(busy)return;setBusy(true);try{await api('/preparations/proposals/'+ticket.ticket_id,'DELETE');remember(null);recover.hidden=true;invalidate();form.hidden=false;message('Temporary preview discarded. Your selected local files remain available.')}catch(error){message(error.message,true)}finally{setBusy(false)}},'text-button'));
   stage(1);form.hidden=true;payload.hidden=false;payload.focus();message('Preview ready. Read the source values and documentation before authorizing an upload.');
  }catch(error){if(isCurrent())message(error.message,true)}finally{setBusy(false)}
 });
 root.append(el('p',{class:'eyebrow'},'Native dataset preparation · Experimental'),el('h1',{},'Start with the files.'),el('p',{class:'lede'},'Let the documentation guide an extraction proposal. You review its meaning before Asterisk prepares any split tables.'),el('p',{class:'preparation-experimental'},'Experimental · Review every proposed identity and split. Automatic extraction has not passed the acceptance study.'),availability,...(draftCapacity?.available===false?[el('aside',{class:'preparation-experimental',role:'note'},el('strong',{},'Preparation storage is full.'),el('p',{},'You can inspect files locally, but a new model proposal is blocked until there is room to save it. Download any draft you want to keep before removing it.'),el('a',{href:'#preparations'},'Review saved drafts'))]:[]),progress,...((title.value||claim.value)?[el('p',{class:'hint'},'Name and claim copied from your split setup. Choose the dataset files below; no files or upload consent were transferred.')]:[]),recover,form,status,payload,editor);
 return root;
}
