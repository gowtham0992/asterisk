import test from 'node:test';
import assert from 'node:assert/strict';
import {readCitations} from '../static/preparation-citations.mjs';
test('editing the first citation retains every untouched citation in order',()=>{
 const second={file:'b.md',start_line:1,end_line:1},entries=[{read:()=>({file:'a.md',start_line:2,end_line:2})},{citation:second}];
 const result=readCitations(entries,{'a.md':'first\ncorrected','b.md':'independent supporting passage'});
 assert.deepEqual(result,[{file:'a.md',start_line:2,end_line:2},second]);result[1].file='mutated';assert.equal(second.file,'b.md');
});
test('every citation must resolve, including new and collapsed passages',()=>{
 const valid={citation:{file:'a',start_line:1,end_line:1}};
 assert.throws(()=>readCitations([valid,{citation:{file:'a',start_line:null,end_line:null}}],{a:'one'}));
 assert.throws(()=>readCitations([valid,{citation:{file:'missing',start_line:1,end_line:1}}],{a:'one'}));
 assert.throws(()=>readCitations([],{a:'one'}));assert.throws(()=>readCitations(Array(21).fill(valid),{a:'one'}));assert.equal(readCitations(Array(20).fill(valid),{a:'one'}).length,20);
});
