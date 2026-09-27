import test from 'node:test';
import assert from 'node:assert/strict';
import {receiptSetup} from '../static/receipt-setup.mjs';
const el=(tag,attrs,...children)=>({tag,attrs,children});
const text=n=>typeof n==='string'?n:(n?.children||[]).map(text).join(' ');
test('preparation model remains visible after manual column review',()=>{
 const output=text(receiptSetup(el,{setup_mode:'manual',preparation_context:{model_proposal:{model:'recorded-model',provider:'Nebius'}}}));
 assert.match(output,/recorded-model · Nebius/);
 assert.match(output,/without another model call/);
 assert.match(output,/Application code measured/);
 assert.match(output,/not provider-authenticated/);
});
test('missing or invalid preparation never invents model participation',()=>{
 const missing=text(receiptSetup(el,{setup_mode:'manual'}));
 assert.doesNotMatch(missing,/Input preparation|Nemotron/);
 const invalid=text(receiptSetup(el,{setup_mode:'manual',preparation_context:{error:'Preparation could not be recomputed.'}}));
 assert.match(invalid,/could not be recomputed/);assert.doesNotMatch(invalid,/recorded model proposal/);
 const manual=text(receiptSetup(el,{setup_mode:'manual',preparation_context:{model_proposal:null}}));
 assert.match(manual,/no model proposal is recorded/);
});
