import test from 'node:test';
import assert from 'node:assert/strict';
import {renderReceiptScope} from '../static/investigations.js';
const el=(tag,attrs,...children)=>({tag,attrs,children});
const text=n=>typeof n==='object'?n.children.map(text).join(' '):String(n);
test('overview exposes the claim, exact labels and excluded population',()=>{
 const n=renderReceiptScope(el,'Unseen lesions',{train_values:[' Train '],test_values:['test']},{ignored_rows:1003});
 assert.equal(n.attrs['aria-label'],'Scope of this result');
 assert.match(text(n),/Unseen lesions/);assert.match(text(n),/" Train "/);assert.match(text(n),/Excluded rows 1,003/);
});
test('missing measurement counts stay unknown rather than becoming zero',()=>{
 const n=renderReceiptScope(el,'Claim',{},{});assert.match(text(n),/Excluded rows Not recorded/);
 assert.match(text(renderReceiptScope(el,'Claim',{}, {ignored_rows:0})),/Excluded rows 0/);
});
