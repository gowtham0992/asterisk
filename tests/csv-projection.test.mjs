import test from 'node:test';
import assert from 'node:assert/strict';
import {inspectCSV,projectCSV} from '../static/csv-projection.mjs';
test('projection preserves literal identifiers, quoting, BOM, order and record count',()=>{
 const input='\uFEFFsample,age,subject\r\n"001",71," p01 "\r\n"a,b",72,"x""y"\r\n"line\nb",73,0002';
 const result=projectCSV(inspectCSV(input),[2,0]);
 assert.equal(result.content,'\uFEFFsample,subject\r\n"001"," p01 "\r\n"a,b","x""y"\r\n"line\nb",0002');
 assert.deepEqual(result.withheld,['age']);assert.equal(result.records,3);
});
test('unselected values never enter output and all-selected is byte identical',()=>{
 const source='id,private,split\na,SECRET_PERSON,train\nb,SECRET_PERSON,test\n';const table=inspectCSV(source);
 assert.ok(!projectCSV(table,[0,2]).content.includes('SECRET_PERSON'));
 assert.equal(projectCSV(table,[0,1,2]).content,source);
 assert.throws(()=>projectCSV(table,[]));
});
for(const source of ['a,a\nx,y','a,b\nx','a,b\n"x,y','a,b\n"x"oops,y','a,b\nx"y,z'])test('ambiguous CSV rejected: '+JSON.stringify(source),()=>assert.throws(()=>inspectCSV(source)));
