// Setup attribution is retained context, never provider attestation or a verdict.
export function receiptSetup(el,investigation){
 const context=investigation.preparation_context;
 const current=['manual','repair_proposal'].includes(investigation.setup_mode)
  ?'Column binding reviewed without another model call.'
  :investigation.setup_mode==='plan_revision'?'Revised plan · no new proposal inference.'
  :'Nemotron '+investigation.model;
 const children=[el('p',{},current)];
 if(context?.model_proposal){
  const proposal=context.model_proposal;
  children.unshift(el('p',{},'Input preparation · recorded model proposal'),
   el('p',{},proposal.model+' · '+proposal.provider));
  children.push(el('p',{class:'hint'},'The model proposed how to extract the tables. Application code measured the overlap. The retained proposal is not provider-authenticated proof.'));
 }else if(context?.error){
  children.push(el('p',{class:'hint'},context.error));
 }else if(context){
  children.push(el('p',{class:'hint'},'Prepared inputs retained; no model proposal is recorded.'));
 }
 return el('div',{class:'receipt-setup'},...children);
}
