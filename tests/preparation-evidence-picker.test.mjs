import test from 'node:test';
import assert from 'node:assert/strict';
import {mountEvidencePicker} from '../static/preparation-evidence-picker.js';
class Node{
 constructor(tag,text,cls){this.tag=tag;this.textContent=text;this.className=cls;this.children=[];this.events={};this.dataset={};this.value=''}
 append(...children){this.children.push(...children)}replaceChildren(...children){this.children=children}
 setAttribute(k,v){this[k]=v}addEventListener(k,fn){this.events[k]=fn}focus(){}
 querySelectorAll(tag){return this.children.flatMap(n=>[...(n.tag===tag?[n]:[]),...n.querySelectorAll(tag)])}
 querySelector(tag){return this.querySelectorAll(tag)[0]}
}
function setup(content){
 const node=(...args)=>new Node(...args),parent=node('div'),doc=node('select'),start=node('input'),end=node('input');let changes=0;
 const refresh=mountEvidencePicker({node,parent,doc,start,end,files:{'notes.txt':content},invalidate(){changes++},message(){}});
 doc.value='notes.txt';doc.events.change();
 const buttons=()=>parent.querySelectorAll('button'),named=t=>buttons().find(n=>n.textContent===t),line=n=>buttons().find(b=>b.dataset.line===String(n));
 return {parent,start,end,doc,refresh,named,line,changes:()=>changes};
}
test('paging reaches lines beyond 200 without changing citation and retains cross-page selection',()=>{
 const s=setup(Array.from({length:241},(_,i)=>'line '+(i+1)).join('\n'));
 s.line(60).events.click();const before=s.changes();s.named('Next source lines').events.click();
 assert.equal(s.changes(),before);assert.equal(s.start.value,60);s.line(61).events.click();assert.equal(s.end.value,61);
 for(let i=0;i<3;i++)s.named('Next source lines').events.click();assert.ok(s.line(241));assert.equal(s.named('Next source lines').disabled,true);
 s.refresh();assert.equal(s.named('Next source lines').disabled,true);
});
test('restoring a late citation displays its page and selection',()=>{
 const s=setup(Array(301).fill('text').join('\r\n'));s.start.value='301';s.end.value='301';s.start.events.input();
 assert.equal(s.line(301)['aria-pressed'],'true');assert.equal(s.named('Next source lines').disabled,true);
});
test('long source lines are bounded in visible and accessible text without changing numbering',()=>{
 const s=setup('x'.repeat(1000000)+'\nActual definition');const first=s.line(1);
 assert.ok(first['aria-label'].length<2100);assert.ok(first.children[1].textContent.length<2100);
 assert.match(first['aria-label'],/display shortened/);s.line(2).events.click();assert.equal(s.start.value,2);
});
test('search reaches late matching lines without editing the citation, wraps, and handles no results',()=>{
 const lines=Array(301).fill('ordinary text');lines[204]='Patient identity definition';lines[300]='patient identity note';
 const s=setup(lines.join('\n'));s.line(2).events.click();const before=s.changes();
 const query=s.parent.querySelector('input');query.value='PATIENT';s.named('Find next').events.click();
 assert.ok(s.line(205));assert.equal(s.start.value,2);assert.equal(s.changes(),before);
 s.named('Find next').events.click();assert.ok(s.line(301));
 s.named('Find next').events.click();assert.ok(s.line(205));
 query.value='missing phrase';s.named('Find next').events.click();
 assert.ok(s.parent.querySelectorAll('p').some(n=>n.textContent==='No matching lines in this document.'));
 assert.equal(s.changes(),before);
});
test('search input and Enter never bubble into policy edits or submit the form',()=>{
 const s=setup('identity definition');const query=s.parent.querySelector('input');query.value='identity';
 let stopped=0,prevented=0;const before=s.changes();
 query.events.input({stopPropagation(){stopped++}});
 query.events.keydown({key:'Enter',stopPropagation(){stopped++},preventDefault(){prevented++}});
 assert.equal(stopped,2);assert.equal(prevented,1);assert.equal(s.changes(),before);assert.equal(s.start.value,'');
});
