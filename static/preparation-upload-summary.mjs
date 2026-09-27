// Describe the actual consent-bound payload, never infer from selected filenames.
export function uploadSummary(ticket){
 const message=ticket?.messages?.find(item=>item.role==='user');
 let files;try{files=JSON.parse(message.content).files}catch{return []}
 if(!files||typeof files!=='object'||Array.isArray(files))return [];
 return Object.entries(files).map(([name,profile])=>{
  if(profile?.kind==='documentation'&&Array.isArray(profile.lines)){
   const total=Number.isInteger(profile.total_lines)?profile.total_lines:null;
   const sent=profile.lines.length,omitted=total===null?null:Math.max(0,total-sent);
   return {name,detail:`${sent} documentation lines included`+(total===null?'':` of ${total}`),
    warning:omitted?`${omitted} lines omitted. Definitions in those lines will not be seen by the model.`:''};
  }
  if(profile?.columns&&typeof profile.columns==='object'&&!Array.isArray(profile.columns)){
   const columns=Object.keys(profile.columns).length;
   return {name,detail:`${columns} column profiles`+(Number.isInteger(profile.records)?` across ${profile.records} records`:'')+'. Includes source values and counts.',warning:''};
  }
  return {name,detail:'Source content or structured profile. Inspect the exact payload below.',warning:''};
 });
}
export function uploadSummaryView(el,ticket){
 const rows=uploadSummary(ticket);
 return el('section',{class:'preparation-upload-summary','aria-label':'Files included in the model request'},
  el('h3',{},'What the model will receive'),
  el('p',{class:'hint'},'Your claim, filenames and the source material listed below. This is not anonymization; source values can identify people or samples.'),
  ...rows.map(row=>el('div',{class:'preparation-upload-item'},el('strong',{},row.name),el('p',{},row.detail),row.warning?el('p',{class:'preparation-upload-warning'},row.warning):null)));
}
