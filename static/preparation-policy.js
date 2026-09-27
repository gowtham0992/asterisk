import {sourceReader} from './preparation-support/source-excerpt.mjs';
import {preparationClaim} from './preparation-claim.mjs';
import {renderPreparationChanges,renderEvidenceChanges,renderObservationChanges} from './preparation-changes.mjs';
import {trackUnsaved} from './preparation-unsaved.mjs';
import {renderLineage} from './preparation-support/lineage-preview.mjs';
import {createPolicyFields} from './preparation-fields.js?v=repeat-excerpts-2';
import {createCitationEditor} from './preparation-citations.mjs';
export function policyEditor({data,api,onSaved,previewPolicy,savePolicy}) {
 const node=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n};
 const form=node('form',undefined,'preparation-policy');
 const messageNode=node('p');messageNode.setAttribute('role','status');messageNode.tabIndex=-1;
 const result=node('div');result.setAttribute('aria-live','polite');
 let sequence=0,pending=false,preview=null,initialized=false,restoringEvidence=false;
 const unsaved=trackUnsaved(form);
 const unsavedNotice=node('p','Unsaved choices · Save before leaving this page. Recovery restores the model response, not these edits.','hint');unsavedNotice.hidden=true;
 const save=node('button','Save reviewed choices','primary');save.type='button';save.hidden=true;
 const message=(text,error=false)=>{if(restoringEvidence)return;messageNode.textContent=text;messageNode.className=error?'error':'hint'};
 const invalidate=()=>{if(restoringEvidence)return;if(initialized){unsaved.changed();unsavedNotice.hidden=false}sequence++;preview=null;save.hidden=true;result.replaceChildren();message('Choices changed. Preview before saving. Nothing has been confirmed.')};
 const readSource=data.record.original_spec?sourceReader(data.record.inputs,data.record.original_spec):null;
 const fields=createPolicyFields({readSource,node,invalidate,message,restoredLabel:data.proposed?"Keep proposed":"Keep saved"});
 const controls=[];
 const originalClaim=preparationClaim(data.record);
 if(originalClaim){const context=node('section',undefined,'preparation-claim');context.append(node('p','Original preparation claim','eyebrow'),node('p',originalClaim,'preparation-claim-text'),node('p','Recorded from the preparation request. Check each choice against this claim; it has not been scientifically verified.','hint'));form.append(context)}
 for(const source of data.sources){
  const saved={sample:source.sample,entity:source.entity,partition:source.partition,...data.record.policies[source.file]};
  const section=node('fieldset'),legend=node('legend',source.file);section.append(legend);
  if(source.identity_counts){
   const census=node('details',undefined,'preparation-identity-census');
   census.append(node('summary','Compare identity counts across source columns'));
   census.append(node('p','Counts cover every source record before transforms or lookups. Shared values can mean a subject, a repeated observation, or something else. Use documentation to decide. Unusable IDs are missing, empty, non-text, over 4,096 characters, or contain a null character.','hint'));
   const table=node('table');table.append(node('caption','Full-file text identity counts'));
   const head=node('tr');for(const label of ['Column','Distinct IDs','Records with repeated IDs','Unusable IDs'])head.append(node('th',label));const thead=node('thead');thead.append(head);table.append(thead);
   const body=node('tbody');for(const [column,counts]of Object.entries(source.identity_counts).slice(0,40)){const row=node('tr');row.append(node('th',column));for(const value of [counts.distinct_values,counts.records_with_repeated_values,counts.unusable_records])row.append(node('td',value.toLocaleString()));body.append(row)}table.append(body);census.append(table);
   if(Object.keys(source.identity_counts).length>40)census.append(node('p','Showing the first 40 columns. Counts for a selected direct column appear under its identity control.','hint'));
   section.append(census);
  }
  const workspace=node('div',undefined,'preparation-policy-workspace'),choices=node('div',undefined,'preparation-policy-choices');
  const observation=node('section',undefined,'preparation-decision-group');
  observation.append(node('p','01 / Observation','eyebrow'),node('h3','What counts as one measurement?'),node('p','An observation is a scan, recording or measurement. Several observations may come from the same subject. Repeated records are only combined when your policy says they represent the same observation.','hint'));
  const sample=fields.identityChoice('What identifies one observation?',source,source.sample,saved.sample,observation,true);
  const repeats=fields.select('How should repeated observation IDs be handled?',[['distinct','Keep distinct observations; reject repeated IDs'],['collapse','Combine retransmissions of the same observation']],observation);repeats.value=saved.repeats;
  choices.append(observation);
  const binding=fields.bindingChoices(source,choices,saved);
  const evidence=node('div',undefined,'preparation-evidence');evidence.append(node('p','Source evidence','eyebrow'),node('h3','Read alongside your choices'),node('p','Use the dataset documentation to justify the identities and split. Selecting a passage records where to look; it does not verify its meaning.','hint'));
  const citations=createCitationEditor({node,fields,inputs:data.record.inputs,citations:saved.evidence,invalidate,message,hydrate:fn=>{restoringEvidence=true;try{fn()}finally{restoringEvidence=false}}});evidence.append(citations.element);
  workspace.append(choices,evidence);section.append(workspace);form.append(section);
  controls.push({file:source.file,sample,repeats,binding,citations,saved});
 }
 const submit=node('button',data.proposed?'Preview reviewed choices':'Preview changed choices','primary');submit.type='submit';
 form.append(submit,unsavedNotice,messageNode,result,save);
 initialized=true;
 function busy(value){pending=value;for(const control of form.querySelectorAll('input,select,button'))control.disabled=value;if(!value)for(const c of controls)c.citations.refresh()}
 form.addEventListener('input',event=>{if(!pending&&event.target.closest('fieldset'))invalidate()});
 form.addEventListener('submit',async event=>{
  event.preventDefault();if(pending)return;invalidate();const version=sequence;busy(true);message('Recomputing every source record…');
  try{
   const policies={};
   for(const c of controls)policies[c.file]={sample:c.sample(),repeats:c.repeats.value,...c.binding(),evidence:c.citations.read()};
   const response=await (previewPolicy?previewPolicy(policies):api('/preparations/'+data.id+'/preview','POST',{revision:data.revision,policies}));if(version!==sequence)return;
   preview=response;result.replaceChildren(node('h3',data.proposed?'Starting proposal → reviewed choices':'Saved draft → proposed edit'));
   for(const [key,label]of [['train','Training observations'],['test','Evaluation observations'],['excluded','Excluded observations']])result.append(node('p',`${label}: ${response.previous_population?.[key]??'—'} → ${response.population[key]}`));
   renderObservationChanges(result,Object.fromEntries(controls.map(c=>[c.file,c.saved])),policies);
   renderPreparationChanges(result,response.source_changes);
   renderEvidenceChanges(result,Object.fromEntries(controls.map(c=>[c.file,c.saved])),policies);
   renderLineage(result,response.lineage,data.record.inputs,response.spec);
   result.append(node('p','Every source was recomputed. These counts are not an overlap result. Saving keeps the draft unconfirmed.','hint'));save.hidden=false;message('Preview ready. Save only if these choices match your documentation.');
  }catch(error){message(error.message,true);messageNode.focus()}finally{busy(false)}
 });
 save.addEventListener('click',async()=>{if(pending||!preview)return;busy(true);message('Saving reviewed choices…');
  try{const saved=await (savePolicy?savePolicy(preview.record):api('/preparations/'+data.id,'PUT',{title:data.title,revision:data.revision,record:preview.record,store_inputs:true}));unsaved.saved();unsavedNotice.hidden=true;onSaved(saved);}
  catch(error){message(error.message,true)}finally{busy(false)}
 });
 message('Editing retains the original files. Preview and save explicitly; no confirmation or provider request is made.');
 return form;
}
