import test from 'node:test';
import assert from 'node:assert/strict';
import {createPolicyFields} from '../static/preparation-fields.js';
class Node {
 constructor(tag,text,cls){Object.assign(this,{tag,textContent:text,className:cls,children:[],events:{},value:''});}
 append(...xs){this.children.push(...xs)} prepend(...xs){this.children.unshift(...xs)} replaceChildren(...xs){this.children=xs}
 setAttribute(k,v){this[k]=v} addEventListener(k,fn){(this.events[k]??=[]).push(fn)}
 querySelectorAll(tag){return this.children.flatMap(n=>[...(n.tag===tag?[n]:[]),...(n.querySelectorAll?.(tag)||[])])}
 querySelector(tag){return this.querySelectorAll(tag)[0]}
 change(value){this.value=value;for(const fn of this.events.change||[])fn()}
}
globalThis.Option=class extends Node{constructor(text,value){super('option',text);this.value=value}};
globalThis.document={createTextNode:text=>new Node('text',text)};
test('review exposes exact saved partition labels before preview and removes stale mapping on edits',()=>{
 const node=(...args)=>new Node(...args),root=node('div');
 const source={columns:['id','split'],entity:{column:'id'},partition:{value:'test'},partition_values:{split:[' Train ','test','val']}};
 const saved={entity:{column:'id'},partition:{column:'split',map:{' Train ':'train',test:'test',val:'excluded'}}};
 const fields=createPolicyFields({node,invalidate(){},message(){}});fields.bindingChoices(source,root,saved);
 const summary=root.querySelectorAll('p').find(n=>n.className==='identity-accounting');
 assert.equal(summary.hidden,false);assert.match(summary.textContent,/" Train " → Training/);assert.match(summary.textContent,/"val" → Excluded/);
 const select=root.querySelectorAll('select').find(n=>n.children.some(o=>o.value==='constant'));
 select.change('original');assert.equal(summary.textContent,'All records → Evaluation');
 select.change('col:split');assert.equal(summary.hidden,true);assert.equal(summary.textContent,'');
 select.change('restored');assert.match(summary.textContent,/"val" → Excluded/);assert.equal(summary.hidden,false);
});
