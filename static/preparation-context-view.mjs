// Group only identical source coordinates inside one preparation record.
// File choices stay separate; shared text never implies shared scientific meaning.
export function preparationContextView(el,context,{repair=false}={}){
 const passages=[],indices=new Map();
 const choices=context.choices.map(choice=>{
  const refs=[];
  for(const passage of choice.passages){
   const key=JSON.stringify([passage.file,passage.start,passage.end,passage.text,passage.shortened]);
   let index=indices.get(key);
   if(index===undefined){index=passages.length;indices.set(key,index);passages.push({...passage,files:[]})}
   if(!passages[index].files.includes(choice.file))passages[index].files.push(choice.file);
   if(!refs.includes(index+1))refs.push(index+1);
  }
  return el('div',{class:'preparation-choice'},el('h4',{},choice.file),
   el('p',{},'Observation: ',el('code',{},choice.sample)),
   el('p',{},'Subject: ',el('code',{},choice.entity)),el('p',{},choice.repeats),
   el('p',{class:'hint'},refs.length?'Supporting passage'+(refs.length>1?'s':'')+': '+refs.join(', '):'No valid supporting passage available. Read the original record and source files.'));
 });
 return el('section',{class:'preparation-context'},
  el('h3',{},repair?'Original preparation · before reassignment':'Imported preparation · review again'),
  ...(repair?[el('p',{class:'identity-warning'},'This retained preparation describes the original split. The repair changed partition assignments in the split table; use Revision context to inspect those changes. The embedded source split has not been rewritten.')]:[]),
  el('p',{class:'hint'},'These choices came from '+context.file+'. They have not been independently verified here. Prior confirmation does not transfer.'),
  ...choices,
  ...(passages.length?[el('h4',{},'Supporting source passages'),el('p',{class:'hint'},'Shared passages appear once. Each label lists the source files whose choices cite it; you still review the meaning of every choice.')]:[]),
  ...passages.map((p,i)=>el('div',{class:'preparation-passage'},el('p',{},el('strong',{},'Passage '+(i+1)), ' · Cited for '+p.files.join(', ')),
   el('blockquote',{},p.text,p.shortened?' … [passage shortened]':'',el('cite',{},p.file+' · lines '+p.start+'–'+p.end+' · embedded source')))),
  ...(context.more?[el('p',{class:'hint'},context.more+' additional source decisions are in the preparation record.')]:[]));
}
