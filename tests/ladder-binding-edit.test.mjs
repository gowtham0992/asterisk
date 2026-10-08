import test from 'node:test';
import assert from 'node:assert/strict';
import {bindingSeed,buildSpec,preserveBinding,bindingQuestions} from '../static/ladder-view.mjs';
const spec={schema:'asterisk-ladder/1',claim:{text:'Unseen rotors',level:'rotor'},sources:[{file:'windows.csv',format:'csv',sample:{column:'window'},partition:{column:'split',map:{fit:'train',hold:'test',reserve:'excluded'}}}],levels:[{name:'window',kind:'observation',expression:{column:'window'}},{name:'rotor',kind:'unit',meaning:'Physical rotor',expression:{lookup:{file:'keys.csv',format:'csv',key_column:'window',value_column:'asset',on:{column:'window',prefix:4}}}}],citations:[{file:'notes.txt',start_line:2,end_line:3},{file:'notes.txt',start_line:7,end_line:8}]};
test('correction opens existing lookup, labels, transforms and evidence rather than guesses',()=>{
 const seed=bindingSeed(spec);assert.equal(seed.unit.lookup.value,'asset');assert.equal(seed.unit.prefix,4);assert.equal(seed.sources[0].partition.map.reserve,'excluded');
 const next=buildSpec({claim:spec.claim.text,unitName:seed.name,sources:seed.sources,unit:{...seed.unit,lookup:{...seed.unit.lookup,value:'rotor'}},citation:{file:'notes.txt',start:2,end:3}});
 const edited=preserveBinding(spec,next);assert.equal(edited.levels[0].name,'window');assert.equal(edited.levels[1].expression.lookup.value_column,'rotor');assert.equal(edited.citations.length,2);assert.equal(spec.levels[1].expression.lookup.value_column,'asset');
});
test('complex definitions never silently flatten into guided grammar',()=>{
 for(const change of [s=>s.levels.push({name:'site',kind:'unit',expression:{column:'site'}}),s=>s.levels[1].by_source={'windows.csv':{column:'other'}},s=>s.sources[0].sample={row:true},s=>s.sources[0].deduplicate=true,s=>s.levels[1].expression.lookup.on={lookup:{}}]){
  const complex=structuredClone(spec);change(complex);assert.equal(bindingSeed(complex),null);assert.throws(()=>preserveBinding(complex,spec),/complete definition/);
 }
});
test('three questions show actual source identity and join without certifying semantics',()=>{
 const q=bindingQuestions(spec);assert.equal(q.length,3);assert.match(q[0].answers[0],/windows.csv.*window/);assert.match(q[1].answers[0],/rotor.*asset.*keys.csv/);assert.match(q[2].answers[0],/window.*first 4 characters/);
});
test('preview covers every observation file and refuses conflicting/missing lookup mappings',async()=>{
 const {bindingPreview}=await import('../static/ladder-view.mjs');
 const p=bindingPreview(['a.csv','b.csv'],{column:'id',lookup:{file:'map.csv',key:'key',value:'subject'}},{'a.csv':[{id:'a'},{id:'b'}],'b.csv':[{id:'c'}],'map.csv':[{key:'a',subject:'s1'},{key:'a',subject:'s2'},{key:'b',subject:'s3'}]});
 assert.equal(p.length,2);assert.equal(p[0].unmapped,1);assert.equal(p[0].examples[0].value,null);assert.equal(p[0].examples[1].value,'s3');assert.equal(p[1].unmapped,1);
});

test('pre-measurement review shows namespace-preserving values from every source',async()=>{
 const {reviewBindingPreview}=await import('../static/ladder-view.mjs');
 const s={schema:'asterisk-ladder/1',claim:{text:'Unseen action-qualified groups',level:'group'},sources:[{file:'fit.txt',format:'lines',sample:{column:'value'},partition:{value:'train'}},{file:'check.txt',format:'lines',sample:{column:'value'},partition:{value:'test'}}],levels:[{name:'clip',kind:'observation',expression:{column:'value'}},{name:'group',kind:'unit',expression:{column:'value',basename:true,field:{separator:'_',from:2,to:3}}}],citations:[]};
 const files={'fit.txt':'Drill/v_Drill_g03_c01.avi 1\r\nSpin/v_Spin_g03_c01.avi 2\r\n','check.txt':'Drill/v_Drill_g03_c02.avi\r\n'};
 const before=JSON.stringify(s),good=reviewBindingPreview(s,files);
 assert.equal(good.available,true);assert.equal(good.files.length,2);assert.equal(good.files[0].examples[0].raw,'Drill/v_Drill_g03_c01.avi 1');
 assert.equal(good.files[0].examples[0].value,'Drill_g03');assert.equal(good.files[0].examples[1].value,'Spin_g03');
 s.levels[1].expression.field.from=3;
 const wrong=reviewBindingPreview(s,files);assert.equal(wrong.files[0].examples[0].value,'g03');assert.equal(wrong.files[0].examples[1].value,'g03');
 assert.equal(JSON.stringify({...s,levels:[s.levels[0],{...s.levels[1],expression:{...s.levels[1].expression,field:{...s.levels[1].expression.field,from:2}}}]}),before);
});

test('review preview explicitly refuses unsupported shapes and parse errors rather than inventing values',async()=>{
 const {reviewBindingPreview}=await import('../static/ladder-view.mjs');
 const complex=structuredClone(spec);complex.levels.push({name:'site',kind:'attribute',expression:{column:'site'}});
 assert.equal(reviewBindingPreview(complex,{}).available,false);
 assert.equal(reviewBindingPreview(spec,{'windows.csv':'a,a\nx,y\n','keys.csv':'window,asset\nx,s\n'}).available,false);
 const altered=structuredClone(spec);altered.sources[0].format='json';
 assert.equal(reviewBindingPreview(altered,{'windows.csv':'[]'}).available,false);
});
