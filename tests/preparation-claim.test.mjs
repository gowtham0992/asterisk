import test from 'node:test';
import assert from 'node:assert/strict';
import {preparationClaim} from '../static/preparation-claim.mjs';
const record=(content,role='user')=>({model_proposal:{approved_payload:{messages:[{role:'system',content:'instructions'},{role,content}]}}});
test('original user claim survives verbatim without accepting a model conclusion',()=>{
 const claim='  Subjects with <unseen> identities must be absent from training.  ';
 assert.equal(preparationClaim(record(JSON.stringify({claim}))),claim);
 assert.equal(preparationClaim(record(JSON.stringify({claim}),'assistant')),'');
});
test('legacy drafts and malformed or oversized context remain blank',()=>{
 for(const candidate of [{},null,record('not json'),record('null'),record('{"claim":5}'),record(JSON.stringify({claim:'x'.repeat(3001)}))])assert.equal(preparationClaim(candidate),'');
});

test('intent is explicit retained user context, never guessed from a claim',async()=>{
 const {preparationIntent}=await import('../static/preparation-claim.mjs');
 const value={target:'unseen_entities',unit:'  frogs  '};
 assert.deepEqual(preparationIntent({model_proposal:{approved_payload:{evaluation_intent:value}}}),{target:'unseen_entities',unit:'frogs'});
 for(const evaluation_intent of [null,{target:'new_sites',unit:'hospitals'},{target:'unseen_entities',unit:''},{target:'unseen_entities',unit:'x'.repeat(121)}])
  assert.equal(preparationIntent({model_proposal:{approved_payload:{evaluation_intent}}}),null);
 assert.equal(preparationIntent(record(JSON.stringify({claim:'Unseen frogs must be absent from training.'}))),null);
});
