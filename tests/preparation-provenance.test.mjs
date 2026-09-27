import test from 'node:test';
import assert from 'node:assert/strict';
import {preparationProvenance} from '../static/preparation-provenance.mjs';
const el=(tag,attrs,...children)=>({tag,attrs,children});
const text=n=>typeof n==='string'?n:(n?.children||[]).map(text).join(' ');
test('original model text stays a text child and is distinguished from current choices',()=>{
 const response='<script>wrong()</script>';
 const record={model_proposal:{approved_payload:{model:'recorded-model',provider:'recorded-provider',messages:[{role:'user',content:'original claim'}]},response_text:response,payload_hash:'abc',consent_recorded_at:'recorded-time'}};
 const result=preparationProvenance(el,record);
 assert.equal(result.tag,'details');assert.match(text(result),/Later edits may differ/);
 assert.match(text(result),/not provider-authenticated/);
 assert.ok(result.children.some(n=>n.tag==='details'&&n.children.some(c=>c.tag==='pre'&&c.children[0]===response)));
 assert.match(text(result),/original claim/);assert.match(text(result),/recorded-time/);
});
test('absent provenance does not claim human or model authorship',()=>{
 const result=text(preparationProvenance(el,{}));assert.match(result,/origin cannot be established/);
 assert.doesNotMatch(result,/human-reviewed/);
});
