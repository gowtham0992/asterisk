// Read-only views of saved input text. Embedded text is never treated as verified.
export function sourceCatalog(files){
 const entries=files.map(f=>({name:f.name,content:f.content,origin:null}));
 for(const file of files){
  if(!file.name.endsWith('preparation-review.json'))continue;
  let record;try{record=JSON.parse(file.content)}catch{continue}
  if(record?.schema_version!==2||![2,3].includes(record.review?.schema_version)||!record.inputs||Array.isArray(record.inputs)||typeof record.inputs!=='object')continue;
  const sources=Object.entries(record.inputs);
  if(sources.length>80||sources.some(([,text])=>typeof text!=='string'))continue;
  for(const [name,content]of sources){if(entries.length>=160)break;entries.push({name,content,origin:file.name})}
 }
 return entries;
}
function sourceLines(content){
 const lines=content?content.split(/\r\n|[\n\r\v\f\x1c-\x1e\x85\u2028\u2029]/):[];
 if(lines.at(-1)==='')lines.pop();
 return lines;
}
// Re-read cited text from embedded inputs; never display the saved quote as proof.
export function preparationContext(files){
 const contexts=[];
 for(const file of files){
  if(!file.name.endsWith('preparation-review.json'))continue;
  let record;try{record=JSON.parse(file.content)}catch{continue}
  if(record?.schema_version!==2||![2,3].includes(record.review?.schema_version)||!Array.isArray(record.review.decisions)||!record.inputs)continue;
  const choices=[];
  for(const decision of record.review.decisions.slice(0,8)){
   if(!decision||typeof decision.file!=='string')continue;
   const definitions=record.review.extraction?.spec?.sources;
   const source=Array.isArray(definitions)?definitions.find(s=>s?.file===decision.file):null;
   const passages=[];
   for(const cite of (Array.isArray(decision.evidence)?decision.evidence:[]).slice(0,2)){
    const content=record.inputs[cite?.file];
    if(typeof content!=='string'||!Number.isInteger(cite.start_line)||!Number.isInteger(cite.end_line)||cite.start_line<1||cite.end_line<cite.start_line||cite.end_line-cite.start_line>=40)continue;
    const lines=sourceLines(content);if(cite.end_line>lines.length)continue;
    const text=lines.slice(cite.start_line-1,cite.end_line).join('\n');
    passages.push({file:cite.file,start:cite.start_line,end:cite.end_line,text:text.slice(0,4000),shortened:text.length>4000});
   }
   choices.push({file:decision.file.slice(0,300),sample:identityDescription(decision.sample),entity:identityDescription(source?.entity||decision.entity),repeats:decision.repeats==='collapse'?'Combine repeated observation IDs':decision.repeats==='distinct'?'Keep observations distinct':'Unrecognized repeat policy',passages});
  }
  contexts.push({file:file.name,choices,more:Math.max(0,record.review.decisions.length-8)});
 }
 return contexts;
}
function identityDescription(value){
 const short=x=>typeof x==='string'?x.slice(0,300):'?';
 if(value?.row===true)return 'Each source record';
 if(value?.lookup)return short(value.lookup.value_column)+' in '+short(value.lookup.file)+', matched by '+short(value.lookup.key_column);
 if(typeof value?.column==='string')return short(value.column)+(value.basename?' → filename':'')+(Number.isInteger(value.prefix)?' → first '+value.prefix+' characters':'');
 return 'Read the original preparation record';
}
export function sourceMatches(content,query){
 if(!query)return {total:0,lines:[]};
 const needle=query.toLowerCase(),matches=[];let total=0;
 sourceLines(content).forEach((line,i)=>{if(line.toLowerCase().includes(needle)){total++;if(matches.length<1000)matches.push(i+1)}});
 return {total,lines:matches};
}
export function sourcePage(content,page=0){
 const lines=sourceLines(content);
 const pages=Math.max(1,Math.ceil(lines.length/60)),index=Math.max(0,Math.min(pages-1,page));
 return {page:index,pages,total:lines.length,lines:lines.slice(index*60,index*60+60).map((text,i)=>({number:index*60+i+1,text:text.slice(0,2000),shortened:text.length>2000}))};
}
