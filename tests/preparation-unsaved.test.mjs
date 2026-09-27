import test from 'node:test';
import assert from 'node:assert/strict';
import {createUnsavedRegistry} from '../static/preparation-unsaved.mjs';
function setup(){const listeners=new Map();return {listeners,registry:createUnsavedRegistry({addEventListener:(name,fn)=>listeners.set(name,fn),removeEventListener:name=>listeners.delete(name)})}}
function unload(listeners){let prevented=false;const event={preventDefault(){prevented=true}};listeners.get('beforeunload')?.(event);return {prevented,event}}
test('edits warn on unload; a preview or failed save does not clear them',()=>{
 const {registry,listeners}=setup(),state=registry.track({isConnected:true});
 assert.equal(listeners.size,0);state.changed();
 assert.equal(unload(listeners).prevented,true);assert.equal(unload(listeners).event.returnValue,'');
 assert.equal(registry.pending(),true);
 state.saved();assert.equal(listeners.size,0);assert.equal(unload(listeners).prevented,false);
});
test('detached editors cannot warn after navigation',()=>{
 const {registry,listeners}=setup(),node={isConnected:true},state=registry.track(node);state.changed();node.isConnected=false;
 assert.equal(unload(listeners).prevented,false);assert.equal(registry.pending(),false);
});
test('saving one editor does not discard another editor’s warning',()=>{
 const {registry,listeners}=setup(),a=registry.track({isConnected:true}),b=registry.track({isConnected:true});a.changed();b.changed();a.saved();assert.equal(unload(listeners).prevented,true);b.dispose();assert.equal(listeners.size,0);
});
test('cancelled navigation preserves edits; discarding removes the warning',async()=>{
 const {registry,listeners}=setup();registry.track({isConnected:true}).changed();
 let prompts=0;assert.equal(await registry.requestLeave(()=>{prompts++;return false}),false);
 assert.equal(registry.pending(),true);assert.equal(unload(listeners).prevented,true);
 assert.equal(await registry.requestLeave(()=>{prompts++;return true}),true);
 assert.equal(registry.pending(),false);assert.equal(listeners.size,0);
 assert.equal(await registry.requestLeave(()=>{throw Error('clean editors must not prompt')}),true);assert.equal(prompts,2);
});
test('cancel restores the current hash without remounting; a later navigation works',async()=>{
 const {createPreparationRouteGuard}=await import('../static/preparation-unsaved.mjs');
 let hash='#preparation/old',allow=true,renders=0;
 const guard=createPreparationRouteGuard({currentHash:()=>hash,restoreHash:value=>{hash=value},mayLeave:()=>allow});
 const route=async()=>{if(await guard())renders++};await route();
 allow=false;hash='#investigate';await route();assert.equal(hash,'#preparation/old');assert.equal(renders,1);
 allow=true;hash='#preparations';await route();assert.equal(renders,2);
 allow=false;hash='#prepare';await route();assert.equal(hash,'#preparations');assert.equal(renders,2);
});
test('only the latest route proceeds when a discard decision is shared',async()=>{
 const {createPreparationRouteGuard}=await import('../static/preparation-unsaved.mjs');
 let hash='#preparation/start',resolve;
 const decision=new Promise(r=>{resolve=r});
 const guard=createPreparationRouteGuard({currentHash:()=>hash,restoreHash:value=>{hash=value},mayLeave:()=>decision});
 hash='#prepare';const first=guard();hash='#preparations';const second=guard();resolve(true);
 assert.equal(await first,false);assert.equal(await second,true);assert.equal(hash,'#preparations');
});
