import test from 'node:test';
import assert from 'node:assert/strict';
import {savedReceiptStatus} from '../static/investigations.js';
test('saved completed checks expose distinct outcomes',()=>{
 for(const [verdict,label] of Object.entries({violation:'Overlap found',clear:'No overlap · reviewed',clear_pending_confirmation:'Needs confirmation',insufficient:'Insufficient evidence'}))assert.equal(savedReceiptStatus({state:'complete',verdict}),label);
});
test('unrun repair cannot inherit a definitive status',()=>{
 assert.equal(savedReceiptStatus({state:'review',verdict:'clear'}),'Ready for review');
 assert.equal(savedReceiptStatus({state:'failed',verdict:'violation'}),'Needs attention');
 assert.equal(savedReceiptStatus({state:'complete'}),'Check completed');
 assert.equal(savedReceiptStatus({state:'unknown'}),'Status unavailable');
});
