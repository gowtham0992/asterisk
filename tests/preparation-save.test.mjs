import test from 'node:test';
import assert from 'node:assert/strict';
import {createDraftSaver} from '../static/preparation-save.mjs';
test('lost response keeps the same key without automatically retrying',async()=>{
 const calls=[];let ids=0;
 const save=createDraftSaver(async(path,method,body)=>{calls.push(body);if(calls.length===1)throw Error('connection lost');return {id:'saved'}},()=>String(++ids));
 await assert.rejects(save('Draft',{choices:['a']}),/connection lost/);
 assert.equal(calls.length,1);
 assert.deepEqual(await save('Draft',{choices:['a']}),{id:'saved'});
 assert.equal(calls[0].request_id,calls[1].request_id);
 assert.equal(ids,1);
 await save('Draft',{choices:['b']});await save('Renamed',{choices:['b']});
 assert.equal(ids,3);
});
