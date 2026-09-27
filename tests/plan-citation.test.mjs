import test from 'node:test';
import assert from 'node:assert/strict';
import {renderPlanCitation} from '../static/investigations.js';
const el=(tag,attrs,...children)=>({tag,attrs,children});
const text=n=>typeof n==='object'&&n!==null?n.children.map(text).join(' '):String(n??'');
test('CSV excerpts never imply documented identity meaning in either setup mode',()=>{
 for(const manual of [true,false]){
  const rendered=renderPlanCitation(el,x=>el('span',{},x),{file:'DATA.CSV',quote:'sample,subject,split',start_line:1,end_line:1},manual);
  assert.match(text(rendered),/Identity meaning unverified/);
  assert.match(text(rendered),/sample,subject,split/);
  assert.doesNotMatch(text(rendered),/Reference passage|Source citation/);
 }
});
test('documentation retains the exact passage and line attribution without interpreting it',()=>{
 const rendered=renderPlanCitation(el,x=>el('span',{},x),{file:'notes.md',quote:'subject is NOT a patient ID.',start_line:4,end_line:4},false);
 assert.match(text(rendered),/subject is NOT a patient ID\./);
 assert.match(text(rendered),/notes.md · lines 4–4/);
 assert.match(text(rendered),/Exact quote checked/);
});
