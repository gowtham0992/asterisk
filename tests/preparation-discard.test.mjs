import test from 'node:test';
import assert from 'node:assert/strict';
import {confirmDiscard} from '../static/preparation-discard.js';
class Node{
 constructor(tag){this.tag=tag;this.children=[];this.events={};this.isConnected=true}
 setAttribute(k,v){this[k]=v}addEventListener(k,fn){this.events[k]=fn}
 append(...nodes){this.children.push(...nodes)}showModal(){this.open=true}
 focus(){document.activeElement=this}close(){this.open=false}remove(){this.isConnected=false}
}
function setup(){const previous=new Node('input');globalThis.document={activeElement:previous,createElement:tag=>new Node(tag),body:new Node('body')};return previous}
const buttons=dialog=>dialog.children.at(-1).children;
test('one dialog for concurrent requests; keep editing restores focus and resolves false',async()=>{
 const previous=setup(),first=confirmDiscard(),second=confirmDiscard();assert.equal(first,second);
 const dialog=document.body.children[0],keep=buttons(dialog)[0];assert.equal(dialog.open,true);assert.equal(document.activeElement,keep);assert.equal(document.body.children.length,1);
 keep.events.click();assert.equal(await first,false);assert.equal(await second,false);assert.equal(dialog.isConnected,false);assert.equal(document.activeElement,previous);
});
test('Escape cancels; explicit discard resolves true and removes the dialog',async()=>{
 setup();let prevented=false;const cancel=confirmDiscard(),first=document.body.children[0];first.events.cancel({preventDefault(){prevented=true}});assert.equal(await cancel,false);assert.equal(prevented,true);
 const discard=confirmDiscard(),second=document.body.children.at(-1);buttons(second)[1].events.click();assert.equal(await discard,true);assert.equal(second.open,false);assert.equal(second.isConnected,false);
});
