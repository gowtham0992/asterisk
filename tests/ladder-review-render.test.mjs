import test from 'node:test';
import assert from 'node:assert/strict';
class Node {
 constructor(tag,text=''){this.tag=tag;this.text=text;this.children=[];this.style={};this.attrs={};}
 append(...nodes){this.children.push(...nodes)}
 replaceChildren(...nodes){this.children=nodes}
 setAttribute(k,v){this.attrs[k]=v}
 addEventListener(){}
 get textContent(){return this.text+this.children.map(n=>n.textContent).join(' ')}
}
globalThis.Node=Node;
globalThis.document={querySelector:()=>null,createElement:tag=>new Node(tag),createTextNode:text=>new Node('#text',String(text))};
const {renderReviewContext, renderLadder}=await import('../static/ladder-render.mjs');
const context={population:{train:2,test:2,excluded:6},partitions:[
 {file:'split.csv',column:'split',label:'test',role:'excluded',rows:6},
 {file:'split.csv',column:'split',label:'val',role:'test',rows:2}],
 sources:[{file:'split.csv',sample:'column "image"',deduplicate:false}],
 levels:[{name:'patient',rule:'first 12 characters',overrides:{}}],
 citations:[{file:'README.md',start_line:1,end_line:2,quote:'Subject identifies the person, not the image.'}],
 confirmation:'I confirm the first 12 characters identify a patient and "val" is the evaluation set.'};
test('review exposes swapped labels and excluded counts without interpreting markup',()=>{
 const node=renderReviewContext(context);
 assert.match(node.textContent,/test → excluded 6/);
 assert.match(node.textContent,/val → test 2/);
 assert.match(node.textContent,/6 excluded/);
 assert.match(node.textContent,/first 12 characters/);
 assert.match(node.textContent,/Subject identifies the person, not the image/);
 assert.match(node.textContent,/README.md, lines 1–2/);
});
test('confirmation uses the reviewed derivation and partition, never proposer prose',()=>{
 const panel=new Node('main');
 const result={claim:{text:'Unseen patients',level:'patient'},finding:{level:'patient',status:'held_out_pending_confirmation',confirmable:true,reason:'No overlap'},
  levels:[{name:'patient',kind:'unit',status:'measured',meaning:'INDEPENDENCE ALREADY PROVEN',shared:0,test_units:1,test_rows:2,affected_test_rows:0,unmapped_rows:0,test_units_seen_in_train_percent:0}],
  population:context.population,review_context:context};
 renderLadder(panel,result,()=>{});
 const all=n=>[n,...n.children.flatMap(all)];
 const label=all(panel).find(n=>n.tag==='label');
 assert.match(label.textContent,/"val" is the evaluation set/);
 assert.doesNotMatch(label.textContent,/ALREADY PROVEN/);
 assert.match(panel.textContent,/Proposer’s note \(unverified\)/);
});
test('citation gaps and denial candidates remain explicitly unverified text',async()=>{
 const {renderCitationReview}=await import('../static/ladder-render.mjs');
 const r={scope:'Matching words do not verify meaning.',requirements:[{description:'rotor join',missing_terms:['window_key'],candidates:[{file:'notes.txt',line:2,text:'Do NOT join <script>window_key</script>',truncated:false}]}]};
 const node=renderCitationReview(r);assert.match(node.textContent,/Missing cited field references: window_key/);
 assert.match(node.textContent,/Candidate passages · not verified support/);assert.match(node.textContent,/Do NOT join/);
 const all=n=>[n,...n.children.flatMap(all)];assert.equal(all(node).some(n=>n.tag==='script'),false);
});

test('row-to-unit values sit in assumption review before confirmation and stay literal text',()=>{
 const panel=new Node('main');
 const result={claim:{text:'Unseen groups',level:'patient'},finding:{level:'patient',status:'held_out_pending_confirmation',confirmable:true,reason:'No overlap'},
  levels:[{name:'patient',kind:'unit',status:'measured',shared:0,test_units:1,test_rows:2,affected_test_rows:0,unmapped_rows:0,test_units_seen_in_train_percent:0}],
  population:context.population,review_context:context};
 const preview={available:true,level:'patient',files:[{file:'split.csv',examples:[{raw:'<script>raw</script>',value:'action_g03'}]}]};
 renderLadder(panel,result,()=>{},preview);
 assert.match(panel.textContent,/See the identity this rule produces/);
 assert.match(panel.textContent,/action_g03/);
 assert.ok(panel.textContent.indexOf('action_g03')<panel.textContent.indexOf('I confirm'));
 assert.match(panel.textContent,/not an independence verdict/);
 const all=n=>[n,...n.children.flatMap(all)];assert.equal(all(panel).some(n=>n.tag==='script'),false);
});


test('each correction control has its own precise name, independent of help text',async()=>{
 const {builderField}=await import('../static/ladder-render.mjs');
 const controls=['First field','Last field','First character','Last character','First cited line','Last cited line'];
 for(const name of controls){
  const input=new Node('input');
  const label=builderField(name,input,'Example values are not a confirmation.');
  assert.equal(input.attrs['aria-label'],name);
  assert.equal(label.tag,'label');
  assert.equal(label.children.filter(n=>n.tag==='input').length,1);
  assert.match(label.textContent,/Example values are not a confirmation/);
 }
 const literal=builderField('<script>file.csv</script>',new Node('select'));
 assert.equal(literal.children.some(n=>n.tag==='script'),false);
});

test('review displays late unmapped rows and reasons as literal text rather than hiding them behind good samples',async()=>{
 const {renderBindingSamples}=await import('../static/ladder-render.mjs');
 const p={available:true,level:'subject',files:[{file:'rows.csv',rows:10,unmapped:4,examples:[{raw:'good',value:'s1'}],failures:[{row:7,raw:'<script>late</script>',key:'k7',reason:'Mapping key has conflicting identity values.'}]}]};
 const node=renderBindingSamples(p);
 assert.match(node.textContent,/10 source rows · 4 unmapped/);
 assert.match(node.textContent,/Inspect unmapped rows/);
 assert.match(node.textContent,/4 unmapped across this entire source; first 1 shown/);
 assert.match(node.textContent,/excluding a CSV header/);
 assert.match(node.textContent,/conflicting identity values/);
 const all=n=>[n,...n.children.flatMap(all)];
 assert.equal(all(node).some(n=>n.tag==='script'),false);
 assert.match(node.textContent,/<script>late<\/script>/);
});

test('pending editor controls restore their original disabled states exactly once',async()=>{
 const {lockBuilderControls}=await import('../static/ladder-render.mjs');
 const editable={disabled:false},partitionLocked={disabled:true};
 const restore=lockBuilderControls([editable,partitionLocked]);
 assert.equal(editable.disabled,true);assert.equal(partitionLocked.disabled,true);
 restore();assert.equal(editable.disabled,false);assert.equal(partitionLocked.disabled,true);
 editable.disabled=true;restore();assert.equal(editable.disabled,true);
});

test('review guard suppresses duplicate requests and permits retry after rejection',async()=>{
 const {createBuilderReview}=await import('../static/ladder-render.mjs');
 const guard=createBuilderReview();let reject,calls=0;
 const first=guard.run(()=>{calls++;return new Promise((resolve,fail)=>{reject=fail})});
 assert.equal(guard.pending,true);
 await guard.run(()=>{calls++});assert.equal(calls,1);
 reject(new Error('Rejected by server'));await assert.rejects(first,/Rejected by server/);
 assert.equal(guard.pending,false);
 assert.equal(await guard.run(()=>{calls++;return 'reviewed'}),'reviewed');
 assert.equal(calls,2);assert.equal(guard.pending,false);
});
