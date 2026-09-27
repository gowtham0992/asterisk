import test from 'node:test';
import assert from 'node:assert/strict';
import {connectClaimDraft} from '../static/claim-draft.js';
const input=value=>({value,events:{},addEventListener(type,fn){this.events[type]=fn}});
test('subject wording follows inputs until the user edits it, including deliberate clearing',()=>{
 const unit=input(''),purpose=input('unseen_entities'),claim=input('');let changes=0;
 connectClaimDraft({unit,purpose,claim,onChange:()=>changes++});
 unit.value='patients';unit.events.input();assert.equal(claim.value,'Evaluation patients must be absent from training.');
 unit.value='specimens';unit.events.input();assert.equal(claim.value,'Evaluation specimens must be absent from training.');
 claim.value='Only specimens from the selected site must be absent.';claim.events.input();
 unit.value='speakers';unit.events.input();assert.equal(claim.value,'Only specimens from the selected site must be absent.');
 claim.value='';claim.events.input();unit.events.input();assert.equal(claim.value,'');assert.ok(changes>0);
});
test('saved wording is preserved and unsupported tasks never acquire suggested claims',()=>{
 const unit=input('patients'),purpose=input('future_observations'),claim=input('');
 connectClaimDraft({unit,purpose,claim});assert.equal(claim.value,'');
 purpose.value='unseen_entities';purpose.events.change();assert.match(claim.value,/patients/);
 purpose.value='new_sites';purpose.events.change();assert.equal(claim.value,'');
 const saved=input('My exact saved wording.');connectClaimDraft({unit,purpose,claim:saved});
 unit.value='specimens';unit.events.input();assert.equal(saved.value,'My exact saved wording.');
});
test('restoring a deliberately empty claim does not invent saved wording',()=>{
 const unit=input('patients'),purpose=input('unseen_entities'),claim=input('');
 connectClaimDraft({unit,purpose,claim,allowAutomatic:false});
 unit.events.input();assert.equal(claim.value,'');
});
