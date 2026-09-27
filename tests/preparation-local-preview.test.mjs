import test from 'node:test';
import assert from 'node:assert/strict';
import {inspectCSV} from '../static/csv-projection.mjs';
import {inspectJSON} from '../static/json-projection.mjs';
import {localColumnSamples} from '../static/preparation-local-preview.mjs';
test('local CSV examples decode quotes, preserve identity text and bound preview size',()=>{
 const table=inspectCSV('id,note\n0001,"two, words"\n0002,"line\nbreak"\n0003,\n0004,not shown\n');
 assert.deepEqual(localColumnSamples(table,0),['0001','0002','0003']);
 assert.deepEqual(localColumnSamples(table,1),['two, words','line\nbreak','[empty cell]']);
 assert.equal(localColumnSamples(inspectCSV('id\n'+ 'x'.repeat(500)+'\n'),0)[0].length,161);
});
test('JSON examples preserve large numeric tokens and omit nested content',()=>{
 const table=inspectJSON('[{"id":9007199254740993,"notes":{"secret":"local"}},{"id":"0001"}]');
 assert.deepEqual(localColumnSamples(table,0),['9007199254740993','"0001"']);
 assert.deepEqual(localColumnSamples(table,1),['[nested field · withheld]','[field absent]']);
});
