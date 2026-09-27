// This is recorded user context, never a model conclusion or binding confirmation.
export function preparationClaim(record){
 const messages=record?.model_proposal?.approved_payload?.messages;
 if(!Array.isArray(messages)||messages.length!==2||messages[1]?.role!=='user')return '';
 try{
  const claim=JSON.parse(messages[1].content).claim;
  if(typeof claim!=='string')return '';
  const length=Array.from(claim.trim()).length;
  return length>=10&&length<=3000?claim:'';
 }catch{return ''}
}

// Never derive this from model prose, identifiers or the claim's wording.
export function preparationIntent(record){
 const value=record?.model_proposal?.approved_payload?.evaluation_intent;
 if(value?.target!=='unseen_entities'||typeof value.unit!=='string')return null;
 const unit=value.unit.trim();
 if(!unit||Array.from(unit).length>120)return null;
 return {target:'unseen_entities',unit};
}
