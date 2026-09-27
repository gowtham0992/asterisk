import test from 'node:test';
import assert from 'node:assert/strict';
import {createPreparations} from '../static/preparations.js';
class Element {
 constructor(tag,attrs={},...children){this.tag=tag;Object.assign(this,attrs);this.children=children.flat(Infinity).filter(v=>v!=null);this.events={};this.value='';this.isConnected=true;}
 append(...children){this.children.push(...children)}
 replaceChildren(...children){this.children=children.flat(Infinity)}
 addEventListener(name,fn){this.events[name]=fn}
 focus(){this.focused=true}
}
const text=n=>n instanceof Element?[n.textContent||'',...n.children.map(text)].join(' '):String(n);
const all=n=>n instanceof Element?[n,...n.children.flatMap(all)]:[];
const find=(root,predicate)=>all(root).find(predicate);
const button=(root,name)=>find(root,n=>n.tag==='button'&&text(n).trim()===name);
const id='a'.repeat(32),record={draft_hash:'b'.repeat(64),inputs:{'notes.txt':'<script>untrusted</script>'},policies:{}};
const unloadListeners=new Map();
const testWindow={addEventListener:(k,v)=>unloadListeners.set(k,v),removeEventListener:k=>unloadListeners.delete(k)};
let previousMain;
const warns=()=>{let prevented=false;unloadListeners.get('beforeunload')?.({preventDefault(){prevented=true}});return prevented};
function setup(api){
 if(previousMain)for(const node of all(previousMain))node.isConnected=false;
 globalThis.window=testWindow;
 const main=new Element('main');previousMain=main;globalThis.document={querySelector:s=>s.includes('h1')?find(main,n=>n.tag==='h1'):new Element('span')};globalThis.location={hash:''};
 const continued=[];
 const el=(...args)=>new Element(...args),ui=createPreparations({el,btn:(t,fn,cls)=>el('button',{onclick:fn,class:cls},t),api,main,toast:()=>{},onContinue:seed=>continued.push(seed)});
 return {main,ui,continued};
}
const detail=()=>({id,title:'Original',revision:1,review_hash:'c'.repeat(64),population:{train:1,test:1,excluded:0},record,confirmation:null});
test('empty list explains storage consent and preserves the no-result boundary',async()=>{
 const {main,ui}=setup(async()=>({drafts:[]}));await ui.route('#preparations');assert.match(text(main),/No preparations saved/);assert.match(text(main),/complete original source files/);assert.match(text(main),/No files are sent to Nebius/);
});
test('a delayed list cannot replace a newer detail route',async()=>{
 let resolve;const {main,ui}=setup(path=>path.endsWith(id)?Promise.resolve(detail()):new Promise(r=>resolve=r));
 const pending=ui.route('#preparations');await ui.route('#preparation/'+id);resolve({drafts:[]});await pending;
 assert.match(text(main),/Original/);assert.doesNotMatch(text(main),/No preparations saved/);
});
test('leaving the preparation route invalidates pending responses',async()=>{
 let resolve;const {main,ui}=setup(()=>new Promise(r=>resolve=r));const pending=ui.route('#preparations');ui.stop();main.replaceChildren('New receipt view');resolve({drafts:[]});await pending;assert.equal(text(main).trim(),'New receipt view');
});
test('source text is a text child and counts are explicitly not overlap results',async()=>{
 const {main,ui}=setup(async()=>detail());await ui.route('#preparation/'+id);assert.match(text(main),/not an overlap result/);const source=find(main,n=>n.tag==='details'&&n.class==='source-reader');source.open=true;source.events.toggle();assert.equal(find(source,n=>n.tag==='code').children[0],record.inputs['notes.txt']);assert.equal(all(main).filter(n=>n.tag==='script').length,0);
});
test('stale rename preserves the entered name and offers reload',async()=>{
 const {main,ui}=setup(async(path,method)=>{if(method==='PUT')throw Error('This preparation changed. Reopen it before saving again');return detail()});await ui.route('#preparation/'+id);
 const input=find(main,n=>n.id==='saved-preparation-title');input.value='Unsaved name';await find(main,n=>n.tag==='form').events.submit({preventDefault(){}});
 assert.equal(input.value,'Unsaved name');assert.match(text(main),/This preparation changed/);assert.equal(button(main,'Save name').disabled,false);assert.ok(button(main,'Reopen latest version'));
});
test('successful rename uses the new revision for deletion and accepts 204',async()=>{
 const calls=[];const {main,ui}=setup(async(path,method,body)=>{calls.push({method,body});if(method==='PUT')return {title:body.title,revision:2};if(method==='DELETE')return null;return detail()});await ui.route('#preparation/'+id);
 find(main,n=>n.id==='saved-preparation-title').value='Renamed';await find(main,n=>n.tag==='form').events.submit({preventDefault(){}});
 await button(main,'Delete this draft').onclick();assert.equal(calls.at(-1).body.revision,2);assert.equal(location.hash,'preparations');
});
test('stale deletion leaves the draft visible and allows recovery',async()=>{
 const {main,ui}=setup(async(path,method)=>{if(method==='DELETE')throw Error('Changed; reopen first');return detail()});await ui.route('#preparation/'+id);await button(main,'Delete this draft').onclick();assert.match(text(main),/Changed; reopen first/);assert.match(text(main),/Original/);assert.equal(location.hash,'');assert.equal(button(main,'Delete this draft').disabled,false);
});

test('handoff requires explicit review and seeds a manual check with no claim or confirmation',async()=>{
 const calls=[];const {main,ui,continued}=setup(async(path,method,body)=>{calls.push({path,body});if(path.endsWith('/handoff'))return {title:'Prepared',files:[{name:'splits.csv',content:'sample,partition\na,train\n'},{name:'asterisk.json',content:JSON.stringify({schema_version:1,arguments:{split_file:'splits.csv',mapping_file:'entities.csv'}})}]};return detail()});
 await ui.route('#preparation/'+id);const action=button(main,'Continue to split check');
 assert.equal(action.disabled,true);await action.onclick();assert.equal(continued.length,0);
 const consent=find(main,n=>n.type==='checkbox');consent.checked=true;consent.events.change();await action.onclick();
 assert.equal(continued.length,1);assert.equal(continued[0].claim,'');assert.equal(continued[0]._manual,true);assert.equal(continued[0].confirmation,undefined);assert.equal(continued[0].files.length,1);assert.equal(continued[0].saved_binding.split_file,'splits.csv');
 assert.deepEqual(calls.at(-1).body,{revision:1,review_hash:'c'.repeat(64),confirm:true});assert.equal(consent.checked,false);
});
test('stale handoff stays on the draft and clears consent',async()=>{
 const {main,ui,continued}=setup(async(path)=>{if(path.endsWith('/handoff'))throw Error('This preparation changed. Reopen it before continuing');return detail()});await ui.route('#preparation/'+id);
 const consent=find(main,n=>n.type==='checkbox');consent.checked=true;consent.events.change();await button(main,'Continue to split check').onclick();
 assert.equal(continued.length,0);assert.equal(consent.checked,false);assert.match(text(main),/Reopen it before continuing/);
});

test('recorded claim is editable starting text and never transfers confirmation',async()=>{
 const original='Evaluation patients must be absent from training.';
 const data=detail();data.record={...record,model_proposal:{approved_payload:{messages:[{role:'system',content:''},{role:'user',content:JSON.stringify({claim:original})}]}}};
 const {main,ui,continued}=setup(async path=>path.endsWith('/handoff')?{title:'Prepared',files:[]}:data);
 await ui.route('#preparation/'+id);
 const claim=find(main,n=>n.id==='preparation-handoff-claim'),consent=find(main,n=>n.type==='checkbox');
 assert.equal(claim.value,original);
 consent.checked=true;consent.events.change();
 claim.value='Evaluation lesions must be absent from training.';claim.events.input();
 assert.equal(consent.checked,false);assert.equal(button(main,'Continue to split check').disabled,true);
 consent.checked=true;consent.events.change();await button(main,'Continue to split check').onclick();
 assert.equal(continued[0].claim,claim.value);assert.equal(continued[0]._manual,true);assert.equal(continued[0].confirmation,undefined);
});

test('import edits warn before leaving, survive rejection, and clear only after saving',async()=>{
 const {main,ui}=setup(async(path,method)=>method==='POST'?{id}:({drafts:[]}));
 await ui.route('#preparations');
 const form=find(main,n=>n.tag==='form'),title=find(main,n=>n.id==='preparation-title'),file=find(main,n=>n.id==='preparation-file');
 const consent=find(main,n=>n.type==='checkbox');
 title.value='Import in progress';form.events.input({target:title});
 assert.equal(warns(),true);
 file.files=[];
 await form.events.submit({preventDefault(){}});
 assert.equal(title.value,'Import in progress');assert.equal(warns(),true);
 file.files=[{size:2,arrayBuffer:async()=>new TextEncoder().encode('{}').buffer}];consent.checked=true;
 await form.events.submit({preventDefault(){}});
 assert.equal(warns(),false);assert.equal(location.hash,'preparation/'+id);
});

test('unsaved rename warns, blocks stale-name handoff, and edit-back clears only its warning',async()=>{
 const calls=[];const {main,ui,continued}=setup(async(path,method)=>{calls.push({path,method});return detail()});await ui.route('#preparation/'+id);
 const input=find(main,n=>n.id==='saved-preparation-title');input.value='Typed name';input.events.input();assert.equal(warns(),true);
 const consent=find(main,n=>n.type==='checkbox');consent.checked=true;consent.events.change();await button(main,'Continue to split check').onclick();
 assert.equal(continued.length,0);assert.equal(calls.length,1);assert.match(text(main),/Save the preparation name/);assert.equal(input.focused,true);
 input.value='Original';input.events.input();assert.equal(warns(),false);
});

test('pending rename locks its input, retains failure edits and clears warning on success',async()=>{
 let resolve,reject;const {main,ui}=setup(async(path,method,body)=>method==='PUT'?new Promise((a,b)=>{resolve=a;reject=b}):detail());await ui.route('#preparation/'+id);
 const input=find(main,n=>n.id==='saved-preparation-title'),form=find(main,n=>n.tag==='form');input.value='New name';input.events.input();
 const failed=form.events.submit({preventDefault(){}});assert.equal(input.disabled,true);reject(Error('offline'));await failed;assert.equal(input.disabled,false);assert.equal(input.value,'New name');assert.equal(warns(),true);
 const saved=form.events.submit({preventDefault(){}});resolve({title:'New name',revision:2});await saved;assert.equal(warns(),false);assert.equal(input.disabled,false);
});

test('a delayed capability check cannot reopen intake after navigation',async()=>{
 let resolve;const {main,ui}=setup(()=>new Promise(r=>resolve=r));
 const pending=ui.route('#prepare');assert.match(text(main),/Checking preparation availability/);
 ui.stop();main.replaceChildren('Another page');resolve({proposal_configured:false});await pending;
 assert.equal(text(main).trim(),'Another page');
});

test('saved purpose is visible and carried into the new check without confirmation',async()=>{
 const data=detail();data.record={...record,model_proposal:{approved_payload:{evaluation_intent:{target:'unseen_entities',unit:'frogs'}}}};
 const {main,ui,continued}=setup(async path=>path.endsWith('/handoff')?{title:'Prepared',files:[]}:data);
 await ui.route('#preparation/'+id);
 assert.match(text(main),/Intended unseen unit: frogs/);
 const consent=find(main,n=>n.type==='checkbox');consent.checked=true;consent.events.change();
 await button(main,'Continue to split check').onclick();
 assert.deepEqual(continued[0].evaluation_intent,{target:'unseen_entities',unit:'frogs'});
 assert.equal(continued[0].confirmation,undefined);
});
