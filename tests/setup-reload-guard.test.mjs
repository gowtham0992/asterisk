import test from 'node:test';
import assert from 'node:assert/strict';
import {protectLocalDrafts} from '../static/setup-reload-guard.js';
test('reload warning follows current unsaved work and never handles route changes',()=>{
 const listeners=new Map();const target={addEventListener:(k,v)=>listeners.set(k,v),removeEventListener:k=>listeners.delete(k)};
 let pending=false;const dispose=protectLocalDrafts(target,()=>pending);
 const fire=()=>{const event={prevented:false,preventDefault(){this.prevented=true}};listeners.get('beforeunload')(event);return event};
 assert.equal(fire().prevented,false);
 pending=true;assert.equal(fire().prevented,true);assert.equal(fire().returnValue,'');
 pending=false;assert.equal(fire().prevented,false);
 assert.deepEqual([...listeners.keys()],['beforeunload']);dispose();assert.equal(listeners.size,0);
});
