// Decode strictly so different invalid byte sequences cannot collapse to one ID.
// Keep a source BOM: receipt hashes must describe the supplied UTF-8 bytes.
async function readSource(file,name){
 const bytes=await file.arrayBuffer();
 try{return new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(bytes)}
 catch{throw new Error(name+': is not valid UTF-8. Export it as UTF-8 and select it again. Nothing from this selection was added.')}
}
// Stage an entire local selection before any form state changes or upload occurs.
export async function stageFiles(existing, incoming) {
 const next=new Map(existing.map(f=>[f.name,f]));
 const skipped=[];let configuration=null,added=0,total=existing.reduce((n,f)=>n+new TextEncoder().encode(f.content).length,0);
 for(const file of incoming){
  const name=file.webkitRelativePath||file.name;
  if(name.split('/').some(p=>p.startsWith('.'))||!/\.(py|csv|md|txt|json)$/i.test(name)){skipped.push(name);continue}
  if(file.size>10000000)throw new Error(name+': exceeds the 10 MB file limit. Nothing from this selection was added.');
  if(file.name==='asterisk.json'){
   if(configuration)throw new Error('Choose one asterisk.json configuration at a time. Nothing from this selection was added.');
   if(file.size>100000)throw new Error('Column configuration exceeds 100 KB.');
   const content=await readSource(file,name);
   let config;try{config=JSON.parse(content.replace(/^\uFEFF/,''))}catch{throw new Error('asterisk.json is not valid JSON. Nothing from this selection was added.')}
   if(config?.schema_version!==1||!config.arguments||['split_file','mapping_file'].some(k=>typeof config.arguments[k]!=='string'||!config.arguments[k]))throw new Error('Unsupported column configuration. Nothing from this selection was added.');
   const prefix=file.webkitRelativePath?file.webkitRelativePath.slice(0,-file.name.length):'';
   configuration={...config,arguments:{...config.arguments,split_file:prefix+config.arguments.split_file,mapping_file:prefix+config.arguments.mapping_file}};
   continue;
  }
  if(next.has(name))throw new Error(name+' is already selected. Remove it first to replace it. Nothing from this selection was added.');
  if(next.size>=80||total+file.size>16000000)throw new Error('Use at most 80 files and 16 MB total. Nothing from this selection was added.');
  const content=await readSource(file,name);total+=new TextEncoder().encode(content).length;
  if(total>16000000)throw new Error('Use at most 80 files and 16 MB total. Nothing from this selection was added.');
  next.set(name,{name,content});added++;
 }
 return {files:[...next.values()],configuration,skipped,added};
}

// Prepared ZIPs are unpacked by this app server, never sent to a model here.
export async function preparedZipFiles(file, fetcher=fetch) {
 if(!file||file.size>18000000)throw new Error('Choose a prepared ZIP below 18 MB.');
 const response=await fetcher('/api/investigations/import-prepared',{method:'POST',headers:{'Content-Type':'application/zip','X-Asterisk-Request':'1'},body:file});
 const result=await response.json();
 if(!response.ok)throw new Error(typeof result.detail==='string'?result.detail:'Could not unpack the prepared ZIP.');
 if(!Array.isArray(result.files))throw new Error('Invalid prepared ZIP response.');
 return result.files.map(f=>new File([f.content],f.name,{type:'text/plain'}));
}
