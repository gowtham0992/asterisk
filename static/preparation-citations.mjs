import {manualRange,sourceLines} from './preparation-support/evidence-selection.mjs';
export function readCitations(entries,inputs){
 if(!entries.length||entries.length>20)throw Error('Keep between 1 and 20 supporting passages.');
 return entries.map(entry=>{
  const citation=entry.read?entry.read():entry.citation;
  if(!Object.hasOwn(inputs,citation.file))throw Error('Choose the source for every supporting passage.');
  manualRange(citation.start_line,citation.end_line,sourceLines(inputs[citation.file]).length);
  return {...citation};
 });
}
export function createCitationEditor({node,fields,inputs,citations,invalidate,message,hydrate=fn=>fn()}){
 const root=node('div',undefined,'preparation-citations'),list=node('div');
 const add=node('button','Add supporting passage','secondary');add.type='button';
 const status=node('p',undefined,'hint');status.setAttribute('role','status');
 const entries=[];
 function refresh(){
  entries.forEach((entry,index)=>{
   entry.refresh?.();
   const c=entry.read?entry.read():entry.citation;
   entry.summary.textContent=`Passage ${index+1} · ${c.file||'Choose a source'}`+(c.start_line&&c.end_line?` · ${c.start_line===c.end_line?'line '+c.start_line:'lines '+c.start_line+'–'+c.end_line}`:' · Choose lines');
   entry.remove.disabled=entries.length===1;entry.remove.setAttribute('aria-label',`Remove passage ${index+1}`);
  });
  add.disabled=entries.length>=20;status.textContent=`${entries.length} of 20 supporting passages. Edit or remove each passage independently.`;
 }
 function append(citation,open=false){
  if(entries.length>=20)return;
  const panel=node('details',undefined,'preparation-citation'),summary=node('summary'),body=node('div');panel.append(summary,body);
  const remove=node('button','Remove passage','text-button');remove.type='button';
  const entry={citation:{...citation},panel,summary,remove,read:null};entries.push(entry);list.append(panel);
  function mount(){
   if(entry.read)return;
   hydrate(()=>{
   const doc=fields.select('Source documenting these choices',Object.keys(inputs).map(name=>[name,name]),body);
   const range=node('details',undefined,'preparation-evidence-range'),grid=node('div');range.append(node('summary','Edit line numbers'),grid);
   const a=node('div'),b=node('div');grid.append(a,b);
   const first=fields.number('First evidence line',a),last=fields.number('Last evidence line',b);
   range.addEventListener('invalid',()=>{panel.open=true;range.open=true;message('Choose valid source line numbers, starting at 1.',true)},true);
   entry.refresh=fields.evidencePicker(doc,first,last,inputs,body);body.append(range,remove);
   doc.value=citation.file||'';doc.dispatchEvent(new Event('change'));
   first.value=citation.start_line??'';last.value=citation.end_line??'';first.dispatchEvent(new Event('input'));
   entry.read=()=>({file:doc.value,start_line:Number(first.value),end_line:Number(last.value)});
   body.addEventListener('input',refresh);body.addEventListener('change',refresh);body.addEventListener('click',refresh);
   });
  }
  panel.addEventListener('toggle',()=>{if(panel.open)mount()});
  remove.addEventListener('click',()=>{if(entries.length<=1)return;const index=entries.indexOf(entry);entries.splice(index,1);panel.remove();invalidate();refresh();(entries[Math.min(index,entries.length-1)]?.summary||add).focus()});
  if(open){panel.open=true;mount()}
  refresh();
  return entry;
 }
 citations.forEach((citation,index)=>append(citation,index===0));
 add.addEventListener('click',()=>{
  const previous=entries.at(-1);const c=previous?.read?previous.read():previous?.citation;
  const entry=append({file:c?.file||'',start_line:null,end_line:null},true);if(entry){invalidate();entry.summary.focus()}
 });
 root.append(list,status,add);
 return {element:root,read:()=>readCitations(entries,inputs),refresh};
}
