import test from 'node:test';
import assert from 'node:assert/strict';
import {stageFiles} from '../static/file-import.js';
const file=(name,text='',size=new TextEncoder().encode(text).length,path='')=>({name,size,webkitRelativePath:path,text:async()=>text,arrayBuffer:async()=>new TextEncoder().encode(text).buffer});
const config=JSON.stringify({schema_version:1,arguments:{split_file:'split.csv',mapping_file:'map.csv'},title:'New title'});
test('failed batch does not modify existing files or expose a configuration',async()=>{
 const existing=[{name:'old.csv',content:'original'}];
 await assert.rejects(stageFiles(existing,[file('asterisk.json',config),file('large.csv','',10000001)]),/10 MB/);
 assert.deepEqual(existing,[{name:'old.csv',content:'original'}]);
});
test('duplicate names cannot silently replace an existing source',async()=>{
 const existing=[{name:'split.csv',content:'original'}];await assert.rejects(stageFiles(existing,[file('split.csv','changed')]),/already selected/);assert.equal(existing[0].content,'original');
});
test('duplicate names within one batch are rejected',async()=>{await assert.rejects(stageFiles([],[file('x.csv','a'),file('x.csv','b')]),/already selected/)});
test('unsupported and hidden files are reported without reading them',async()=>{
 const blocked=name=>({...file(name),text:async()=>{throw Error('must not read')},arrayBuffer:async()=>{throw Error('must not read')}});
 const b=await stageFiles([],[blocked('.env'),blocked('photo.png'),file('x.csv','id\na')]);assert.deepEqual(b.skipped,['.env','photo.png']);assert.equal(b.added,1);
});
test('nested configuration paths are resolved and source bytes preserved',async()=>{
 const b=await stageFiles([],[file('asterisk.json',config,config.length,'dataset/asterisk.json'),file('split.csv','sample,split\r\na,train\r\n',23,'dataset/split.csv')]);
 assert.equal(b.configuration.arguments.split_file,'dataset/split.csv');assert.equal(b.files[0].content,'sample,split\r\na,train\r\n');assert.equal(b.added,1);
});
test('count and aggregate size limits reject before oversized contents are read',async()=>{
 await assert.rejects(stageFiles(Array.from({length:80},(_,i)=>({name:i+'.csv',content:''})),[file('new.csv')]),/80 files/);
 const large='a'.repeat(9000000);await assert.rejects(stageFiles([],[file('a.csv',large),file('b.csv','',9000000)]),/16 MB/);
});
test('multiple or malformed configurations fail the batch',async()=>{
 await assert.rejects(stageFiles([],[file('asterisk.json','{')]),/valid JSON/);
 await assert.rejects(stageFiles([],[file('asterisk.json',config),file('asterisk.json',config)]),/one asterisk.json/);
});

const bytesFile=(name,bytes)=>({name,size:bytes.length,webkitRelativePath:'',text:async()=>new TextDecoder().decode(bytes),arrayBuffer:async()=>bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength)});
test('malformed UTF-8 is rejected rather than converting identity bytes to replacement characters',async()=>{
 for(const byte of [0x80,0x81]){
  const bytes=Uint8Array.from([...new TextEncoder().encode('sample,identity\na,'),byte,10]);
  await assert.rejects(stageFiles([],[bytesFile('identity.csv',bytes)]),/identity\.csv.*UTF-8/);
 }
});
test('late encoding failure leaves existing sources intact and returns no staged configuration',async()=>{
 const existing=[{name:'old.csv',content:'original'}];
 await assert.rejects(stageFiles(existing,[file('asterisk.json',config),file('valid.csv','id\na'),bytesFile('bad.csv',Uint8Array.of(0xff))]),/Nothing from this selection was added/);
 assert.deepEqual(existing,[{name:'old.csv',content:'original'}]);
});
test('valid source BOM, Unicode and line endings survive import byte for byte',async()=>{
 const bytes=new TextEncoder().encode('\ufeffsample,identity\r\na,μ\r\nb,�\r\n');
 const batch=await stageFiles([],[bytesFile('unicode.csv',bytes)]);
 assert.deepEqual(new TextEncoder().encode(batch.files[0].content),bytes);
});
test('configuration encoding is checked before JSON parsing',async()=>{
 const bytes=Uint8Array.from([...new TextEncoder().encode(config.replace('New title','BAD')),0xff]);
 await assert.rejects(stageFiles([],[bytesFile('asterisk.json',bytes)]),/asterisk\.json.*UTF-8/);
});
test('valid UTF-8 BOM in a configuration is accepted',async()=>{
 const batch=await stageFiles([],[bytesFile('asterisk.json',new TextEncoder().encode('\ufeff'+config))]);
 assert.equal(batch.configuration.title,'New title');
});

// The ZIP helper receives file text, then uses the same atomic import path.
import {preparedZipFiles} from '../static/file-import.js';
test('prepared archive imports columns through the existing staging path',async()=>{
 const config={schema_version:1,arguments:{split_file:'splits.csv',mapping_file:'entities.csv'},confirmation:{confirmed:true}};
 let options;
 const incoming=await preparedZipFiles(new File(['zip'],'prepared.zip'),async(path,request)=>{
  assert.equal(path,'/api/investigations/import-prepared');options=request;
  return {ok:true,json:async()=>({files:[{name:'asterisk.json',content:JSON.stringify(config)},{name:'splits.csv',content:'sample,partition\na,train\n'}]})};
 });
 assert.equal(options.headers['X-Asterisk-Request'],'1');
 const batch=await stageFiles([],incoming);
 assert.equal(batch.files.length,1);
 assert.equal(batch.configuration.arguments.split_file,'splits.csv');
});
test('archive rejection preserves the original selection',async()=>{
 const old=[{name:'old.csv',content:'x'}];
 await assert.rejects(preparedZipFiles(new File(['bad'],'bad.zip'),async()=>({ok:false,json:async()=>({detail:'Invalid archive'})})),/Invalid archive/);
 assert.deepEqual(old,[{name:'old.csv',content:'x'}]);
});
