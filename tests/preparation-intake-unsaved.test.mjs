import test from 'node:test';
import assert from 'node:assert/strict';
import {nativePreparation} from '../static/preparation-intake.js';
class Element {
 constructor(tag,attrs={},...children){this.tag=tag;Object.assign(this,attrs);this.children=children.flat();this.events={};this.dataset={};this.value='';this.files=[];this.isConnected=true;}
 append(...nodes){this.children.push(...nodes)}
 replaceChildren(...nodes){this.children=nodes}
 setAttribute(k,v){this[k]=v}removeAttribute(k){delete this[k]}
 addEventListener(k,fn){this.events[k]=fn}focus(){this.focused=true}
 querySelectorAll(){return []}
}
const all=n=>n instanceof Element?[n,...n.children.flatMap(all)]:[];
const listeners=new Map();
globalThis.window={addEventListener:(k,v)=>listeners.set(k,v),removeEventListener:k=>listeners.delete(k)};
globalThis.sessionStorage={getItem:()=>null};
const warns=()=>{let prevented=false;listeners.get('beforeunload')?.({preventDefault(){prevented=true}});return prevented};
test('intake edits remain protected after a failed preview, until the page is detached',async()=>{
 const el=(...args)=>new Element(...args);
 const root=nativePreparation({el,btn:(text,onclick)=>el('button',{onclick},text),api:async()=>{throw Error('offline')},onSaved(){},isCurrent:()=>true});
 assert.equal(root.children.includes(null),false,'native append would render null as visible text');
 assert.equal(warns(),false);
 const nodes=all(root),form=nodes.find(n=>n.tag==='form'),title=nodes.find(n=>n.id==='native-title');
 title.value='Important unsaved preparation';form.events.input({target:title});
 assert.equal(warns(),true,'typing an unsaved claim/name must warn before navigation');
 // The storage validation failure must leave the current form protected.
 await form.events.submit({preventDefault(){}});
 assert.equal(title.value,'Important unsaved preparation');assert.equal(warns(),true);
 assert.equal(nodes.find(n=>n.role==='status').focused,true,'errors receive keyboard focus without clearing inputs');
 root.isConnected=false;assert.equal(warns(),false);
});
test('copied setup text starts unconfirmed, without file selection or storage consent',async()=>{
 const el=(...args)=>new Element(...args);
 const root=nativePreparation({el,btn:(text,onclick)=>el('button',{onclick},text),api:async()=>{throw Error('must not call')},onSaved(){},isCurrent:()=>true,initial:{title:'Imported name',claim:'Evaluation people must be absent from training.'}});
 const nodes=all(root);
 assert.equal(nodes.find(n=>n.id==='native-title').value,'Imported name');
 assert.equal(nodes.find(n=>n.id==='native-claim').value,'Evaluation people must be absent from training.');
 assert.deepEqual(nodes.find(n=>n.id==='native-files').files,[]);
 assert.ok(nodes.filter(n=>n.type==='checkbox').every(n=>!n.checked));
 await Promise.resolve();assert.equal(warns(),true);root.isConnected=false;assert.equal(warns(),false);
});

async function previewReviewed(form,root){
 await form.events.submit({preventDefault(){}});
 const panel=all(root).find(n=>n.tag==='section'&&n.class==='preparation-file-roles');
 for(const box of all(panel).filter(n=>n.type==='checkbox')){box.checked=true;box.events.change()}
 all(form).find(n=>n.id==='native-storage').checked=true;
 await form.events.submit({preventDefault(){}});
}

test('capacity rejection allows an explicit reauthorized attempt, never an automatic retry',async()=>{
 const el=(...args)=>new Element(...args);let calls=0;
 const api=async path=>{
  if(path==='/preparations/proposal-preview')return {ticket_id:'ticket',payload_hash:'hash',provider_available:true,model:'test',estimated_reservation_usd:0.01,messages:[]};
  calls++;const error=Error(calls===1?'Busy; request not started':'Ambiguous connection error');
  if(calls===1)error.preparationNotStarted=true;
  throw error;
 };
 const root=nativePreparation({el,btn:(text,onclick)=>el('button',{onclick},text),api,onSaved(){},isCurrent:()=>true});
 let nodes=all(root);const form=nodes.find(n=>n.tag==='form');
 nodes.find(n=>n.id==='native-files').files=[{name:'data.csv',size:4,arrayBuffer:async()=>new TextEncoder().encode('a\nb\n').buffer}];
 nodes.find(n=>n.id==='native-storage').checked=true;
 await previewReviewed(form,root);
 nodes=all(root);const request=nodes.find(n=>n.tag==='button'&&n.children.includes('Request extraction proposal'));
 const upload=nodes.find(n=>n.type==='checkbox'&&!all(form).includes(n));
 upload.checked=true;await request.onclick();assert.equal(calls,1);assert.equal(upload.checked,false);
 await request.onclick();assert.equal(calls,1,'fresh consent is required');
 upload.checked=true;await request.onclick();assert.equal(calls,2,'same ticket may be explicitly retried only after a known pre-dispatch rejection');
 upload.checked=true;await request.onclick();assert.equal(calls,2,'ambiguous failures must remain consumed');
 root.isConnected=false;
});

test('a refused proposal can hand original CSV inputs to manual setup without another request',async()=>{
 const el=(...args)=>new Element(...args),calls=[],seeds=[];
 const source='sample,subject,split\na,p1,train\nb,p2,test\n';
 const api=async path=>{calls.push(path);return path.endsWith('proposal-preview')?{ticket_id:'ticket',provider_available:true,estimated_reservation_usd:0.01,messages:[]}:{status:'insufficient',missing:['No supported interpretation proposed']}};
 const root=nativePreparation({el,btn:(text,onclick)=>el('button',{onclick},text),api,onSaved(){},onManual:seed=>seeds.push(seed),isCurrent:()=>true});
 const form=all(root).find(n=>n.tag==='form');
 all(root).find(n=>n.id==='native-title').value='Retained title';all(root).find(n=>n.id==='native-claim').value='Evaluation subjects must be new.';
 all(root).find(n=>n.id==='native-files').files=[{name:'data.csv',size:source.length,arrayBuffer:async()=>new TextEncoder().encode(source).buffer}];all(form).find(n=>n.id==='native-storage').checked=true;
 await previewReviewed(form,root);
 const upload=all(root).find(n=>n.type==='checkbox'&&!all(form).includes(n));upload.checked=true;
 await all(root).find(n=>n.children.includes('Request extraction proposal')).onclick();
 const manual=all(root).find(n=>n.children.includes('Use these CSV files in manual split setup'));
 assert.equal(manual.hidden,false);manual.onclick();
 assert.equal(calls.length,2);assert.equal(seeds.length,1);assert.deepEqual(seeds[0].files[0],{name:'data.csv',content:source});assert.equal(seeds[0].title,'Retained title');assert.equal(seeds[0]._manual,true);
 const projection=JSON.parse(seeds[0].files[1].content);assert.equal(projection.format,'asterisk-client-projection');assert.deepEqual(projection.files[0].included,['sample','subject','split']);
 assert.equal(seeds[0].saved_binding,undefined);assert.equal(seeds[0].confirmation,undefined);root.isConnected=false;
});

test('manual handoff is hidden for JSON-only inputs and invalidated when files are edited',async()=>{
 const el=(...args)=>new Element(...args),seeds=[];
 for(const name of ['data.json','data.csv']){
  const root=nativePreparation({el,btn:(text,onclick)=>el('button',{onclick},text),api:async()=>({ticket_id:'ticket',provider_available:false,messages:[]}),onSaved(){},onManual:seed=>seeds.push(seed),isCurrent:()=>true});
  const form=all(root).find(n=>n.tag==='form');all(root).find(n=>n.id==='native-files').files=[{name,size:2,arrayBuffer:async()=>new TextEncoder().encode(name.endsWith('.csv')?'id\na\n':'[{"id":"a"}]').buffer}];all(form).find(n=>n.id==='native-storage').checked=true;
  await previewReviewed(form,root);
  const manual=all(root).find(n=>n.children.includes('Use these CSV files in manual split setup'));
  assert.equal(manual.hidden,name.endsWith('.json'));
  all(root).find(n=>n.children.includes('Edit files or claim')).onclick();manual.onclick();assert.equal(seeds.length,0);root.isConnected=false;
 }
});

test('local review sends nothing until explicit column selection; withheld values never reach API',async()=>{
 const el=(...args)=>new Element(...args),calls=[];
 const root=nativePreparation({el,btn:(text,onclick)=>el('button',{onclick},text),api:async(path,method,body)=>{calls.push({path,body});return {ticket_id:'safe',provider_available:false,messages:[]}},onSaved(){},isCurrent:()=>true});
 const form=all(root).find(n=>n.tag==='form');
 const source='sample,age,subject,split\n001,PRIVATE_AGE,p1,train\n002,PRIVATE_AGE,p1,test\n';
 all(root).find(n=>n.id==='native-files').files=[{name:'data.csv',size:source.length,arrayBuffer:async()=>new TextEncoder().encode(source).buffer}];
 await form.events.submit({preventDefault(){}});assert.equal(calls.length,0);
 const panel=all(root).find(n=>n.tag==='section'&&n.class==='preparation-file-roles');
 const boxes=all(panel).filter(n=>n.type==='checkbox');assert.ok(boxes.every(b=>!b.checked));
 for(const i of [0,2,3]){boxes[i].checked=true;boxes[i].events.change()}
 all(form).find(n=>n.id==='native-storage').checked=true;
 await form.events.submit({preventDefault(){}});
 assert.equal(calls.length,1);assert.equal(calls[0].body.files['data.csv'],'sample,subject,split\n001,p1,train\n002,p1,test\n');
 assert.ok(!JSON.stringify(calls).includes('PRIVATE_AGE'));
 root.isConnected=false;
});

test('oversized native source is rejected before reading or uploading',async()=>{
 const el=(...args)=>new Element(...args);let reads=0,calls=0;
 const root=nativePreparation({el,btn:(text,onclick)=>el('button',{onclick},text),api:async()=>{calls++;throw Error('must not upload')},onSaved(){},isCurrent:()=>true});
 all(root).find(n=>n.id==='native-files').files=[{name:'benchmark.json',size:32000001,arrayBuffer:async()=>{reads++;throw Error('must not read')}}];
 await all(root).find(n=>n.tag==='form').events.submit({preventDefault(){}});
 assert.equal(reads,0);assert.equal(calls,0);assert.match(all(root).find(n=>n.role==='status').textContent,/32 MB/);root.isConnected=false;
});

test('large local JSON yields only explicitly selected scalar fields in the API payload',async()=>{
 const el=(...args)=>new Element(...args),calls=[];
 const root=nativePreparation({el,btn:(text,onclick)=>el('button',{onclick},text),api:async(path,method,body)=>{calls.push(body);return {ticket_id:'json',provider_available:false,messages:[]}},onSaved(){},isCurrent:()=>true});
 const source='[{"image":"slideA","conversations":[{"text":"PRIVATE_NARRATIVE"}]}]';
 all(root).find(n=>n.id==='native-files').files=[{name:'data.json',size:11860158,arrayBuffer:async()=>new TextEncoder().encode(source).buffer}];
 const form=all(root).find(n=>n.tag==='form');await form.events.submit({preventDefault(){}});assert.equal(calls.length,0);
 const panel=all(root).find(n=>n.tag==='section'&&n.class==='preparation-file-roles'),boxes=all(panel).filter(n=>n.type==='checkbox');
 assert.equal(boxes[1].disabled,true);boxes[0].checked=true;boxes[0].events.change();all(form).find(n=>n.id==='native-storage').checked=true;
 await form.events.submit({preventDefault(){}});assert.equal(calls.length,1);assert.ok(!JSON.stringify(calls).includes('PRIVATE_NARRATIVE'));
 assert.deepEqual(JSON.parse(calls[0].files['data.json']),[{image:'slideA'}]);assert.deepEqual(calls[0].projection[0].withheld,['conversations']);root.isConnected=false;
});

test('recovered rejected proposal explains local refusal without reflecting model content or retrying',async()=>{
 const el=(...args)=>new Element(...args),calls=[];
 const root=nativePreparation({el,btn:(text,onclick)=>el('button',{onclick},text),
  api:async path=>{calls.push(path);return {state:'completed',result:{status:'rejected',message:'UNTRUSTED MODEL CONTENT'}}},
  onSaved(){},isCurrent:()=>true});
 const previous=globalThis.sessionStorage;
 globalThis.sessionStorage={getItem:()=> 'saved-ticket'};
 try{
  await all(root).find(n=>n.children.includes('Recover previous response')).onclick();
  const status=all(root).find(n=>n.role==='status');
  assert.match(status.textContent,/local checker could not execute/);
  assert.doesNotMatch(status.textContent,/UNTRUSTED/);
  assert.equal(calls.length,1);
  assert.equal(calls[0],'/preparations/proposals/saved-ticket');
 }finally{globalThis.sessionStorage=previous;root.isConnected=false}
});

test('recovered rejection restores projected CSVs and original claim without a model retry',async()=>{
 const previous=globalThis.sessionStorage;globalThis.sessionStorage={getItem:()=> 'saved-ticket'};
 const el=(...args)=>new Element(...args),calls=[],seeds=[];
 const source='sample,subject,split\na,p1,train\nb,p1,test\n';
 const root=nativePreparation({el,btn:(text,onclick)=>el('button',{onclick},text),api:async path=>{
  calls.push(path);return {state:'completed',result:{status:'rejected'},manual_inputs:{files:{'data.csv':source},claim:'Evaluation subjects must be new.',projection:[]}};
 },onSaved(){},onManual:seed=>seeds.push(seed),isCurrent:()=>true});
 try{
  await all(root).find(n=>n.children.includes('Recover previous response')).onclick();
  const manual=all(root).find(n=>n.children.includes('Use these CSV files in manual split setup'));
  assert.equal(manual.hidden,false);manual.onclick();
  assert.equal(seeds.length,1);assert.deepEqual(seeds[0].files,[{name:'data.csv',content:source}]);
  assert.equal(seeds[0].claim,'Evaluation subjects must be new.');assert.equal(seeds[0].confirmation,undefined);
  assert.deepEqual(calls,['/preparations/proposals/saved-ticket']);
 }finally{globalThis.sessionStorage=previous;root.isConnected=false}
});

test('local inspection permits empty research details and restores form validation before upload',async()=>{
 const el=(...args)=>new Element(...args);let calls=0;
 const root=nativePreparation({el,btn:(text,onclick)=>el('button',{onclick},text),api:async()=>{calls++;throw Error('No request expected')},onSaved(){},isCurrent:()=>true});
 const form=all(root).find(n=>n.tag==='form');
 assert.equal(form.novalidate,true);
 const files=all(root).find(n=>n.id==='native-files');
 files.files=[{name:'data.csv',size:5,arrayBuffer:async()=>new TextEncoder().encode('id\na\n').buffer}];
 await form.events.submit({preventDefault(){}});
 assert.equal(calls,0);assert.equal(form.noValidate,false);
 assert.equal(all(root).find(n=>n.id==='native-title').required,'true');
 assert.equal(all(root).find(n=>n.id==='native-claim').required,'true');
 files.events.change();assert.equal(form.noValidate,true);root.isConnected=false;
});

test('unsupported source names stop the whole batch locally before reading any file',async()=>{
 for(const name of ['vowel-context.data','ae.train','.env','folder/data.csv','data(1).csv']){
  let reads=0,calls=0;const el=(...args)=>new Element(...args);
  const root=nativePreparation({el,btn:(text,onclick)=>el('button',{onclick},text),api:async()=>{calls++;throw Error('must not upload')},onSaved(){},isCurrent:()=>true});
  const nodes=all(root);nodes.find(n=>n.id==='native-title').value='Keep my work';
  nodes.find(n=>n.id==='native-files').files=['valid.csv',name].map(name=>({name,size:4,arrayBuffer:async()=>{reads++;return new TextEncoder().encode('a\nb\n').buffer}}));
  await nodes.find(n=>n.tag==='form').events.submit({preventDefault(){}});
  assert.equal(reads,0,name);assert.equal(calls,0,name);
  assert.match(nodes.find(n=>n.role==='status').textContent,/before.*upload|not.*uploaded/i);
  assert.equal(nodes.find(n=>n.id==='native-title').value,'Keep my work');
  root.isConnected=false;
 }
});

test('availability is visible before file selection and makes no provider request',()=>{
 for(const [configured,expected] of [[false,/unavailable on this server/],[true,/budget and provider availability are checked/],[null,/could not be checked/]]){
  const el=(...args)=>new Element(...args);let calls=0;
  const root=nativePreparation({el,btn:(text,onclick)=>el('button',{onclick},text),api:async()=>{calls++},onSaved(){},isCurrent:()=>true,proposalConfigured:configured});
  const note=all(root).find(n=>n.role==='note');assert.match(note.children.join(' '),expected);assert.equal(calls,0);
  assert.deepEqual(all(root).find(n=>n.id==='native-files').files,[]);root.isConnected=false;
 }
});

test('real benchmark loading stays local, preserves typed details and requires field consent',async()=>{
 const el=(...args)=>new Element(...args);let apiCalls=0,loads=0;
 const root=nativePreparation({el,btn:(text,onclick)=>el('button',{onclick},text),api:async()=>{apiCalls++;throw Error('Unexpected upload')},onSaved(){},isCurrent:()=>true,loadBenchmark:async()=>{loads++;return [new File(['sample,subject,age,split\na,p,42,train\n'],'metadata.csv')];}});
 let nodes=all(root);const title=nodes.find(n=>n.id==='native-title');title.value='My claim context';
 await nodes.find(n=>n.tag==='button'&&n.children.includes('Load real benchmark files')).onclick();
 assert.equal(title.value,'My claim context');assert.equal(loads,1);assert.equal(apiCalls,0);
 const form=nodes.find(n=>n.tag==='form');await form.events.submit({preventDefault(){}});
 nodes=all(root);assert.ok(nodes.some(n=>n['aria-label']==='Include age from metadata.csv'));
 assert.ok(nodes.filter(n=>n.type==='checkbox').every(n=>!n.checked));assert.equal(apiCalls,0);
 // Choosing local files replaces, rather than silently combining with, the example.
 const file=nodes.find(n=>n.id==='native-files');file.files=[new File(['id,split\nz,test\n'],'own.csv')];file.events.change();
 await form.events.submit({preventDefault(){}});
 assert.ok(all(root).some(n=>n['aria-label']==='Include id from own.csv'));
 assert.ok(!all(root).some(n=>n['aria-label']==='Include age from metadata.csv'));
});

test('failed benchmark load preserves user text and offers retry without upload',async()=>{
 const el=(...args)=>new Element(...args);let loads=0;
 const root=nativePreparation({el,btn:(text,onclick)=>el('button',{onclick},text),api:async()=>{throw Error('Unexpected upload')},onSaved(){},isCurrent:()=>true,loadBenchmark:async()=>{loads++;throw Error('Source changed')}});
 const nodes=all(root),title=nodes.find(n=>n.id==='native-title'),button=nodes.find(n=>n.children.includes('Load real benchmark files'));title.value='Keep this';
 await button.onclick();assert.equal(title.value,'Keep this');assert.equal(nodes.find(n=>n.role==='status').textContent,'Source changed');
 await button.onclick();assert.equal(loads,2);
});

test('fresh upload preview replaces stale startup availability',async()=>{
 const el=(...args)=>new Element(...args);
 const root=nativePreparation({el,btn:(text,onclick)=>el('button',{onclick},text),api:async()=>({ticket_id:'ticket',provider_available:true,model:'test',estimated_reservation_usd:0.01,messages:[]}),onSaved(){},isCurrent:()=>true,proposalConfigured:false});
 const nodes=all(root),file=nodes.find(n=>n.id==='native-files');file.files=[new File(['id,split\na,train\n'],'data.csv')];file.events.change();
 await previewReviewed(nodes.find(n=>n.tag==='form'),root);
 assert.match(nodes.find(n=>n.role==='note').textContent,/available for this reviewed payload/);
});
