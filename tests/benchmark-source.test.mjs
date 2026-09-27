import test from 'node:test';
import assert from 'node:assert/strict';
import {readPinnedSource,loadDermaBenchmark,DERMA_BASE} from '../static/benchmark-source.mjs';
const text='sample,split\na,train\n';
const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text))),n=>n.toString(16).padStart(2,'0')).join('');
test('pinned download preserves bytes and omits credentials and referrer',async()=>{
 let options;const result=await readPinnedSource('https://example.invalid/file',digest,async(url,opts)=>{options=opts;return new Response(text)});
 assert.equal(result,text);assert.equal(options.credentials,'omit');assert.equal(options.referrerPolicy,'no-referrer');assert.equal(options.redirect,'error');
});
test('changed source cannot become a loaded example',async()=>{
 await assert.rejects(readPinnedSource('source',digest,async()=>new Response(text+'changed')),/pinned version/);
});
test('source size bound cancels the stream',async()=>{
 let cancelled=false;const body=new ReadableStream({start(c){c.enqueue(new Uint8Array(2_000_001))},cancel(){cancelled=true}});
 await assert.rejects(readPinnedSource('source',digest,async()=>new Response(body)),/size limit/);assert.equal(cancelled,true);
});
test('benchmark stops on first failed source without accepting partial files',async()=>{
 const urls=[];await assert.rejects(loadDermaBenchmark(async url=>{urls.push(url);return new Response('',{status:503})}),/could not be downloaded/);
 assert.equal(urls.length,1);assert.equal(urls[0],DERMA_BASE+'dermamnist_split_info.csv');
});
