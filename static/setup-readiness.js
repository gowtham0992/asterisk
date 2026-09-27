// UI readiness only. Scientific sufficiency and bindings are checked later.
export function setupReadiness({target,unit,title,claim,fileCount,manual,consent,reading=false,saving=false}){
 const length=value=>Array.from(String(value||'').trim()).length;
 const checks=[
  {id:'evaluation-target',label:target?'Choose a supported evaluation task':'Choose what should be new at evaluation time',ok:target==='unseen_entities'},
  {id:'evaluation-unit',label:'Name who or what should be unseen',ok:length(unit)>0&&length(unit)<=120},
  {id:'investigation-title',label:'Give this receipt a name',ok:length(title)>0&&length(title)<=120},
  {id:'investigation-claim',label:'Write an evaluation claim of 10–3,000 characters',ok:length(claim)>=10&&length(claim)<=3000},
  {id:'investigation-files',label:'Add your split and identity source files',ok:fileCount>0},
  {id:'proposal-consent',label:'Choose manual setup or authorize a model proposal',ok:manual===true||consent===true},
 ];
 const missing=checks.filter(check=>!check.ok);
 return {ready:missing.length===0&&!reading&&!saving,complete:checks.length-missing.length,total:checks.length,
  next:missing[0]||null,message:saving?'Saving this setup…':reading?'Reading selected files locally…':missing.length?missing[0].label:manual?'Ready to choose columns. No model proposal will run.':'Ready to request a proposal. Your column review comes next.'};
}
