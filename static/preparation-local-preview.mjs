// Display-only samples. Never infer safe fields or modify the projection.
export function localColumnSamples(table,index){
 const name=table.headers[index];
 const rows=table.format==='json'?table.rows.slice(0,3):table.rows.slice(1,4);
 return rows.map(row=>{
  let value;
  if(table.format==='json'){
   const field=row.get(name);
   if(!field)return '[field absent]';
   if(field.type!=='scalar')return '[nested field · withheld]';
   value=table.text.slice(field.start,Math.min(field.end,field.start+161));
  }else{
   const raw=row.fields[index];
   value=raw.startsWith('"')?raw.slice(1,-1).replaceAll('""','"'):raw;
  }
  return value===''?'[empty cell]':value.length>160?value.slice(0,160)+'…':value;
 });
}
