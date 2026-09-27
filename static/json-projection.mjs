// Parse structure while retaining literal scalar tokens. Never round numeric IDs
// through a JavaScript Number. Reject duplicate keys, even in withheld objects.
export function inspectJSON(text){
 if(typeof text!=='string'||new TextEncoder().encode(text).length>32_000_000)throw Error('JSON exceeds the 32 MB local inspection limit.');
 let i=0,nodes=0;const ws=()=>{while(/[\x20\t\r\n]/.test(text[i]||'!'))i++};
 const fail=()=>{throw Error('Malformed or ambiguous JSON; correct it locally before uploading.')};
 function string(){const start=i;if(text[i++]!=='"')fail();while(i<text.length){if(text[i]==='\\'){i+=2;continue}if(text[i++]==='"'){const raw=text.slice(start,i);try{return JSON.parse(raw)}catch{fail()}}}fail()}
 function value(depth=0){
  if(depth>64||++nodes>2_000_000)throw Error('JSON exceeds structural inspection limits.');
  ws();const start=i,c=text[i];let fields=null,type='scalar';
  if(c==='"')string();
  else if(c==='{'){
   type='object';fields=new Map();i++;ws();if(text[i]!=='}')while(true){ws();const key=string();if(fields.has(key))fail();ws();if(text[i++]!==':')fail();const v=value(depth+1);fields.set(key,v);ws();if(text[i]!==',')break;i++;}
   if(text[i++]!=='}')fail();
  }else if(c==='['){type='array';i++;ws();if(text[i]!==']')while(true){value(depth+1);ws();if(text[i]!==',')break;i++;}if(text[i++]!==']')fail();}
  else{const match=/^(?:true|false|null|-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?)/.exec(text.slice(i));if(!match)fail();i+=match[0].length;}
  return {start,end:i,type,fields};
 }
 ws();if(text[i++]!=='[')throw Error('Choose a JSON array of objects; nested dataset containers need local preparation.');
 const rows=[],headers=[],blocked=new Set();ws();
 if(text[i]!==']')while(true){
  const row=value();if(row.type!=='object')throw Error('Every JSON record must be an object.');
  rows.push(row.fields);if(rows.length>100000)throw Error('JSON exceeds 100,000 records.');
  for(const [key,v] of row.fields){if(!key)fail();if(!headers.includes(key))headers.push(key);if(headers.length>80)throw Error('JSON exceeds 80 fields.');if(v.type!=='scalar')blocked.add(key)}
  ws();if(text[i]!==',')break;i++;
 }
 if(text[i++]!==']')fail();ws();if(i!==text.length)fail();
 if(!rows.length)throw Error('JSON contains no records.');
 return {format:'json',text,rows,headers,recordCount:rows.length,blocked:[...blocked]};
}
export function projectJSON(table,columns){
 if(!Array.isArray(columns)||!columns.length||new Set(columns).size!==columns.length||columns.some(i=>!Number.isInteger(i)||i<0||i>=table.headers.length))throw Error('Choose at least one valid JSON field.');
 const included=[...columns].sort((a,b)=>a-b).map(i=>table.headers[i]);
 if(included.some(k=>table.blocked.includes(k)))throw Error('Choose scalar identifier or partition fields; nested objects and arrays cannot be sent by this projector.');
 const content='[\n'+table.rows.map(row=>'{'+included.map(key=>{const field=row.get(key);if(!field)throw Error('A selected JSON field is missing from a record.');return JSON.stringify(key)+':'+table.text.slice(field.start,field.end)}).join(',')+'}').join(',\n')+'\n]';
 if(new TextEncoder().encode(content).length>10_000_000)throw Error('Selected JSON fields exceed the 10 MB upload limit.');
 return {content,included,withheld:table.headers.filter(k=>!included.includes(k)),records:table.recordCount};
}
