import test from 'node:test';
import assert from 'node:assert/strict';
import {preparationSourceView} from '../static/preparation-source-view.js';
class Element {
 constructor(tag,attrs={},...children){this.tag=tag;Object.assign(this,attrs);this.children=children.flat();this.events={};this.value=''}
 append(...nodes){this.children.push(...nodes)}
 replaceChildren(...nodes){this.children=nodes}
 addEventListener(k,fn){this.events[k]=fn}
 querySelector(){return null}
}
const all=n=>n instanceof Element?[n,...n.children.flatMap(all)]:[];
const text=n=>n instanceof Element?[n.textContent||'',...n.children.map(text)].join(' '):String(n);
const find=(root,p)=>all(root).find(p);
const button=(root,name)=>find(root,n=>n.tag==='button'&&text(n).trim()===name);
function setup(content){const el=(...args)=>new Element(...args);const root=preparationSourceView({el,btn:(label,onclick,cls)=>el('button',{onclick,class:cls},label),name:'source.csv',content});return root}
test('lazy reader finds literal text past the old truncation limit and leaves inputs unchanged',()=>{
 const content=Array.from({length:301},(_,i)=>i===204?'needle[1],<script>text</script>':('record '+i+' ').repeat(10)).join('\r\n');
 const root=setup(content);assert.equal(all(root).filter(n=>n.tag==='code').length,0);
 root.open=true;root.events.toggle();
 assert.equal(all(root).filter(n=>n.tag==='code').length,60);
 const query=find(root,n=>n.type==='search');query.value='NEEDLE[1]';button(root,'Find').onclick();
 assert.match(text(root),/1 matching lines/);assert.match(text(root),/Lines 181–240 of 301/);
 const selected=find(root,n=>n.class==='source-line-selected');assert.equal(selected['data-source-line'],'205');assert.match(text(selected),/<script>text<\/script>/);assert.equal(all(root).filter(n=>n.tag==='script').length,0);
 const before=text(root);root.events.toggle();assert.equal(text(root),before,'reopening does not reset search');
 query.value='absent';query.events.input();button(root,'Next match').onclick();assert.match(text(root),/No matching lines/);assert.equal(find(root,n=>n.class==='source-line-selected'),undefined);
});
test('last-page navigation, invalid locations and empty files are explicit',()=>{
 const root=setup(Array.from({length:125},(_,i)=>'record '+i).join('\n'));root.open=true;root.events.toggle();
 const line=find(root,n=>n.type==='number');line.value='125';button(root,'Go to line').onclick();assert.match(text(root),/Lines 121–125 of 125/);assert.equal(button(root,'Next lines').disabled,true);
 line.value='126';button(root,'Go to line').onclick();assert.match(text(root),/Choose a line between 1 and 125/);
 const empty=setup('');empty.open=true;empty.events.toggle();assert.match(text(empty),/Empty source/);button(empty,'Go to line').onclick();assert.match(text(empty),/This file has no lines/);
});
