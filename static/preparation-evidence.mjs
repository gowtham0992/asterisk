import {manualRange,sourceLines} from './preparation-support/evidence-selection.mjs';
// Resolve coordinates against original inputs. A saved/model-supplied quote is ignored.
export function citedPassage(inputs,citation){
 if(!citation||typeof citation.file!=='string'||!inputs||!Object.hasOwn(inputs,citation.file)||typeof inputs[citation.file]!=='string')return {error:'The cited source file is unavailable.'};
 const lines=sourceLines(inputs[citation.file]);
 try{manualRange(citation.start_line,citation.end_line,lines.length)}catch{return {error:'The cited line range is unavailable or exceeds 40 lines.'}}
 const selected=lines.slice(citation.start_line-1,citation.end_line);
 if(Array.from(selected.join('\n')).length>8000)return {error:'This passage exceeds the 8,000-character evidence limit. Read the original file.'};
 return {lines:selected.map((text,index)=>({number:citation.start_line+index,text}))};
}
export function evidenceDisclosure(el,inputs,citation){
 const range=citation.start_line===citation.end_line?'line '+citation.start_line:'lines '+citation.start_line+'–'+citation.end_line;
 const body=el('div',{class:'preparation-cited-body'});
 const disclosure=el('details',{class:'preparation-cited-passage'},el('summary',{},'Read '+citation.file+' · '+range),body);
 let loaded=false;
 disclosure.addEventListener('toggle',()=>{
  if(!disclosure.open||loaded)return;loaded=true;
  const passage=citedPassage(inputs,citation);
  if(passage.error){body.append(el('p',{class:'error',role:'status'},passage.error));return}
  body.append(el('p',{class:'hint'},'Original file text. The citation identifies a passage; you decide whether it supports the saved choices.'),
   el('div',{class:'preparation-cited-lines',role:'region',tabindex:'0','aria-label':'Source passage from '+citation.file},...passage.lines.map(line=>el('div',{},el('span',{class:'preparation-cited-number','aria-label':'Line '+line.number},line.number),el('code',{},line.text)))));
 });
 return disclosure;
}
