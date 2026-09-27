// Fixed public sources only. Nothing is posted to Asterisk or a model here.
export const DERMA_BASE='https://raw.githubusercontent.com/kakumarabhishek/Corrected-Skin-Image-Datasets/ac655ac5a5b93264c57d69d6d520778d915bfc89/DermaMNIST/DermaMNIST_Analysis/';
export const DERMA_SOURCES=[
 {name:'dermamnist_split_info.csv',sha256:'0c9b1719bf04fa9ad3cdee2a852067a8b848795624e88ea794df40fd13c099f0'},
 {name:'HAM10000_metadata.csv',sha256:'de17ec44cb25ea9c3f6378ba18d69224c740afd62e86ec2edc6a894d6aa663d3'}
];
export async function readPinnedSource(url,expected,fetcher=fetch,signal){
 const response=await fetcher(url,{credentials:'omit',referrerPolicy:'no-referrer',redirect:'error',signal});
 if(!response.ok)throw Error('The public source could not be downloaded. Try again or choose local files.');
 const reader=response.body?.getReader();if(!reader)throw Error('This browser could not read the source download. Choose local files instead.');
 const chunks=[];let size=0;
 try{while(true){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>2_000_000)throw Error('The source exceeds the pinned example size limit.');chunks.push(value)}}
 catch(error){await reader.cancel().catch(()=>{});throw error}finally{reader.releaseLock()}
 const bytes=new Uint8Array(size);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length}
 const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),n=>n.toString(16).padStart(2,'0')).join('');
 if(digest!==expected)throw Error('The public source does not match the pinned version. Nothing was loaded; do not use changed files as this example.');
 return new TextDecoder('utf-8',{fatal:true}).decode(bytes);
}
export async function loadDermaBenchmark(fetcher=fetch){
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),30000);
 try{
  const files=[];
  for(const source of DERMA_SOURCES){const content=await readPinnedSource(DERMA_BASE+source.name,source.sha256,fetcher,controller.signal);files.push(new File([content],source.name,{type:'text/csv'}))}
  const documentation='DermaMNIST original split — source context, not an overlap answer.\n'
   +'Source: '+DERMA_BASE+'README.md\n'
   +'The source README describes dermamnist_split_info.csv as an image_id to split mapping and HAM10000_metadata.csv as containing the lesion_id to image_id mapping. This is a developer paraphrase; inspect the original source.\n'
   +'Requested evaluation unit: lesions, not patients. Compare train with test; val is excluded. Review this claim before accepting it.\n'
   +'Source files are pinned to commit ac655ac5a5b93264c57d69d6d520778d915bfc89. Their SHA-256 hashes were checked in the browser. Original metadata contains personal attributes; select identifier columns only.\n'
   +'Attribution: Kumar Abhishek, Aditi Jain and Ghassan Hamarneh, Investigating the Quality of DermaMNIST and Fitzpatrick17k Dermatological Image Datasets, Scientific Data (2025), doi:10.1038/s41597-025-04382-5. Original HAM10000: Tschandl, Rosendahl and Kittler (2018), doi:10.1038/sdata.2018.161.\n';
  files.push(new File([documentation],'benchmark-context.txt',{type:'text/plain'}));return files;
 }catch(error){if(controller.signal.aborted)throw Error('The public source download timed out. No partial example was loaded. Try again or choose local files.');throw error}finally{clearTimeout(timer)}
}
