import assert from 'node:assert/strict';
import {createInvestigations,renderWitnessSource,renderBindingSummary,renderBindingInterpretation,renderBindingExamples} from '../static/investigations.js';
// Small DOM adapter: exercise the real route/renderer with the API's public shape.
class Node {
 constructor(tag,attrs={},...children){this.tag=tag;this.attrs=attrs;this.children=children.flat().filter(x=>x!=null);Object.assign(this,attrs);this.parentElement={};this.classList={toggle(){},add(){}}}
 append(...x){this.children.push(...x.flat().filter(x=>x!=null))}
 prepend(...x){this.children.unshift(...x)}
 replaceChildren(...x){this.children=x.flat().filter(x=>x!=null)}
 setAttribute(k,v){this.attrs[k]=v}
 getAttribute(k){return this.attrs[k]}
 addEventListener(type,handler){(this.events??={})[type]??=[];this.events[type].push(handler)} dispatch(type){for(const handler of this.events?.[type]||[])handler()} after(){} before(){} focus(){} scrollIntoView(){}
 querySelector(tag){return this.children.find(x=>x?.tag===tag)||this.children.filter(x=>x instanceof Node).map(x=>x.querySelector(tag)).find(Boolean)||null}
}
const elements=new Map();
globalThis.document={querySelector(s){if(!elements.has(s))elements.set(s,new Node('div'));return elements.get(s)}};
globalThis.location={hash:'#investigation/'+'a'.repeat(24)};
const el=(...a)=>new Node(...a),main=new Node('main'),messages=[];
const receipt={id:'a'.repeat(24),title:'Public shape',claim:'My own claim',state:'review',model:'super',files:[],binding_profiles:{},setup_mode:'manual',plan:{scope:'MODEL CLAIM MUST NOT BE THE HEADING',binding:null,citations:[],steps:[],limitations:[]}};
let previewReply,inputReply;
const api=async path=>path.endsWith('/inputs')?inputReply():path.endsWith('/binding-preview')?previewReply():path.endsWith('/config')?{supported_categories:['entity_overlap']}:path==='/investigations'?[receipt]:receipt;
const ui=createInvestigations({el,btn:(text,handler)=>el('button',{onclick:handler},text),api,main,label:text=>el('span',{},text),toast:x=>messages.push(x)});
await ui.route(location.hash);
const text=node=>node instanceof Node?node.children.map(text).join(' '):String(node);
assert.match(text(main),/My own claim/);
assert.match(text(main),/No usable CSV tables/);
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
receipt.state='review';delete receipt.result;delete receipt.result_integrity;delete receipt.walkthrough;
receipt.binding_profiles={'broken.csv':{error:'Malformed CSV. Check quotation marks, headers and row lengths.'}};
await ui.route(location.hash);
assert.match(text(main),/broken.csv/);
assert.match(text(main),/Malformed CSV/);
assert.doesNotMatch(text(main),/Check these columns/);
const all=node=>node instanceof Node?[node,...node.children.flatMap(all)]:[];
const revise=all(main).find(n=>n.tag==='a'&&n.attrs.href==='#revise-investigation/'+receipt.id);
assert.ok(revise,'Unreadable tables need a direct revision link');
receipt.binding_profiles['valid.csv']={rows:2,columns:{sample:{distinct:2},partition:{distinct:2}}};
await ui.route(location.hash);
assert.match(text(main),/Malformed CSV/);
assert.match(text(main),/Check these columns/);
console.log('Unreadable table errors remain visible with and without usable tables');
receipt.state='draft';receipt.plan=null;
await ui.route(location.hash);
assert.match(text(main),/Choose columns manually/);
assert.ok(all(main).some(n=>n.tag==='a'&&n.attrs.href==='#revise-investigation/'+receipt.id));
assert.match(text(main),/broken.csv/);
console.log('Saved draft offers manual recovery without a provider request');

const source={file:'wide.csv',csv_row:7,columns:['note','sample','partition','blank'],highlights:['sample','partition'],values:{sample:'001',partition:'test',note:'<img src=x onerror=alert(1)>',blank:''}};
const sourceBefore=JSON.stringify(source);
const renderedSource=renderWitnessSource(el,source);
const directFields=renderedSource.children.find(n=>n instanceof Node&&n.tag==='dl');
assert.match(text(directFields),/001/);
assert.match(text(directFields),/test/);
assert.doesNotMatch(text(directFields),/onerror|note/);
const other=renderedSource.children.find(n=>n instanceof Node&&n.tag==='details');
assert.equal(other.attrs.open,undefined);
assert.match(text(other),/Other source fields · 2/);
assert.match(text(other),/<img src=x onerror=alert\(1\)>/);
assert.match(text(other),/\(empty\)/);
assert.equal(all(renderedSource).filter(n=>n.tag==='dd').length,4);
assert.equal(JSON.stringify(source),sourceBefore);
console.log('Witness view emphasizes join fields without discarding original values');

const checked={arguments:{split_file:'split.csv',mapping_file:'map.csv',sample_column:'sample',partition_column:'partition',mapping_sample_column:'key',entity_column:'person',train_values:['fit','FIT'],test_values:['test ']},partition_rows:{fit:3,FIT:2,'test ':4},ignored_rows:7,text:'Exact original statement <script> retained.'};
const binding=renderBindingSummary(el,checked);
const population=all(binding).find(n=>n.attrs.class==='binding-population');
assert.deepEqual(all(population).filter(n=>n.tag==='strong').map(text),['5','4','7']);
assert.match(text(binding),/"test "/);
assert.match(text(binding),/not an overlap result/);
assert.equal(text(all(binding).find(n=>n.tag==='details').children[1]),checked.text);
assert.equal(all(binding).filter(n=>n.tag==='script').length,0);
console.log('Binding preview preserves exact labels and statement, sums source populations');

receipt.state='review';receipt.plan={binding:checked.arguments,citations:[],steps:[],limitations:[]};
receipt.binding_profiles={'split.csv':{rows:9,columns:{sample:{distinct:9},partition:{distinct:3}}},'map.csv':{rows:9,columns:{key:{distinct:9},person:{distinct:4}}}};
await ui.route(location.hash);
let resolvePreview;
previewReply=()=>new Promise(resolve=>{resolvePreview=resolve});
const checkButton=all(main).find(n=>n.tag==='button'&&text(n)==='Check these columns');
const pending=checkButton.onclick();
const labels=all(main).find(n=>n.id==='binding-test_values');
labels.value='changed';labels.dispatch('input');
resolvePreview(checked);await pending;
assert.equal(all(main).filter(n=>n.tag==='button'&&text(n)==='Confirm binding').length,0,'An old response must not restore confirmation after edits');
console.log('Edited binding discards an in-flight preview');
for(const trigger of ['change','edit-back','failure']){
 let resolve,reject;
 previewReply=()=>new Promise((yes,no)=>{resolve=yes;reject=no});
 const request=checkButton.onclick();
 if(trigger==='change')all(main).find(n=>n.id==='binding-entity_column').dispatch('change');
 else {labels.value='temporary';labels.dispatch('input');labels.value='changed';labels.dispatch('input')}
 if(trigger==='failure')reject(new Error('Obsolete request error'));else resolve(checked);
 await request;
 assert.equal(all(main).filter(n=>n.tag==='button'&&text(n)==='Confirm binding').length,0);
 assert.doesNotMatch(text(main),/Obsolete request error/);
}
previewReply=async()=>checked;
await checkButton.onclick();
assert.equal(all(main).filter(n=>n.tag==='button'&&text(n)==='Confirm binding').length,1,'A current response must remain usable');
console.log('Select changes, edit-back and stale failures are discarded; current preview recovers');

await ui.route(location.hash);
const reader=all(main).find(n=>n.attrs.class==='source-reader');reader.open=true;
inputReply=async()=>{throw new Error('Temporary source load failure')};
await reader.events.toggle[0]();
assert.match(text(reader),/Temporary source load failure/);
inputReply=async()=>({files:[{name:'notes.txt',content:'<script>plain source</script>'}]});
await all(reader).find(n=>n.tag==='button'&&text(n)==='Retry loading sources').onclick();
assert.match(text(reader),/<script>plain source<\/script>/);
assert.equal(all(reader).filter(n=>n.tag==='script').length,0);
assert.doesNotMatch(text(reader),/Temporary source load failure/);
console.log('Source reader recovers from load failure and renders supplied text without markup');

const interpretation=renderBindingInterpretation(el,{...checked.arguments,entity_column:'<img onerror=bad>',train_values:['fit','FIT'],test_values:['test ']});
assert.match(text(interpretation),/"test "/);
assert.match(text(interpretation),/"fit"/);
assert.match(text(interpretation),/"FIT"/);
assert.match(text(interpretation),/not a finding/);
assert.match(text(interpretation),/<img onerror=bad>/);
assert.equal(all(interpretation).filter(n=>n.tag==='img').length,0);
assert.match(text(renderBindingInterpretation(el,{})),/Not selected/);
receipt.plan.binding={...checked.arguments};
await ui.route(location.hash);
let editor=all(main).find(n=>n.attrs.class==='binding-controls');
assert.equal(editor.open,false,'Complete supplied selections start in readable review mode');
const identityChoice=all(main).find(n=>n.id==='binding-entity_column');
identityChoice.value='changed_subject';identityChoice.dispatch('change');
const summary=all(main).find(n=>n.attrs.class==='interpretation-wrap');
assert.match(text(summary),/changed_subject/,'Interpretation must follow current edits');
identityChoice.value='';identityChoice.dispatch('change');
await all(main).find(n=>n.tag==='button'&&text(n)==='Check these columns').onclick();
assert.equal(editor.open,true,'Missing selections must open the controls before focusing the error');
assert.equal(all(main).filter(n=>n.tag==='button'&&text(n)==='Confirm binding').length,0);
console.log('Interpretation preserves literal values and exposes incomplete edits without confirming them');

const examples=renderBindingExamples(el,{scope:'Bounded source rows, not a finding',row_numbering:'CSV record numbers',rows:[{side:'train',sample:' a ',entity:'<img src=x>',split_row:2,mapping_row:3},{side:'test',sample:'b',entity:null,split_row:4,mapping_row:null},{side:'test',sample:'c',entity:'',split_row:5,mapping_row:6}]});
assert.match(text(examples),/" a "/);
assert.match(text(examples),/No mapping row/);
assert.match(text(examples),/Split 4 → Mapping missing/);
assert.match(text(examples),/""/);
assert.equal(all(examples).filter(n=>n.tag==='img').length,0);
console.log('Source examples preserve exact values, distinguish missing and blank, and escape markup');
