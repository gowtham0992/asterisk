import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

function harness(){
 const nodes=new Map();const node=id=>{if(!nodes.has(id))nodes.set(id,{checked:true,value:id==='study-experience'?'yes':id==='study-exposure'?'no':'Independent ML evaluation',hidden:true,disabled:false,addEventListener(event,fn){this[event]=fn},replaceChildren(){},reset(){}});return nodes.get(id)};
 let calls=0,resolve,reject,timers=0;
 const context=vm.createContext({document:{getElementById:node,addEventListener(){}},fetch(){calls++;return new Promise((r,j)=>{resolve=r;reject=j})},renderLadder(){},crypto:{subtle:{async digest(){return new Uint8Array(32)}},randomUUID(){return 'participant'}},TextEncoder,Uint8Array,performance:{now:()=>100},Date,setInterval(){timers++;return 1},clearInterval(){},setTimeout(){}});
 const source=fs.readFileSync(new URL('../static/receipt-study.js',import.meta.url),'utf8').replace(/^import .*\n/,'');
 vm.runInContext(source,context);
 return {node,get calls(){return calls},get timers(){return timers},submit:()=>node('study-screen').submit({preventDefault(){}}),resolve:()=>resolve({ok:true,text:async()=>'{"schema":"fixture"}'}),reject:()=>reject(new Error('offline'))};
}

test('double submit while the receipt loads starts one fetch and one timer',async()=>{
 const h=harness();const first=h.submit();const second=h.submit();assert.equal(h.calls,1);h.resolve();await Promise.all([first,second]);assert.equal(h.timers,1);assert.equal(h.node('study-screen').hidden,true);
 await h.submit();assert.equal(h.calls,1);
});

test('failed loading can be retried without claiming that a study started',async()=>{
 const h=harness();const first=h.submit();h.reject();await first;assert.match(h.node('study-status').textContent,/No task has started/);assert.equal(h.timers,0);
 const retry=h.submit();assert.equal(h.calls,2);h.resolve();await retry;assert.equal(h.timers,1);
});
