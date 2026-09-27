import test from 'node:test';
import assert from 'node:assert/strict';
import {describeIdentity,preparationSummary} from '../static/preparation-summary.mjs';
test('saved overrides take precedence while original subject and split remain visible when inherited',()=>{
 const data={sources:[{file:'data.csv',sample:{column:'image'},entity:{column:'patient'},partition:{column:'split',map:{' Train ':'train',test:'test',val:'excluded'}}}],record:{policies:{'data.csv':{sample:{column:'scan'},repeats:'collapse',evidence:[{file:'notes.md',start_line:2,end_line:4}]}}}};
 const rows=Object.fromEntries(preparationSummary(data)[0].rows);
 assert.equal(rows['Observation identity'],'Column "scan"');assert.equal(rows['Subject identity'],'Column "patient"');
 assert.match(rows['Partition membership'],/" Train " → Training/);assert.match(rows['Partition membership'],/"val" → Excluded/);
 assert.equal(rows['Supporting source'],'"notes.md", lines 2–4');assert.match(rows['Repeated observations'],/Combine/);
 data.record.policies['data.csv'].entity={row:true};data.record.policies['data.csv'].partition={value:'test'};
 const overridden=Object.fromEntries(preparationSummary(data)[0].rows);assert.match(overridden['Subject identity'],/Each source record/);assert.equal(overridden['Partition membership'],'All records → Evaluation');
});
test('transform order and lookup keys are explicit; source identifiers remain literal',()=>{
 assert.equal(describeIdentity({column:'barcode',basename:true,prefix:12}),'Column "barcode" → filename after the last / → first 12 characters');
 assert.equal(describeIdentity({lookup:{file:'ids.csv',value_column:'subject',key_column:'image',on:{column:'path',basename:true}}}),'"subject" in "ids.csv", joined on "image" using Column "path" → filename after the last /');
 assert.equal(describeIdentity({column:'<img>'}),'Column "<img>"');
});
