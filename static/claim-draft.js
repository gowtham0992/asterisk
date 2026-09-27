// Suggest wording only. This never confirms the meaning of an identity column.
export function connectClaimDraft({unit,purpose,claim,onChange=()=>{},allowAutomatic=true}){
 let automatic=allowAutomatic&&!claim.value.trim();
 const update=()=>{
  if(!automatic)return;
  const subject=unit.value.trim();
  claim.value=purpose.value==='unseen_entities'&&subject?`Evaluation ${subject} must be absent from training.`:'';
  onChange();
 };
 const edited=()=>{automatic=false};
 unit.addEventListener('input',update);
 purpose.addEventListener('change',update);
 claim.addEventListener('input',edited);
 update();
 return {update};
}
