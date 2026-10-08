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
