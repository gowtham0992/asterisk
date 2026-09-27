import test from 'node:test';
import assert from 'node:assert/strict';
import {preparationContextView} from '../static/preparation-context-view.mjs';
const el=(tag,attrs,...children)=>({tag,attrs,children});
const all=n=>typeof n==='object'?[n,...n.children.flatMap(all)]:[];
const text=n=>typeof n==='string'?n:(n?.children||[]).map(text).join(' ');
const passage={file:'notes.txt',start:21,end:21,text:'Each recording is one frog.',shortened:false};
const choice=(file,passages=[passage])=>({file,sample:'Each source record',entity:'RecordID',repeats:'Keep observations distinct',passages});
test('shared passage appears once with both file associations and separate choices',()=>{
 const result=preparationContextView(el,{file:'preparation-review.json',choices:[choice('train.csv'),choice('test.csv')],more:0});
 assert.equal(all(result).filter(n=>n.tag==='blockquote').length,1);
 assert.match(text(result),/Cited for train.csv, test.csv/);
 assert.equal(text(result).match(/Subject:  RecordID/g).length,2);
 assert.match(text(result),/Prior confirmation does not transfer/);
});
test('different coordinates and missing evidence are not silently combined',()=>{
 const result=preparationContextView(el,{file:'record',choices:[choice('a'),choice('b',[{...passage,start:22,end:22}]),choice('c',[])],more:3},{repair:true});
 assert.equal(all(result).filter(n=>n.tag==='blockquote').length,2);
 assert.match(text(result),/No valid supporting passage/);
 assert.match(text(result),/original split/);assert.match(text(result),/3 additional/);
});
test('untrusted text remains a text child and duplicate citations do not duplicate references',()=>{
 const unsafe={...passage,text:'<script>not code</script>'};
 const result=preparationContextView(el,{file:'record',choices:[choice('a',[unsafe,unsafe])],more:0});
 assert.equal(all(result).find(n=>n.tag==='blockquote').children[0],unsafe.text);
 assert.equal(all(result).filter(n=>n.tag==='script').length,0);
 assert.match(text(result),/Supporting passage: 1/);
});
