import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {ladderView,levelRow,referencedFiles,matchFiles} from '../static/ladder-view.mjs';
const load=name=>JSON.parse(readFileSync(new URL(`../static/ladders/${name}.json`,import.meta.url)));
test('a slide-disjoint benchmark reads as shared at the claimed patient level',()=>{
 const view=ladderView(load('wsibench-report'));
 assert.equal(view.claimLevel,'patient');assert.equal(view.finding.tone,'shared');assert.equal(view.finding.title,'Not held out');
 const rows=Object.fromEntries(view.rows.map(r=>[r.name,r]));
 assert.equal(rows.slide.tone,'held');assert.equal(rows.slide.isClaim,false);
 assert.equal(rows.patient.tone,'shared');assert.equal(rows.patient.isClaim,true);assert.ok(rows.patient.witnesses.length>0);
 assert.match(rows.patient.detail,/^42 evaluation patients of 207 also in training · 43 of 208 evaluation rows affected$/);
});
test('held out stays pending, unmapped rows are unknown, attributes are never leaks, and nesting breaks are shown',()=>{
 const view=ladderView(load('ptbxl'));
 assert.equal(view.finding.tone,'held');assert.match(view.finding.title,/pending your confirmation/);
 const rows=Object.fromEntries(view.rows.map(r=>[r.name,r]));
 assert.equal(rows.patient.state,'Held out');
 assert.equal(rows.site.tone,'shared');assert.ok(rows.site.notes.some(n=>/16 selected rows had no site value/.test(n)));assert.ok(rows.site.notes.some(n=>/do not nest/.test(n)));
 assert.equal(rows.device.tone,'attribute');assert.ok(rows.device.notes.some(n=>/not a leak/.test(n)));
 assert.equal(view.population,'17,418 training · 2,198 evaluation · 2,183 excluded rows');
});
test('zero overlap is not called held out when it cannot be established',()=>{
 const base={name:'lesion',kind:'unit',status:'measured',shared:0,test_units:3,affected_test_rows:0,test_rows:3,unmapped_rows:0,test_units_seen_in_train_percent:0,one_unit_per_sample:false,disjoint_namespaces:null};
 assert.equal(levelRow(base,'lesion').state,'Held out');
 assert.equal(levelRow({...base,unmapped_rows:2},'lesion').tone,'unknown');
 const families=levelRow({...base,disjoint_namespaces:{train_tokens:['HAM_'],test_tokens:['HAMTEST_']}},'lesion');
 assert.equal(families.state,'Not comparable');assert.match(families.notes.at(-1),/HAM_ vs HAMTEST_/);
 assert.ok(levelRow({...base,one_unit_per_sample:true},'lesion').notes.some(n=>/Confirm this column really names a lesion/.test(n)));
 const missing=levelRow({name:'site',kind:'unit',status:'unavailable',reason:'Blank site'},'site');
 assert.equal(missing.state,'Unavailable');assert.equal(missing.percent,null);assert.equal(missing.detail,'Blank site');
});
test('the files a spec reads include lookup tables and citations, matched by exact name or basename',()=>{
 const spec=JSON.parse(readFileSync(new URL('../static/ladder-example/spec.json',import.meta.url)));
 assert.deepEqual(referencedFiles(spec),['split.csv','subjects.csv','README.md']);
 const pick=names=>names.map(name=>({name}));
 assert.deepEqual(matchFiles(spec,pick(['split.csv','README.md'])).missing,['subjects.csv']);
 const nested={sources:[{file:'a/train.json'},{file:'b/train.json'}],levels:[],citations:[]};
 assert.deepEqual(matchFiles(nested,pick(['train.json'])).ambiguous,['b/train.json']);
 assert.deepEqual(matchFiles(nested,pick(['a/train.json','b/train.json'])).ambiguous,[]);
});
test('confirmation is offered only when the meaning of the claim level is the one open question',async()=>{
 const {confirmable,ladderView}=await import('../static/ladder-view.mjs');
 const row={name:'patient',kind:'unit',meaning:'GDC participant barcode',one_unit_per_sample:false};
 const base={levels:[row],confirmed_levels:[],finding:{status:'held_out_pending_confirmation',level:'patient',reason:'',confirmable:true}};
 assert.deepEqual(confirmable(base),{level:'patient',meaning:'GDC participant barcode',perSample:false});
 assert.equal(confirmable({...base,confirmed_levels:['patient']}),null);
 assert.equal(confirmable({...base,finding:{status:'violation',level:'patient'}}),null);
 const perSample={...base,levels:[{...row,one_unit_per_sample:true}],finding:{status:'not_established',level:'patient',confirmable:true,reason:'Every selected sample has its own patient value.'}};
 assert.equal(confirmable(perSample).perSample,true);
 const tautology={...base,finding:{status:'not_established',level:'patient',reason:'In split.csv the partition is read from the column that defines patient'}};
 assert.equal(confirmable(tautology),null);
 assert.equal(confirmable({...base,levels:[{...row,kind:'observation'}]}),null);
 assert.equal(ladderView({...load('ptbxl'),finding:{...load('ptbxl').finding,status:'held_out'}}).finding.title,'Held out');
});
test('proposal helpers read columns locally, describe expressions and quote cited lines',async()=>{
 const v=await import('../static/ladder-view.mjs');
 assert.deepEqual(v.tableColumns('split.csv','record,split\nI01,train\n'),['record','split']);
 assert.deepEqual(v.tableColumns('t.json','[{"image":"a","age":"61"}]'),['image','age']);
 assert.deepEqual(v.tableColumns('test_list.txt','x.png\n'),['value']);
 assert.equal(v.isDocumentation('README.md'),true);assert.equal(v.isDocumentation('split.csv'),false);
 assert.equal(v.describeExpression({column:'image',basename:true,prefix:12}),'column "image", file name after the last /, first 12 characters');
 assert.equal(v.describeExpression({lookup:{file:'mapping.csv',key_column:'record',value_column:'patient',on:{column:'record'}}}),'"patient" from mapping.csv, matched on "record" = column "record"');
 assert.deepEqual(v.citedLines([{file:'README.md',start_line:2,end_line:3}],{'README.md':'a\nb\nc\nd'}),[{file:'README.md',start:2,end:3,text:'b\nc'}]);
 const r=v.receipt({claim:'c',proposal:{provider:'Nebius Token Factory',model:'m',payload_sha256:'h',attempts:[{error:'x'},{error:null}],total_tokens:5},spec:{},result:{...load('ptbxl'),confirmed_levels:['patient']},replay:{provenance:{runtime:'nebius-sandbox',matches_local:true}},createdAt:'t'});
 assert.equal(r.proposal.repaired,true);assert.equal(r.replay.matches_local,true);assert.deepEqual(r.confirmed_levels,['patient']);
 assert.equal(JSON.stringify(r).includes('patient_id,'),false);
});
test('the guided builder derives units exactly like the engine and emits a valid-shaped spec',async()=>{
 const v=await import('../static/ladder-view.mjs');
 assert.equal(v.deriveValue('PN00/PN00-1.edf',{basename:true,prefix:4}),'PN00');
 assert.equal(v.deriveValue('s20011',{prefix:5}),'s2001');
 assert.equal(v.deriveValue('ab',{prefix:5}),null);assert.equal(v.deriveValue('',{}),null);
 assert.equal(v.guessPartition(' Train '),'train');assert.equal(v.guessPartition('x'),'excluded');assert.equal(v.guessPartition('Test'),'test');
 assert.equal(v.splitColumn(['record','split']),'split');assert.equal(v.splitColumn(['record','subject']),null);
 assert.deepEqual(v.tableRows('s.csv','record,split\ns20011,train\n'),[{record:'s20011',split:'train'}]);
 const spec=v.buildSpec({claim:'No test subject appears in training.',unitName:'Subject',
  sources:[{file:'split.csv',sample:{column:'record'},partition:{column:'split',map:{train:'train',test:'test'}}}],
  unit:{column:'record',prefix:5,meaning:'Records from one subject differ in the last digit only.'},citation:{file:'ltst.md',start:2,end:3}});
 assert.equal(spec.claim.level,'subject');assert.equal(spec.levels.length,2);
 assert.deepEqual(spec.levels[1].expression,{column:'record',prefix:5});assert.equal(spec.sources[0].format,'csv');
 const look=v.buildSpec({claim:'c c c',unitName:'patient',sources:[{file:'a.csv',sample:{column:'record'},partition:{value:'train'}}],
  unit:{column:'record',lookup:{file:'mapping.csv',key:'record',value:'patient'}},citation:{file:'r.md',start:1,end:1}});
 assert.deepEqual(look.levels[1].expression,{lookup:{file:'mapping.csv',format:'csv',key_column:'record',value_column:'patient',on:{column:'record'}}});
});
test('a final newline does not count as a citable line',async()=>{
 const {lineCount}=await import('../static/ladder-view.mjs');
 assert.equal(lineCount('a\nb\n'),2);assert.equal(lineCount('a\nb'),2);assert.equal(lineCount(''),0);
});
test('field and characters derive and describe exactly like the engine',async()=>{
 const v=await import('../static/ladder-view.mjs');
 assert.equal(v.deriveValue('1034-121119-0003',{field:{separator:'-',from:1}}),'1034');
 assert.equal(v.deriveValue('x/airport-barcelona-0-0-a.wav',{basename:true,field:{separator:'-',from:2,to:3}}),'barcelona-0');
 assert.equal(v.deriveValue('SC4011E0',{characters:{from:4,to:5}}),'01');
 assert.equal(v.deriveValue('a-b',{field:{separator:'-',from:3}}),null);assert.equal(v.deriveValue('abc',{characters:{from:2,to:9}}),null);
 assert.equal(v.describeExpression({column:'f',basename:true,field:{separator:'-',from:2,to:3}}),'column "f", file name after the last /, fields 2–3 split on "-"');
 assert.equal(v.describeExpression({column:'c',characters:{from:4,to:5}}),'column "c", characters 4–5');
 const spec=v.buildSpec({claim:'c c c',unitName:'location',sources:[{file:'a.csv',sample:{column:'f'},partition:{value:'train'}}],
  unit:{column:'f',basename:true,field:{separator:'-',from:2,to:3},characters:{from:0}},citation:{file:'r.md',start:1,end:1}});
 assert.deepEqual(spec.levels.at(-1).expression,{column:'f',basename:true,field:{separator:'-',from:2,to:3}});
 const chars=v.buildSpec({claim:'c c c',unitName:'subject',sources:[{file:'a.csv',sample:{column:'f'},partition:{value:'train'}}],
  unit:{column:'f',characters:{from:4,to:5},prefix:5},citation:{file:'r.md',start:1,end:1}});
 assert.deepEqual(chars.levels.at(-1).expression,{column:'f',characters:{from:4,to:5}});
});
