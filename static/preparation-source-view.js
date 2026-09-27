import {sourcePage,sourceMatches} from './source-reader.js';
// Read-only navigation over saved text. Display limits never change stored files.
export function preparationSourceView({el,btn,name,content}) {
 const body=el('div',{class:'source-reader-body'});
 const disclosure=el('details',{class:'source-reader'},el('summary',{},name,el('span',{},' · '+new TextEncoder().encode(content).length.toLocaleString()+' bytes')),body);
 let loaded=false;
 disclosure.addEventListener('toggle',()=>{
  if(!disclosure.open||loaded)return;loaded=true;
  let page=0,selected=null,matches={total:0,lines:[]},index=-1;
  const query=el('input',{type:'search','aria-label':'Find text in '+name,maxlength:'200',placeholder:'Find an identifier or phrase'});
  const line=el('input',{type:'number',min:'1',step:'1','aria-label':'Go to line in '+name,placeholder:'Line'});
  const status=el('p',{class:'hint',role:'status'}),view=el('div');
  function paint(){
   const result=sourcePage(content,page);page=result.page;
   const previous=btn('Previous lines',()=>{page--;paint()},'secondary'),next=btn('Next lines',()=>{page++;paint()},'secondary');
   previous.disabled=page===0;next.disabled=page===result.pages-1;
   view.replaceChildren(el('div',{class:'source-reader-lines',tabindex:'0','aria-label':'Original text of '+name},...result.lines.map(row=>el('div',{'data-source-line':String(row.number),class:selected===row.number?'source-line-selected':''},el('span',{class:'source-line-number'},String(row.number)),el('code',{},row.text||' ',row.shortened?' … [long line shortened]':'')))),el('div',{class:'source-reader-nav'},previous,el('span',{role:'status'},result.total?'Lines '+result.lines[0].number+'–'+result.lines.at(-1).number+' of '+result.total:'Empty source'),next));
  }
  function jump(value){
   const total=sourcePage(content).total;
   if(!Number.isInteger(value)||value<1||value>total){status.textContent=total?'Choose a line between 1 and '+total+'.':'This file has no lines.';return}
   selected=value;page=Math.floor((value-1)/60);paint();view.querySelector('[data-source-line="'+value+'"]')?.scrollIntoView({block:'nearest'});
  }
  function find(){
   matches=sourceMatches(content,query.value);index=matches.lines.length?0:-1;
   status.textContent=!query.value?'Enter text to find.':matches.total?matches.total+' matching lines · literal, case-insensitive search.'+(matches.total>1000?' Navigation covers the first 1,000 matches.':''):'No matching lines.';
   if(index>=0)jump(matches.lines[index]);else{selected=null;paint()}
  }
  query.addEventListener('input',()=>{matches={total:0,lines:[]};index=-1;selected=null;status.textContent='';paint()});
  query.addEventListener('keydown',event=>{if(event.key==='Enter'){event.preventDefault();find()}});
  line.addEventListener('keydown',event=>{if(event.key==='Enter'){event.preventDefault();jump(Number(line.value))}});
  const nextMatch=btn('Next match',()=>{if(!matches.lines.length){find();return}index=(index+1)%matches.lines.length;jump(matches.lines[index]);status.textContent='Match '+(index+1)+' of '+matches.lines.length+' · line '+matches.lines[index]+(matches.total>1000?' · first 1,000 matching lines':'')},'secondary');
  body.append(el('p',{class:'hint'},'Original saved text. Search covers the complete file. Lines are text locations, not CSV record numbers. Long lines display at most 2,000 characters; the draft download retains every character.'),el('div',{class:'source-reader-tools'},el('div',{},query,btn('Find',find,'secondary'),nextMatch),el('div',{},line,btn('Go to line',()=>jump(Number(line.value)),'secondary'))),status,view);
  paint();
 });
 return disclosure;
}
