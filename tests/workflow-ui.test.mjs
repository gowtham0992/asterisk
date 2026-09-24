import assert from 'node:assert/strict';
import {createInvestigations} from '../static/investigations.js';
// Small DOM adapter: exercise the real route/renderer with the API's public shape.
class Node {
 constructor(tag,attrs={},...children){this.tag=tag;this.attrs=attrs;this.children=children.flat().filter(x=>x!=null);Object.assign(this,attrs);this.parentElement={};this.classList={toggle(){},add(){}}}
 append(...x){this.children.push(...x.flat().filter(x=>x!=null))}
 prepend(...x){this.children.unshift(...x)}
 replaceChildren(...x){this.children=x.flat().filter(x=>x!=null)}
 setAttribute(k,v){this.attrs[k]=v}
 getAttribute(k){return this.attrs[k]}
 addEventListener(){} after(){} before(){} focus(){} scrollIntoView(){}
 querySelector(tag){return this.children.find(x=>x?.tag===tag)||this.children.filter(x=>x instanceof Node).map(x=>x.querySelector(tag)).find(Boolean)||null}
}
const elements=new Map();
globalThis.document={querySelector(s){if(!elements.has(s))elements.set(s,new Node('div'));return elements.get(s)}};
globalThis.location={hash:'#investigation/'+'a'.repeat(24)};
const el=(...a)=>new Node(...a),main=new Node('main'),messages=[];
const receipt={id:'a'.repeat(24),title:'Public shape',claim:'My own claim',state:'review',model:'super',files:[],binding_profiles:{},setup_mode:'manual',plan:{scope:'MODEL CLAIM MUST NOT BE THE HEADING',binding:null,citations:[],steps:[],limitations:[]}};
const api=async path=>path.endsWith('/config')?{supported_categories:['entity_overlap']}:path==='/investigations'?[receipt]:receipt;
const ui=createInvestigations({el,btn:(text,handler)=>el('button',{onclick:handler},text),api,main,label:text=>el('span',{},text),toast:x=>messages.push(x)});
await ui.route(location.hash);
const text=node=>node instanceof Node?node.children.map(text).join(' '):String(node);
assert.match(text(main),/My own claim/);
assert.match(text(main),/Check these columns/);
assert.doesNotMatch(text(main),/Cannot read properties|MODEL CLAIM/);
assert.deepEqual(messages,[]);
console.log('Public API plan -> actual renderer passed');
receipt.walkthrough='specimen-v1';
await ui.route(location.hash);
assert.match(text(main),/Review what each column means/);
assert.match(text(main),/supplied with the example, not inferred by a model/);
receipt.state='complete';
receipt.result={verdict:{verdict:'clear'}};
receipt.result_integrity={matches:false,reason:'Tampered evidence'};
await ui.route(location.hash);
assert.match(text(main),/Read the actual result before continuing/);
assert.doesNotMatch(text(main),/Hand over the revised evidence/);
assert.match(text(main),/The retained receipt is inconsistent/);
console.log('Walkthrough guidance respects inconsistent evidence');
