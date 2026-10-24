import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
class Node {
 constructor(tag,text=''){this.tag=tag;this.text=text;this.children=[];this.style={};this.attrs={}}
 append(...nodes){this.children.push(...nodes)}
 replaceChildren(...nodes){this.children=nodes}
 setAttribute(k,v){this.attrs[k]=v}
 get textContent(){return this.text+this.children.map(n=>n.textContent).join(' ')}
}
globalThis.Node=Node;
globalThis.document={querySelector:()=>null,createElement:t=>new Node(t),createTextNode:t=>new Node('#text',String(t))};
const {heroFigure}=await import('../static/ladder-figure.mjs');
const result=JSON.parse(readFileSync(new URL('../static/ladders/wsibench-report.json',import.meta.url)));
test('saved figure distinguishes contextual sites without changing measured evidence',async()=>{
 const before=JSON.stringify(result);globalThis.fetch=async()=>({ok:true,json:async()=>result});
 const panel=new Node('ol');await heroFigure(panel);
 const site=panel.children.find(n=>n.textContent.includes('site'));
 const patient=panel.children.find(n=>n.textContent.includes('patient'));
 assert.match(site.textContent,/Expected shared · context/);assert.match(site.className,/row-attribute/);
 assert.match(patient.textContent,/42/);assert.match(patient.className,/row-shared/);
 assert.match(panel.textContent,/0 of 208 test slides/);assert.equal(JSON.stringify(result),before);
});
test('saved figure fails visibly when its retained measurement is unavailable',async()=>{
 globalThis.fetch=async()=>({ok:false});const panel=new Node('ol');await heroFigure(panel);
 assert.match(panel.textContent,/could not be loaded/);assert.doesNotMatch(panel.textContent,/42/);
});
