import {sourcePage,sourceMatches} from './source-reader.js';
import {selectLine,manualRange,sourceLines} from './preparation-support/evidence-selection.mjs';
export function mountEvidencePicker({node,invalidate,message,doc,start,end,files,parent}){
 let selected=null,page=0,total=0,pages=1;
 const help=node('p','Select the first and last supporting lines. A single line is also valid.','muted');
 const status=node('p','No evidence selected.','selection-status');status.setAttribute('role','status');
 const list=node('div',undefined,'evidence-lines');list.setAttribute('aria-label','Select supporting source lines');
 const navigation=node('div',undefined,'preparation-evidence-pages');
 const previous=node('button','Previous source lines','secondary'),next=node('button','Next source lines','secondary');
 const position=node('span');position.setAttribute('role','status');
 for(const button of [previous,next])button.type='button';navigation.append(previous,position,next);
 const clear=node('button','Clear evidence selection','secondary');clear.type='button';
 const search=node('div',undefined,'preparation-evidence-search');
 const searchLabel=node('label','Find in this document'),query=node('input');query.type='search';query.maxLength=200;
 query.setAttribute('aria-label','Find in this document');searchLabel.append(query);
 const find=node('button','Find next','secondary');find.type='button';
 const searchStatus=node('p','','muted');searchStatus.setAttribute('role','status');
 search.append(searchLabel,find,searchStatus);
 let searched='',matches=[],matchIndex=-1;
 function resetSearch(){searched='';matches=[];matchIndex=-1;searchStatus.textContent=''}
 function findNext(){
  const term=query.value.trim();if(!term){resetSearch();return}
  if(searched!==term){
   const result=sourceMatches(files[doc.value]||'',term);matches=result.lines;matchIndex=-1;searched=term;
   search.dataset.total=String(result.total);
  }
  if(!matches.length){searchStatus.textContent='No matching lines in this document.';return}
  matchIndex=(matchIndex+1)%matches.length;const line=matches[matchIndex];page=Math.floor((line-1)/60);render();
  searchStatus.textContent=`Matching line ${matchIndex+1} of ${search.dataset.total}: line ${line}.`+(Number(search.dataset.total)>matches.length?' Navigation shows the first 1,000 matching lines; narrow your search.':'');
  const target=[...list.querySelectorAll('button')].find(button=>Number(button.dataset.line)===line);
  target?.focus();
 }
 find.addEventListener('click',findNext);
 query.addEventListener('input',event=>{event.stopPropagation();resetSearch()});
 query.addEventListener('keydown',event=>{if(event.key==='Enter'){event.preventDefault();event.stopPropagation();findNext()}});
 const refresh=()=>{previous.disabled=page===0;next.disabled=page>=pages-1};
 function paint(){
  for(const button of list.querySelectorAll('button')){const line=Number(button.dataset.line);button.setAttribute('aria-pressed',String(Boolean(selected&&line>=selected.start&&line<=selected.end)))}
  status.textContent=selected?`Selected ${doc.value}, ${selected.start===selected.end?'line '+selected.start:'lines '+selected.start+'–'+selected.end}.`+(selected.anchor?' Select an end line to extend the range.':' Select another line to start over.'):'No evidence selected.';
 }
 function render(){
  const view=sourcePage(files[doc.value]||'',page);page=view.page;total=view.total;pages=view.pages;
  list.replaceChildren();list.scrollTop=0;navigation.hidden=pages===1;refresh();
  position.textContent=`Lines ${view.lines[0]?.number||0}–${view.lines.at(-1)?.number||0} of ${total}. Page ${page+1} of ${pages}.`;
  for(const line of view.lines){
   const shortened=line.shortened?' [display shortened; original text retained]':'';
   const button=node('button',undefined,'evidence-line');button.type='button';button.dataset.line=String(line.number);
   button.setAttribute('aria-label',`Select line ${line.number}: ${line.text||'(blank line)'}${shortened}`);
   button.append(node('span',String(line.number),'line-number'),node('span',(line.text||'(blank line)')+shortened));
   button.addEventListener('click',()=>{try{selected=selectLine(selected,line.number,total);start.value=selected.start;end.value=selected.end;paint();changed()}catch(error){message(error.message,true)}});
   list.append(button);
  }
  paint();
 }
 function changed(){invalidate();message('Evidence changed. Preview the policy again.')}
 function reset(){selected=null;start.value='';end.value='';paint()}
 previous.addEventListener('click',()=>{page--;render()});next.addEventListener('click',()=>{page++;render()});
 clear.addEventListener('click',()=>{reset();changed();list.querySelector('button')?.focus()});
 doc.addEventListener('change',()=>{reset();resetSearch();page=0;render();changed()});
 for(const field of [start,end])field.addEventListener('input',()=>{
  try{selected=manualRange(Number(start.value),Number(end.value),sourceLines(files[doc.value]||'').length);page=Math.floor((selected.start-1)/60);render()}catch{selected=null;paint()}
 });
 parent.append(help,search,list,navigation,status,clear);
 return refresh;
}
