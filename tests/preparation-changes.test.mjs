import test from 'node:test';
import assert from 'node:assert/strict';
import {renderPreparationChanges,renderEvidenceChanges,renderObservationChanges} from '../static/preparation-changes.mjs';
function node(tag){return {tag,children:[],ownerDocument:{createElement:node},append(...children){this.children.push(...children)}}}
const text=n=>[n.textContent||'',...n.children.map(text)].join(' ');
test('citation-only correction shows exact before and after passages',()=>{
 const root=node('div');renderEvidenceChanges(root,{'data.csv':{evidence:[{file:'notes.txt',start_line:4,end_line:4}]}},{'data.csv':{evidence:[{file:'notes.txt',start_line:3,end_line:4}]}});
 assert.match(text(root),/Before: notes.txt · lines 4–4/);assert.match(text(root),/After: notes.txt · lines 3–4/);
 assert.match(text(root),/does not confirm its meaning/);
});
test('reordering the same citations does not report an evidence edit',()=>{
 const root=node('div'),a={file:'a.txt',start_line:1,end_line:2},b={file:'b.txt',start_line:2,end_line:3};
 renderEvidenceChanges(root,{x:{evidence:[a,b]}},{x:{evidence:[b,a]}});assert.equal(root.children.length,0);
});
test('removing a citation is explicit',()=>{
 const root=node('div');renderEvidenceChanges(root,{x:{evidence:[{file:'<notes>',start_line:1,end_line:1}]}},{x:{evidence:[]}});
 assert.match(text(root),/After: No supporting passage/);
});
test('unchanged totals cannot hide swapped partitions; examples retain exact source coordinates',()=>{
 const root=node('div');renderPreparationChanges(root,{available:true,source_records:100,changed_records:2,changed_fields:{sample:0,entity:0,partition:2},examples:[{source:{file:'data.csv',line_start:2,line_end:3},changed_fields:['partition'],before:{partition:'train'},after:{partition:'test'}}]});
 const view=text(root);assert.match(view,/2 of 100 original source records/);assert.match(view,/Showing 1 of 2/);assert.match(view,/data.csv · lines 2–3/);assert.match(view,/Before "train" After "test"/);
});
test('unavailable comparison never implies zero changes',()=>{
 const root=node('div');renderPreparationChanges(root,{available:false,reason:'Original proposal blocked'});
 assert.match(text(root),/Original proposal blocked/);assert.doesNotMatch(text(root),/0 of/);
});
test('zero changes is explicit without an empty examples section',()=>{
 const root=node('div');renderPreparationChanges(root,{available:true,source_records:2,changed_records:0,changed_fields:{sample:0,entity:0,partition:0},examples:[]});
 assert.match(text(root),/0 of 2/);assert.doesNotMatch(text(root),/Showing/);
});
test('row identity replacement remains visible without executable before rows',()=>{
 const root=node('div');renderObservationChanges(root,{x:{sample:{column:'obs'},repeats:'distinct'}},{x:{sample:{row:true},repeats:'distinct'}});
 assert.match(text(root),/Row numbers give every source record/);
 assert.match(text(root),/could not produce rows/);
 assert.match(text(root),/Before: Column "obs"/);assert.match(text(root),/After: Each source record is a separate observation/);
 assert.match(text(root),/Exact observation expressions/);
});
test('nested lookup edits are detected while object key order is ignored',()=>{
 const a={lookup:{file:'m.csv',on:{column:'a'}}},b={lookup:{file:'m.csv',on:{column:'b'}}};
 const root=node('div');renderObservationChanges(root,{x:{sample:a}},{x:{sample:b}});assert.equal(root.children.length,1);
 const unchanged=node('div');renderObservationChanges(unchanged,{x:{sample:a}},{x:{sample:{lookup:{on:{column:'a'},file:'m.csv'}}}});assert.equal(unchanged.children.length,0);
});
test('combining repeats requires meaning even with unchanged identity',()=>{
 const root=node('div');renderObservationChanges(root,{x:{sample:{column:'obs'},repeats:'distinct'}},{x:{sample:{column:'obs'},repeats:'collapse'}});
 assert.match(text(root),/documented retransmission meaning/);assert.doesNotMatch(text(root),/Row numbers/);
});
