import test from 'node:test';
import assert from 'node:assert/strict';
import {uploadSummary} from '../static/preparation-upload-summary.mjs';
const ticket=files=>({messages:[{role:'system',content:'ignored'},{role:'user',content:JSON.stringify({files})}]});
test('summary exposes omitted documentation rather than promising complete context',()=>{
 const [row]=uploadSummary(ticket({'notes.txt':{kind:'documentation',lines:Array(100).fill({}),total_lines:301}}));
 assert.equal(row.detail,'100 documentation lines included of 301');assert.match(row.warning,/201 lines omitted/);
 assert.equal(uploadSummary(ticket({short:{kind:'documentation',lines:[{}],total_lines:1}}))[0].warning,'');
});
test('table summary describes profiles and source values, not full table transmission',()=>{
 const [row]=uploadSummary(ticket({'data.csv':{kind:'csv',records:1200,columns:{sample:{},patient:{}}}}));
 assert.equal(row.detail,'2 column profiles across 1200 records. Includes source values and counts.');
 assert.equal(row.warning,'');
});
test('unknown or malformed profile cannot be described as anonymized or complete',()=>{
 assert.deepEqual(uploadSummary({messages:[]}),[]);
 assert.match(uploadSummary(ticket({unknown:{}}))[0].detail,/Inspect the exact payload/);
 assert.equal(uploadSummary(ticket({'<script>':null}))[0].name,'<script>');
});
