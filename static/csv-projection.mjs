// Strict CSV projection. Selected cells retain their original serialized bytes;
// no numeric conversion, trimming, row filtering or identity inference occurs.
export function inspectCSV(text){
 if(typeof text!=='string'||new TextEncoder().encode(text).length>10_000_000)throw Error('CSV exceeds the 10 MB local review limit.');
 const bom=text.startsWith('\uFEFF')?'\uFEFF':'';let i=bom.length,start=i,quoted=false,closed=false,atStart=true,row=[],rows=[],cells=0;
 function cell(end){row.push(text.slice(start,end));if(++cells>2_000_000||row.length>80)throw Error('CSV exceeds the cell or column limit.');}
 function record(end,newline){cell(end);rows.push({fields:row,newline});if(rows.length>100001)throw Error('CSV exceeds 100,000 data records.');row=[];}
 while(i<text.length){const c=text[i];
  if(quoted){if(c==='"'){if(text[i+1]==='"'){i+=2;continue}quoted=false;closed=true}i++;continue}
  if(c==='"'){if(!atStart||closed)throw Error('Malformed CSV quoting.');quoted=true;atStart=false;i++;continue}
  if(c===','){cell(i);start=++i;atStart=true;closed=false;continue}
  if(c==='\r'||c==='\n'){const newline=c==='\r'&&text[i+1]==='\n'?'\r\n':c;record(i,newline);i+=newline.length;start=i;atStart=true;closed=false;continue}
  if(closed)throw Error('Unexpected text after a quoted CSV field.');atStart=false;i++;
 }
 if(quoted)throw Error('Unterminated quoted CSV field.');
 if(start<text.length||row.length)record(text.length,'');
 if(!rows.length)throw Error('CSV is empty.');
 const decode=s=>s.startsWith('"')?s.slice(1,-1).replaceAll('""','"'):s;
 const headers=rows[0].fields.map(decode);
 if(headers.some(h=>!h)||new Set(headers).size!==headers.length)throw Error('CSV needs nonempty, unique column names.');
 if(rows.some(r=>r.fields.length!==headers.length))throw Error('CSV has inconsistent record widths; fix it locally before uploading.');
 return {bom,headers,rows,recordCount:rows.length-1};
}
export function projectCSV(table,columns){
 if(!Array.isArray(columns)||!columns.length||new Set(columns).size!==columns.length||columns.some(n=>!Number.isInteger(n)||n<0||n>=table.headers.length))throw Error('Choose at least one valid column for each CSV.');
 const indices=[...columns].sort((a,b)=>a-b);
 return {content:table.bom+table.rows.map(row=>indices.map(i=>row.fields[i]).join(',')+row.newline).join(''),
  included:indices.map(i=>table.headers[i]),withheld:table.headers.filter((_,i)=>!indices.includes(i)),records:table.recordCount};
}

export async function projectionRecord(file,original,result){
 const hash=async text=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text))),x=>x.toString(16).padStart(2,'0')).join('');
 return {file,original_sha256:await hash(original),projected_sha256:await hash(result.content),included:result.included,withheld:result.withheld,records:result.records};
}

// Portable context, not a measurement or scientific confirmation.
export function projectionCompanion(files,projection){
 if(!projection?.length)return null;
 let name='asterisk-projection-record.json',suffix=0;
 while(Object.hasOwn(files,name))name='asterisk-projection-record-'+(++suffix)+'.json';
 return {name,content:JSON.stringify({format:'asterisk-client-projection',version:1,
  scope:'Browser-reported projection. Original hashes and withheld names are not authenticated. No anonymization or scientific confirmation.',
  files:projection},null,2)};
}
