import test from 'node:test';
import assert from 'node:assert/strict';
import {sourceCatalog,sourcePage,sourceMatches} from '../static/source-reader.js';
test('embedded source is explicitly attributed without changing stored inputs',()=>{
 const files=[{name:'preparation-review.json',content:JSON.stringify({schema_version:2,review:{schema_version:3},inputs:{'notes.txt':'<script>not markup</script>'}})}];
 const before=JSON.stringify(files),catalog=sourceCatalog(files);
 assert.equal(catalog[1].origin,'preparation-review.json');assert.equal(catalog[1].content,'<script>not markup</script>');assert.equal(JSON.stringify(files),before);
});
test('ordinary JSON and malformed nested inputs remain raw sources',()=>{
 for(const content of ['broken',JSON.stringify({inputs:{a:'text'}}),JSON.stringify({schema_version:2,review:{schema_version:3},inputs:{a:42}})])assert.equal(sourceCatalog([{name:'preparation-review.json',content}]).length,1);
});
test('paging preserves logical line numbers and exposes the final page',()=>{
 const source=Array.from({length:125},(_,i)=>'line '+(i+1)).join('\r\n')+'\r\n';
 assert.equal(sourcePage(source).lines.length,60);
 assert.equal(sourcePage(source,1).lines[0].number,61);
 assert.equal(sourcePage(source,99).lines.at(-1).number,125);
 assert.equal(sourcePage(source,-1).page,0);
});
test('line breaks match source citations and long lines are explicitly shortened',()=>{
 assert.deepEqual(sourcePage('a\rb\u2028c\n').lines.map(x=>x.text),['a','b','c']);
 const page=sourcePage('x'.repeat(3000));assert.equal(page.lines[0].text.length,2000);assert.equal(page.lines[0].shortened,true);
 assert.equal(sourcePage('').total,0);
});

test('search is literal, case-insensitive and preserves original line numbering',()=>{
 assert.deepEqual(sourceMatches('a.b\r\nA.B\naxb','a.b'),{total:2,lines:[1,2]});
 assert.deepEqual(sourceMatches('patient\u2028subject','subject'),{total:1,lines:[2]});
 assert.deepEqual(sourceMatches('abc','['),{total:0,lines:[]});
 assert.deepEqual(sourceMatches('abc',''),{total:0,lines:[]});
});
test('search counts all matching lines but bounds navigation storage',()=>{
 const result=sourceMatches(Array(1200).fill('match').join('\n'),'match');
 assert.equal(result.total,1200);assert.equal(result.lines.length,1000);assert.equal(result.lines.at(-1),1000);
});

import {preparationContext} from '../static/source-reader.js';
function prepared(overrides={}){
 const record={schema_version:2,inputs:{'notes.txt':'First line\nActual subject definition.\n'},review:{schema_version:3,decisions:[{file:'data.csv',sample:{column:'capture'},repeats:'distinct',evidence:[{file:'notes.txt',start_line:2,end_line:2,quote:'Invented claim'}]}],extraction:{spec:{sources:[{file:'data.csv',entity:{column:'path',basename:true,prefix:12}}]}}}};
 overrides(record);return [{name:'preparation-review.json',content:JSON.stringify(record)}];
}
test('preparation context uses embedded source text rather than the saved quote',()=>{
 const result=preparationContext(prepared(()=>{}))[0].choices[0];
 assert.equal(result.passages[0].text,'Actual subject definition.');
 assert.equal(result.sample,'capture');assert.equal(result.entity,'path → filename → first 12 characters');
 assert.equal(result.repeats,'Keep observations distinct');
});
test('malformed source definitions and out-of-range passages stay nonauthoritative',()=>{
 const result=preparationContext(prepared(r=>{r.review.extraction.spec.sources={find:'not a function'};r.review.decisions[0].evidence[0].end_line=99}))[0].choices[0];
 assert.deepEqual(result.passages,[]);assert.equal(result.entity,'Read the original preparation record');
});
test('large preparation context is bounded and does not interpret markup',()=>{
 const result=preparationContext(prepared(r=>{r.inputs['notes.txt']='a\n<script>'+('x'.repeat(4500));r.review.decisions=Array(12).fill(r.review.decisions[0])}))[0];
 assert.equal(result.choices.length,8);assert.equal(result.more,4);
 assert.equal(result.choices[0].passages[0].text.length,4000);assert.equal(result.choices[0].passages[0].shortened,true);
 assert.match(result.choices[0].passages[0].text,/^<script>/);
});
