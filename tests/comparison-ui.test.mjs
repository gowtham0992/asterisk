import assert from 'node:assert/strict';
import {comparisonNotice,comparisonVerdict} from '../static/investigations.js';
// Historical records must not silently acquire the new comparison guarantee.
for (const old of [{partition_only_change:true},{partition_only_change:false},{}]) {
 assert.match(comparisonNotice(old).heading,/Earlier comparison/);
 assert.match(comparisonNotice(old).note,/not a guarantee of unchanged features/);
}
const compatible=comparisonNotice({schema_version:2,identity_membership_comparable:true});
assert.match(compatible.heading,/Same samples and identities/);
assert.match(compatible.note,/Other input fields may differ/);
assert.match(comparisonNotice({schema_version:2,identity_membership_comparable:false}).heading,/scope differs/);
console.log('Comparison UI: historical and current records passed');

assert.match(comparisonVerdict('clear_pending_confirmation'),/needs confirmation/);
assert.match(comparisonVerdict('clear'),/identity confirmed/);
assert.equal(comparisonVerdict('made_up'), 'No supported verdict');
