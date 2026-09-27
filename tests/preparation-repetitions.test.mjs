import test from 'node:test';
import assert from 'node:assert/strict';
import {renderRepetitions} from '../static/preparation-repetitions.mjs';
function node(tag){return {tag,children:[],ownerDocument:{createElement:node},append(...children){this.children.push(...children)}}}
const text=n=>[n.textContent||'',...n.children.map(text)].join(' ');
const source={file:'observations.csv',identity_counts:{capture:{repeated_values:7}},repeated_examples:{capture:[{value:'<a> ',record_count:4,locations:[{record_number:1,reference:{file:'observations.csv',line_start:2,line_end:3}},{record_number:21,reference:{file:'observations.csv',line_start:23,line_end:23}}]}]}};
test('repeat evidence shows later record locations, full count, and literal untrusted IDs',()=>{
 const root=node('div');renderRepetitions(root,source,'capture');
 assert.match(text(root),/Showing 1 of 7 repeated values/);assert.match(text(root),/4 source records/);assert.match(text(root),/Record 21 · observations.csv · lines 23–23/);assert.match(text(root),/"<a> "/);assert.match(text(root),/ordinary categories/);
});
test('row identity exposes repetitions without choosing an observation column',()=>{
 const root=node('div');renderRepetitions(root,source);assert.match(text(root),/before using row identities/);assert.match(text(root),/capture/);
});
test('absent metadata does not claim that records are unique',()=>{
 const root=node('div');renderRepetitions(root,{});assert.equal(root.children.length,0);
});

test('original repeated records are read lazily and rendered as literal text',()=>{
 const interactive=tag=>({tag,children:[],events:{},ownerDocument:{createElement:interactive},append(...children){this.children.push(...children)},addEventListener(name,fn){this.events[name]=fn}});
 const root=interactive('div'),calls=[];
 renderRepetitions(root,source,'capture',ref=>{calls.push(ref);return {text:'<script>do not execute</script>\noriginal record',shortened:true}});
 const all=n=>[n,...n.children.flatMap(all)];
 const passage=all(root).find(n=>n.className==='source-passage');
 assert.equal(calls.length,0,'collapsed examples do not read large source files');
 passage.open=false;passage.events.toggle();assert.equal(calls.length,0);
 passage.open=true;passage.events.toggle();passage.events.toggle();
 assert.deepEqual(calls,[source.repeated_examples.capture[0].locations[0].reference]);
 assert.equal(all(passage).find(n=>n.tag==='pre').textContent,'<script>do not execute</script>\noriginal record');
 assert.match(text(passage),/first 4,000 characters/);
});

test('CSV header and record remain separate literal excerpts',()=>{
 const interactive=tag=>({tag,children:[],events:{},ownerDocument:{createElement:interactive},append(...children){this.children.push(...children)},addEventListener(name,fn){this.events[name]=fn}});
 const headerRef={file:'observations.csv',line_start:1,line_end:2};
 const root=interactive('div');
 renderRepetitions(root,{...source,header_reference:headerRef},'capture',ref=>({text:ref===headerRef?'"capture\nname",subject,partition':'a,p1,train',shortened:false}));
 const all=n=>[n,...n.children.flatMap(all)];const passage=all(root).find(n=>n.className==='source-passage');
 passage.open=true;passage.events.toggle();
 assert.deepEqual(all(passage).filter(n=>n.tag==='pre').map(n=>n.textContent),['"capture\nname",subject,partition','a,p1,train']);
 assert.match(text(passage),/Original CSV header/);assert.match(text(passage),/Original record/);
});
