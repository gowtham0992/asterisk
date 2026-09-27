// Portable, local-only unfinished setup. Never carries a result or permission.
const encoder=new TextEncoder();
export function setupBackup(seed){
 return {format:'asterisk-setup',version:1,title:seed.title||'',claim:seed.claim||'',evaluation_intent:{target:seed.evaluation_intent?.target||'',unit:seed.evaluation_intent?.unit||''},manual:seed._manual===true,files:seed.files||[]};
}
export function readSetupBackup(text){
 if(encoder.encode(text).length>100000000)throw new Error('Setup backup exceeds 100 MB.');
 let data;try{data=JSON.parse(text)}catch{throw new Error('This is not a valid setup backup.');}
 if(data?.format!=='asterisk-setup'||data.version!==1)throw new Error('Unsupported setup backup.');
 for(const [key,limit] of [['title',120],['claim',3000]])if(typeof data[key]!=='string'||Array.from(data[key]).length>limit)throw new Error('Invalid '+key+' in backup.');
 const intent=data.evaluation_intent;
 if(!intent||!['','unseen_entities','future_observations','new_sites','other'].includes(intent.target)||typeof intent.unit!=='string'||Array.from(intent.unit).length>120)throw new Error('Invalid evaluation intent.');
 if(!Array.isArray(data.files)||data.files.length>80)throw new Error('Invalid backup files.');
 let total=0;const names=new Set();const files=data.files.map(file=>{
  if(!file||typeof file.name!=='string'||typeof file.content!=='string'||!file.name||file.name.length>1000||file.name.split(/[\\/]/).some(p=>!p||p.startsWith('.'))||!/\.(py|csv|md|txt|json)$/i.test(file.name)||names.has(file.name))throw new Error('Invalid or duplicate filename in backup.');
  const size=encoder.encode(file.content).length;total+=size;
  if(size>10000000||total>16000000)throw new Error('Backup exceeds the source-file limits.');
  names.add(file.name);return {name:file.name,content:file.content};
 });
 return {title:data.title,claim:data.claim,evaluation_intent:{target:intent.target,unit:intent.unit},files,_manual:data.manual===true};
}

// A delayed read must not replace work started after the chooser was opened.
export async function restoreSetupFile(file,{isCurrent,canReplace}){
 if(!isCurrent())return null;
 if(!canReplace())throw new Error('Open a new tab to restore this backup without replacing unfinished work.');
 if(file.size>100000000)throw new Error('Setup backup exceeds 100 MB.');
 let text;
 try{text=await file.text()}catch(error){if(!isCurrent())return null;throw error}
 if(!isCurrent())return null;
 if(!canReplace())throw new Error('Your setup changed while reading the backup. Open a new tab to restore it.');
 return readSetupBackup(text);
}
