import {preparationSourceView} from './preparation-source-view.js';
import {preparationClaim,preparationIntent} from './preparation-claim.mjs';
import {evidenceDisclosure} from './preparation-evidence.mjs';
import {preparationSummary} from './preparation-summary.mjs';
import {mayLeavePreparation,trackUnsaved} from './preparation-unsaved.mjs';
import {createDraftSaver} from './preparation-save.mjs';
import {nativePreparation} from './preparation-intake.js?v=local-field-preview-3';
import {preparationProvenance} from './preparation-provenance.mjs';
import {stageFiles} from './file-import.js?v=prepared-zip-1';
import {policyEditor} from './preparation-policy.js?v=manual-preparation-handoff-1';
// Drafts are server-owned. This view never treats saved choices as confirmation.
export function createPreparations({el,btn,api,main,toast,onContinue}) {
 let epoch=0,pendingIntake=null;
 const go=id=>{location.hash=id?'preparation/'+id:'preparations'};
 const errorNode=()=>el('p',{class:'error',role:'alert',hidden:'true'});
 const showError=(node,error)=>{node.hidden=false;node.textContent=error.message;node.tabIndex=-1;node.focus()};
 function download(record){const url=URL.createObjectURL(new Blob([JSON.stringify(record,null,2)],{type:'application/json'}));const a=el('a',{href:url,download:'asterisk-preparation-draft-'+record.draft_hash.slice(0,12)+'.json'});document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000)}
 function shell(title,intro,...children){document.querySelector('#page-name').textContent='Preparation drafts';main.replaceChildren(el('div',{class:'preparation-page'},el('p',{class:'eyebrow'},'Dataset preparation · Experimental'),el('h1',{},title),el('p',{class:'lede'},intro),...children));main.focus({preventScroll:true})}
 async function list(version){
  shell('Keep your work.','Save a reviewed preparation here, then return to the same source files and choices. A saved draft is not a confirmed interpretation or a split result.',el('p',{role:'status'},'Loading preparations…'));
  try{
   const {drafts}=await api('/preparations');if(version!==epoch)return;
   const saveDraft=createDraftSaver(api);
   const title=el('input',{id:'preparation-title',maxlength:'120',required:'true',placeholder:'e.g. Patient split · first review'});
   const file=el('input',{id:'preparation-file',type:'file',accept:'.json',required:'true'});
   const consent=el('input',{type:'checkbox',required:'true'}),error=errorNode();
   const submit=el('button',{type:'submit',class:'primary'},'Save preparation');
   const form=el('form',{class:'preparation-import'},el('h2',{},'Bring a preparation into this workspace'),el('p',{},'Choose an unconfirmed draft JSON exported by the preparation editor. Confirmed review records are not accepted here.'),
    el('div',{class:'field'},el('label',{for:title.id},'Preparation name'),title),el('div',{class:'field'},el('label',{for:file.id},'Draft file · up to 32 MB'),file),
    el('label',{class:'preparation-consent'},consent,el('span',{},'Store this draft and its complete original source files on the Asterisk app server. No files are sent to Nebius by this action.')),error,submit);
   const importEdits=trackUnsaved(form);
   form.addEventListener('input',()=>importEdits.changed());
   form.addEventListener('change',()=>importEdits.changed());
   form.addEventListener('submit',async event=>{event.preventDefault();if(submit.disabled)return;submit.disabled=true;title.disabled=true;file.disabled=true;consent.disabled=true;error.hidden=true;submit.textContent='Validating and saving…';
    try{const picked=file.files[0];if(!picked||picked.size>32_000_000)throw new Error('Choose a draft JSON smaller than 32 MB.');let record;try{record=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(await picked.arrayBuffer()))}catch{throw new Error('The draft must be valid UTF-8 JSON.')}if(!consent.checked)throw new Error('Confirm server storage before saving.');
     const saved=await saveDraft(title.value,record);importEdits.saved();if(version===epoch)go(saved.id);else toast('Preparation saved. Find it under Preparation drafts.');
    }catch(e){if(version===epoch)showError(error,e)}finally{submit.disabled=false;title.disabled=false;file.disabled=false;consent.disabled=false;submit.textContent='Save preparation'}
   });
   const rows=el('section',{class:'preparation-list','aria-label':'Saved preparations'},el('div',{class:'section-line'},el('h2',{},'Saved preparations'),el('span',{},drafts.length+' / 10')),
    ...(drafts.length?drafts.map(d=>el('a',{class:'preparation-card',href:'#preparation/'+d.id},el('div',{},el('strong',{},d.title),el('p',{},'Unconfirmed · Revision '+d.revision)),el('span',{},'Open →'))):[el('p',{class:'preparation-empty'},'No preparations saved yet. Your saved drafts will appear here, separate from completed split receipts.')]));
   shell('Keep your work.','Return to your original files and reviewed choices. Reopening recomputes the preparation and requires fresh confirmation.',btn('Prepare dataset files',()=>{location.hash='prepare'}),rows,form,
    el('p',{class:'hint'},'Drafts belong to this browser session. Keep a downloaded copy before clearing browser data. Native-file preparation is available above and remains experimental.'));
  }catch(e){if(version===epoch)shell('Preparations unavailable.','Your saved work has not been changed.',el('p',{class:'error',role:'alert'},e.message),btn('Try again',()=>list(++epoch)))}
 }
 async function detail(id,version){
  shell('Opening preparation…','Recomputing the saved choices from their original inputs.',el('p',{role:'status'},'Loading…'));
  try{
   const data=await api('/preparations/'+id);if(version!==epoch)return;
   const error=errorNode(),title=el('input',{id:'saved-preparation-title',maxlength:'120',required:'true'});title.value=data.title;
   const rename=el('button',{type:'submit',class:'secondary'},'Save name');
   const form=el('form',{class:'preparation-rename'},el('div',{class:'field'},el('label',{for:title.id},'Preparation name'),title),rename);
   const nameEdits=trackUnsaved(title);
   title.addEventListener('input',()=>{if(title.value===data.title)nameEdits.saved();else nameEdits.changed()});
   const remove=btn('Delete draft',()=>{confirmation.hidden=false;confirmDelete.focus()},'text-button');
   const confirmDelete=btn('Delete this draft',async()=>{if(confirmDelete.disabled)return;confirmDelete.disabled=true;rename.disabled=true;cancel.disabled=true;error.hidden=true;
    try{await api('/preparations/'+id,'DELETE',{revision:data.revision});if(version===epoch){nameEdits.saved();claimEdits.saved();go()}else toast('Preparation draft deleted.')}catch(e){if(version===epoch)showError(error,e)}finally{confirmDelete.disabled=false;rename.disabled=false;cancel.disabled=false}},'secondary');
   const cancel=btn('Keep draft',()=>{confirmation.hidden=true;remove.focus()},'text-button');
   const confirmation=el('div',{class:'preparation-delete',hidden:'true'},el('p',{},'Delete this draft and its stored source files? Download a copy first if you want to keep it.'),el('div',{class:'actions'},confirmDelete,cancel));
   form.addEventListener('submit',async event=>{event.preventDefault();if(rename.disabled)return;rename.disabled=true;title.disabled=true;remove.disabled=true;error.hidden=true;
    try{const saved=await api('/preparations/'+id,'PUT',{title:title.value,record:data.record,revision:data.revision,store_inputs:true});Object.assign(data,saved);title.value=saved.title;nameEdits.saved();if(version===epoch){document.querySelector('.preparation-page h1').textContent=saved.title;toast('Preparation name saved.')}}catch(e){if(version===epoch)showError(error,e)}finally{rename.disabled=false;title.disabled=false;remove.disabled=false}
   });
   const counts=el('div',{class:'preparation-counts'},...Object.entries(data.population).map(([key,count])=>el('div',{},el('span',{},key==='train'?'Training observations':key==='test'?'Evaluation observations':'Excluded observations'),el('strong',{},Number(count).toLocaleString()))));
   const interpretation=el('section',{class:'preparation-interpretation','aria-label':'Saved interpretation'},el('div',{class:'preparation-section-heading'},el('p',{class:'eyebrow'},'The choices behind these counts'),el('h2',{},'What this preparation means'),el('p',{class:'hint'},'These are the saved rules, not a confirmation that they match your research claim. Compare them with the original documentation below.')),
    ...preparationSummary(data).map(source=>el('section',{class:'preparation-meaning-source'},el('h3',{},source.file),el('dl',{},...source.rows.map(([label,value])=>el('div',{},el('dt',{},label),el('dd',{},value)))),...source.citations.map(citation=>evidenceDisclosure(el,data.record.inputs,citation)))));
   const accept=el('input',{type:'checkbox'});
   const claim=el('textarea',{id:'preparation-handoff-claim',rows:'3',maxlength:'3000'});claim.value=preparationClaim(data.record);
   const claimEdits=trackUnsaved(claim);
   const continueButton=btn('Continue to split check',async()=>{if(!accept.checked||continueButton.disabled)return;if(title.disabled||title.value!==data.title){showError(error,new Error('Save the preparation name before continuing, or restore its saved name.'));title.focus();return}continueButton.disabled=true;accept.disabled=true;error.hidden=true;
    try{const prepared=await api('/preparations/'+id+'/handoff','POST',{revision:data.revision,review_hash:data.review_hash,confirm:true});
     const staged=await stageFiles([],prepared.files.map(f=>new File([f.content],f.name,{type:'text/plain'})));
     if(version===epoch){claimEdits.saved();onContinue({title:prepared.title,claim:claim.value,evaluation_intent:preparationIntent(data.record),files:staged.files,saved_binding:staged.configuration?.arguments||null,_manual:true})}
    }catch(e){if(version===epoch)showError(error,e)}finally{accept.checked=false;accept.disabled=false;continueButton.disabled=true}
   });continueButton.disabled=true;
   claim.addEventListener('input',()=>{claimEdits.changed();accept.checked=false;continueButton.disabled=true});
   accept.addEventListener('change',()=>{continueButton.disabled=!accept.checked});
   const intent=preparationIntent(data.record);
   const handoff=el('section',{class:'preparation-handoff'},el('p',{class:'eyebrow'},'Next · Check the split'),el('h2',{},'Carry the evidence forward.'),...(intent?[el('p',{},'Intended unseen unit: '+intent.unit+'. Copied from your preparation setup; review or edit it in the split check. This does not confirm an identity binding.')]:[]),el('p',{},'Use the saved choices and their original sources to prepare a new split check. Review your claim and the identity binding in the new check. No model or Sandbox call runs now.'),el('div',{class:'field'},el('label',{for:claim.id},'Claim for the new split check'),el('p',{class:'hint'},claim.value?'Copied from your original preparation request. Edit it if needed; copying it does not confirm the identity binding.':'Optional starting text. You will finish and review the claim in the new split check.'),claim),el('label',{class:'preparation-consent'},accept,el('span',{},'I reviewed this saved preparation’s observation identities, repeated-record policy, subjects, partition mapping and exclusions against the source documentation.')),continueButton);
   const editor=el('section',{hidden:'true'});
   const edit=btn('Edit preparation choices',async()=>{if(!await mayLeavePreparation()||version!==epoch)return;title.value=data.title;handoff.hidden=true;accept.checked=false;continueButton.disabled=true;editor.replaceChildren(policyEditor({data,api,onSaved:()=>{if(version===epoch)detail(id,++epoch)}}));editor.hidden=false;editor.querySelector('select')?.focus()},'secondary');
   const sources=el('section',{},el('h2',{},'Original files'),...Object.entries(data.record.inputs).map(([name,content])=>preparationSourceView({el,btn,name,content})));
   shell(data.title,'Unconfirmed preparation · Counts recomputed from the saved sources and choices. These are preparation counts, not an overlap result.',btn('← All preparations',()=>go(),'text-button'),counts,interpretation,preparationProvenance(el,data.record),
    el('div',{class:'actions'},btn('Download draft',()=>download(data.record)),edit,btn('Reopen latest version',async()=>{if(await mayLeavePreparation()&&version===epoch)detail(id,++epoch)},'secondary')),
    el('p',{class:'hint'},'Edit observation, subject and partition choices here. Preview their effect before saving. The draft remains unconfirmed.'),editor,form,error,sources,el('details',{class:'preparation-source'},el('summary',{},'Recorded preparation choices'),el('pre',{tabindex:'0'},JSON.stringify(data.record.policies,null,2))),handoff,remove,confirmation);
  }catch(e){if(version===epoch)shell('Could not open this preparation.','It may have been deleted or belong to a different browser session.',el('p',{class:'error',role:'alert'},e.message),btn('Try again',()=>detail(id,++epoch)),btn('All preparations',()=>go(),'secondary'))}
 }
 function stop(){epoch++}
 async function route(hash){const version=++epoch;if(hash==='#prepare'){const initial=pendingIntake||{};pendingIntake=null;document.querySelector('#page-name').textContent='Prepare dataset files';main.replaceChildren(el('p',{role:'status'},'Checking preparation availability…'));let proposalConfigured=null,draftCapacity=null;try{const capability=await api('/preparations/capabilities');draftCapacity=capability.draft_capacity??null;if(typeof capability.proposal_configured==='boolean')proposalConfigured=capability.proposal_configured}catch{}if(version!==epoch)return true;main.replaceChildren(nativePreparation({el,btn,api,initial,proposalConfigured,draftCapacity,onSaved:go,onManual:onContinue,isCurrent:()=>version===epoch}));main.focus({preventScroll:true});return true;}if(hash==='#preparations'){await list(version);return true}const match=hash.match(/^#preparation\/([a-f0-9]{32})$/);if(match){await detail(match[1],version);return true}return false}
 return {route,stop,queueIntake(seed){pendingIntake={title:seed.title,claim:seed.claim,evaluation_intent:seed.evaluation_intent};location.hash='prepare'}};
}
