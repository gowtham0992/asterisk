import test from 'node:test';
import assert from 'node:assert/strict';
import {setupReadiness} from '../static/setup-readiness.js';
const complete={target:'unseen_entities',unit:'patients',title:'Patient split',claim:'Evaluation patients must be absent from training.',fileCount:2,manual:true,consent:false};
test('manual setup is ready without provider consent',()=>assert.equal(setupReadiness(complete).ready,true));
test('model setup never treats a saved configuration as upload consent',()=>{
 const state=setupReadiness({...complete,manual:false});assert.equal(state.ready,false);assert.equal(state.next.id,'proposal-consent');
 assert.equal(setupReadiness({...complete,manual:false,consent:true}).ready,true);
});
test('unsupported intent remains blocked even when other fields are complete',()=>{
 const state=setupReadiness({...complete,target:'future_observations'});assert.equal(state.ready,false);assert.equal(state.next.id,'evaluation-target');
});
test('whitespace and short claims are caught before saving',()=>{
 for(const field of ['unit','title','claim'])assert.equal(setupReadiness({...complete,[field]:'  '}).ready,false);
 assert.equal(setupReadiness({...complete,claim:'short'}).next.id,'investigation-claim');
});
test('reading files and saving cannot present a ready action',()=>{
 assert.equal(setupReadiness({...complete,reading:true}).ready,false);
 assert.equal(setupReadiness({...complete,saving:true}).message,'Saving this setup…');
});
test('removing the last file identifies the missing input without resetting the other fields',()=>{
 const state=setupReadiness({...complete,fileCount:0});assert.equal(state.next.id,'investigation-files');assert.equal(state.complete,5);
});
test('character bounds match server code point counts including non-BMP text',()=>{
 assert.equal(setupReadiness({...complete,claim:'😀'.repeat(9)}).ready,false);
 assert.equal(setupReadiness({...complete,claim:'😀'.repeat(10)}).ready,true);
 assert.equal(setupReadiness({...complete,title:'a'.repeat(121)}).ready,false);
 assert.equal(setupReadiness({...complete,claim:'a'.repeat(3001)}).ready,false);
});
