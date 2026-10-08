import {renderLadder,renderCitationReview} from './ladder-render.mjs?v=citations-1';
import {FINDINGS} from './ladder-view.mjs?v=ladder-6';

export function createLadderWorkspace({el,btn,api,main,toast}){
 let generation=0;
 const title=text=>{document.querySelector('#page-name').textContent=text};
 const link=(text,href)=>el('a',{class:'secondary',href},text);
 const evidenceAction=rid=>{
  const download=link('Download evidence + inputs (ZIP)',`/api/ladder/receipts/${rid}/export?format=zip`);download.hidden=true;
  const consent=el('input',{type:'checkbox',onchange:event=>{download.hidden=!event.target.checked}});
  return el('details',{},el('summary',{},'Include original inputs in an evidence ZIP'),el('p',{class:'hint'},'Includes every uploaded source file, including columns not sent to the model. Share only with authorized recipients.'),el('label',{},consent,' I want to include the uploaded source files.'),download);
 };
 const actions=rid=>el('div',{class:'chain-actions'},
  link('Download readable receipt',`/api/ladder/receipts/${rid}/export`),
  link('Download measurement JSON',`/api/ladder/receipts/${rid}/export?format=json`),
  evidenceAction(rid));
 async function route(hash){
  const g=++generation;
  const match=hash.match(/^#ladder\/([a-f0-9]{24})$/);
  if(hash!=='#ladders'&&!match)return false;
  title(match?'Ladder receipt':'Saved ladders');
  main.replaceChildren(el('p',{role:'status'},'Loading saved ladders…'));
  try{
   if(!match){
    const rows=await api('/ladder/receipts');if(g!==generation)return true;
    main.replaceChildren(el('section',{class:'hero'},el('div',{},el('h1',{},'Your independence ladders.'),
     el('p',{class:'lede'},'Keep the claim, every measured level, and its execution record together.'),
     link('Create an independence ladder','/static/ladder.html#propose'))),
     ...(rows.length?rows.map(r=>el('section',{class:'panel ladder-saved-card'},
      el('p',{class:'small-label'},r.execution==='sandbox_replay'?'Matched Sandbox replay':'Local measurement'),
      el('h2',{},el('a',{href:'#ladder/'+r.id},r.claim)),
      el('p',{},(FINDINGS[r.finding.status]?.title||r.finding.status)+' · '+r.finding.level),el('p',{class:'hint'},new Date(r.created_at).toLocaleString()))):
      [el('section',{class:'panel ladder-saved-card'},el('h2',{},'No saved ladders yet.'),
       el('p',{},'Measure a ladder and choose “Save to workspace”. A successful Sandbox replay is saved here automatically. No paid call is needed to save a local measurement.'))]));
    return true;
   }
   const r=await api('/ladder/receipts/'+match[1]);if(g!==generation)return true;
   const panel=el('section',{class:'ladder-panel'});renderLadder(panel,r.result);
   // A saved record was confirmed by its creator, not necessarily the current reader.
   for(const note of panel.querySelectorAll('.finding-confirmed'))note.textContent='Recorded confirmation: '+(r.result.confirmed_levels||[]).join(', ');
   const origin=r.binding_origin;
   const originText=origin?.kind==='recorded_model_proposal'?`Proposed by ${origin.model_name}, prompt ${origin.prompt_version}. Specification edited: ${origin.edited}; inputs changed: ${origin.inputs_changed}.`:(origin?.note||'This older receipt does not record proposal origin.');
   const scope=r.execution.kind==='sandbox_replay'?'Matched a fresh Nebius Sandbox replay, as attested by this Asterisk server.':'Measured on the Asterisk server. No Sandbox replay is recorded.';
   main.replaceChildren(el('div',{class:'ladder-page'},link('← All saved ladders','#ladders'),panel,renderCitationReview(r.citation_review),
    el('section',{class:'panel ladder-saved-card'},el('h2',{},'Keep the evidence.'),el('p',{},scope),el('p',{},originText),
     origin?.kind==='recorded_model_proposal'?el('details',{},el('summary',{},'Proposal origin'),el('pre',{},JSON.stringify(origin,null,2))):null,
     el('p',{class:'hint'},r.confirmation.scope+' HTML and JSON contain the full measurement and witnesses. The evidence ZIP also includes all uploaded inputs and instructions for recomputation from a separately trusted Asterisk installation. No new model or Sandbox call is made.'),
     actions(r.id),el('details',{},el('summary',{},'Saved extraction specification'),el('pre',{},JSON.stringify(r.spec,null,2))),
     el('details',{},el('summary',{},'Execution provenance'),el('pre',{},JSON.stringify(r.execution,null,2))),
     btn('Delete this saved ladder',async()=>{
      if(!window.confirm('Delete this ladder and its saved inputs from this workspace? Download any receipt you want to keep first.'))return;
      try{await api('/ladder/receipts/'+r.id,'DELETE');location.hash='#ladders'}catch(e){toast(e.message)}
     },'text-button'))));
  }catch(e){if(g===generation)main.replaceChildren(el('div',{class:'error',role:'alert'},e.message),link('Back to saved ladders','#ladders'))}
  return true;
 }
 return {route};
}
