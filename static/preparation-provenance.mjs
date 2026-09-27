// Recorded provenance is inspectable context, never provider attestation.
export function preparationProvenance(el,record){
 const model=record?.model_proposal;
 if(!model)return el('p',{class:'hint'},'No model proposal is recorded in this draft. Its origin cannot be established from the saved choices alone.');
 const payload=model.approved_payload||{};
 return el('details',{class:'preparation-source'},
  el('summary',{},'Recorded model proposal · '+(payload.model||'Model unspecified')),
  el('p',{class:'hint'},'This is the original proposal, not a confirmation of the current choices. Later edits may differ. The saved request and response are internally checked when reopened; this is not provider-authenticated evidence.'),
  el('dl',{class:'preparation-provenance'},
   el('dt',{},'Recorded provider'),el('dd',{},payload.provider||'Not recorded'),
   el('dt',{},'Upload consent recorded at'),el('dd',{},model.consent_recorded_at||'Not recorded'),
   el('dt',{},'Payload SHA-256'),el('dd',{},model.payload_hash||'Not recorded')),
  el('details',{},el('summary',{},'Original model response'),el('pre',{tabindex:'0'},model.response_text||'')),
  el('details',{},el('summary',{},'Exact approved request'),el('pre',{tabindex:'0'},JSON.stringify(payload,null,2))));
}
