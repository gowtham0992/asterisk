import test from 'node:test';
import assert from 'node:assert/strict';
import {setupBackup,readSetupBackup} from '../static/setup-backup.js';
const seed={title:'unfinished',claim:'',evaluation_intent:{target:'',unit:''},files:[{name:'source/identities.csv',content:'\uFEFFid,subject\r\na,S1\r\n'}],_manual:true,preflight_confirmation:{confirmed:true},result:{verdict:'clear'},saved_binding:{entity_column:'invented'},consent:true};
test('unfinished setup survives serialization with exact source bytes, without authority',()=>{
 const restored=readSetupBackup(JSON.stringify(setupBackup(seed)));
 assert.deepEqual(restored,{title:seed.title,claim:'',evaluation_intent:seed.evaluation_intent,files:seed.files,_manual:true});
 const malicious={...setupBackup(seed),result:seed.result,consent:true,preflight_confirmation:seed.preflight_confirmation};
 assert.deepEqual(readSetupBackup(JSON.stringify(malicious)),restored);
});
test('backup rejects malformed, duplicate, traversal and oversized inputs',()=>{
 const base=setupBackup(seed);
 for(const bad of [{...base,version:2},{...base,title:'x'.repeat(121)},{...base,files:[...base.files,...base.files]},{...base,files:[{name:'../bad.csv',content:''}]},{...base,files:[{name:'x.csv',content:'x'.repeat(10000001)}]}])assert.throws(()=>readSetupBackup(JSON.stringify(bad)));
 assert.throws(()=>readSetupBackup('{'));
});
import {restoreSetupFile} from '../static/setup-backup.js';
const delayed=()=>{let resolve,reject;const promise=new Promise((yes,no)=>{resolve=yes;reject=no});return {file:{size:100,text:()=>promise},resolve,reject}};
test('a pending import or new edits prevent a delayed restore from replacing work',async()=>{
 for(const reason of ['import','edit']){
  const read=delayed();let replaceable=true;
  const restoration=restoreSetupFile(read.file,{isCurrent:()=>true,canReplace:()=>replaceable});
  replaceable=false;read.resolve(JSON.stringify(setupBackup(seed)));
  await assert.rejects(restoration,/changed while reading/,reason);
 }
});
test('navigation discards both delayed backup results and stale read errors',async()=>{
 for(const failed of [false,true]){
  const read=delayed();let current=true;
  const restoration=restoreSetupFile(read.file,{isCurrent:()=>current,canReplace:()=>true});
  current=false;
  if(failed)read.reject(new Error('old page read failed'));else read.resolve(JSON.stringify(setupBackup(seed)));
  assert.equal(await restoration,null);
 }
});
test('stable restore succeeds and existing work is rejected before reading',async()=>{
 const text=JSON.stringify(setupBackup(seed));let reads=0;
 const file={size:text.length,text:async()=>{reads++;return text}};
 await assert.rejects(restoreSetupFile(file,{isCurrent:()=>true,canReplace:()=>false}),/unfinished work/);assert.equal(reads,0);
 assert.deepEqual(await restoreSetupFile(file,{isCurrent:()=>true,canReplace:()=>true}),readSetupBackup(text));assert.equal(reads,1);
});
