import test from 'node:test';
import assert from 'node:assert/strict';
import {syntheticExample,specimenExample} from '../static/synthetic-example.js';
class Element{
 constructor(tag,attrs={},...children){this.tag=tag;Object.assign(this,attrs);this.children=children.flat();this.events={}}
 scrollIntoView(){}
 append(...children){this.children.push(...children)}
 addEventListener(name,fn){this.events[name]=fn}
}
const all=n=>n instanceof Element?[n,...n.children.flatMap(all)]:[];
const text=n=>n instanceof Element?n.children.map(text).join(' '):String(n);
test('exploring is read-only; starting returns the same source fixture in a fresh object',()=>{
 let started=[];const el=(...args)=>new Element(...args);
 const root=syntheticExample({el,btn:(label,onclick)=>el('button',{onclick},label),onStart:x=>started.push(x)});
 assert.equal(started.length,0);assert.equal(all(root).filter(n=>n.tag==='table').length,0);
 root.open=true;root.events.toggle();root.events.toggle();
 assert.equal(started.length,0);assert.equal(all(root).filter(n=>n.tag==='table').length,1);
 assert.match(text(root),/not a saved check or a Sandbox result/);
 assert.equal(all(root).filter(n=>n.class==='example-shared').length,2);
 assert.deepEqual(all(root).filter(n=>n.tag==='pre').map(n=>n.children[0]),specimenExample().files.map(f=>f.content));
 all(root).find(n=>n.tag==='button').onclick();assert.equal(started.length,1);
 assert.deepEqual(started[0],specimenExample());started[0].files[0].content='changed';
 assert.match(specimenExample().files[0].content,/a,train\nb,test\nc,test/);
 assert.equal(started[0].result,undefined);assert.equal(started[0].preflight_confirmation,undefined);
});
