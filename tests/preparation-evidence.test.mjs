import test from 'node:test';
import assert from 'node:assert/strict';
import {citedPassage,evidenceDisclosure} from '../static/preparation-evidence.mjs';
test('citations use original text, preserve numbering and ignore fabricated saved quotes',()=>{
 const result=citedPassage({'notes.txt':'intro\r\nreal <script>\u2028last\n'},{file:'notes.txt',start_line:2,end_line:3,quote:'invented'});
 assert.deepEqual(result.lines,[{number:2,text:'real <script>'},{number:3,text:'last'}]);
});
test('missing, invalid, oversized and inherited sources are unavailable, not substituted',()=>{
 for(const citation of [{file:'missing',start_line:1,end_line:1},{file:'notes',start_line:0,end_line:1},{file:'notes',start_line:'1',end_line:1},{file:'notes',start_line:1,end_line:2}])assert.ok(citedPassage({notes:'one'},citation).error);
 assert.ok(citedPassage(Object.create({notes:'inherited'}),{file:'notes',start_line:1,end_line:1}).error);
 assert.ok(citedPassage({notes:'a'.repeat(8001)},{file:'notes',start_line:1,end_line:1}).error);
 assert.ok(citedPassage({notes:Array(41).fill('a').join('\n')},{file:'notes',start_line:1,end_line:41}).error);
 assert.equal(citedPassage({notes:'😀'.repeat(8000)},{file:'notes',start_line:1,end_line:1}).lines.length,1);
});
test('passage rendering is lazy, text-based and does not duplicate on reopening',()=>{
 const el=(tag,attrs={},...children)=>({tag,attrs,children,events:{},append(...items){this.children.push(...items)},addEventListener(name,fn){this.events[name]=fn}});
 const source=evidenceDisclosure(el,{notes:'<img src=x>'},{file:'notes',start_line:1,end_line:1});const body=source.children[1];assert.equal(body.children.length,0);
 source.events.toggle();assert.equal(body.children.length,0);source.open=true;source.events.toggle();assert.equal(body.children.length,2);
 assert.equal(body.children[1].children[0].children[1].children[0],'<img src=x>');source.events.toggle();assert.equal(body.children.length,2);
});
