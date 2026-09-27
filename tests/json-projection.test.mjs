import test from 'node:test';
import assert from 'node:assert/strict';
import {inspectJSON,projectJSON} from '../static/json-projection.mjs';
test('preserves exact numeric and string tokens while removing narratives',()=>{
 const source='[{"image":"path/a","id":9007199254740993,"notes":[{"text":"PRIVATE"}]},{"image":"path/b","id":-0,"notes":[]}]';
 const table=inspectJSON(source),result=projectJSON(table,[0,1]);
 assert.ok(result.content.includes('9007199254740993'));assert.ok(result.content.includes('"id":-0'));assert.ok(!result.content.includes('PRIVATE'));
 assert.deepEqual(result.withheld,['notes']);assert.deepEqual(table.blocked,['notes']);assert.throws(()=>projectJSON(table,[2]));
});
for(const text of ['[{"id":1,"id":2}]','[{"id":1,"hidden":{"x":1,"x":2}}]','[{"id":01}]','[{"id":1,}]','[{"id":NaN}]','[{"id":"bad\ntext"}]','[{"id":1}] junk','{"records":[]}','[1]'])test('rejects ambiguous JSON '+JSON.stringify(text),()=>assert.throws(()=>inspectJSON(text)));
test('never invents a value for a missing field',()=>assert.throws(()=>projectJSON(inspectJSON('[{"id":"a"},{"other":"b"}]'),[0])));
test('escaped key duplicates are rejected',()=>assert.throws(()=>inspectJSON('[{"id":1,"\\u0069d":2}]')));
