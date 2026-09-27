// Read original text for display only. Never parse numbers or reconstruct CSV rows.
export function sourceFormats(spec) {
  const formats=new Map();
  const add=(file,format)=>{const values=formats.get(file)||new Set();values.add(format);formats.set(file,values)};
  for(const source of spec.sources){add(source.file,source.format);for(const expr of [source.sample,source.entity])if(expr.lookup)add(expr.lookup.file,expr.lookup.format)}
  return formats;
}
function jsonRanges(text) {
  // Inputs were validated by the executor. Locate top-level array values without
  // JSON.parse/stringify, which would round large integers in unrelated fields.
  const ranges=[];let depth=0,string=false,escape=false,start=null;
  for(let i=0;i<text.length;i++){
    const c=text[i];
    if(string){if(escape)escape=false;else if(c==='\\')escape=true;else if(c==='"')string=false;continue}
    if(depth===1&&start===null&&!/\s/.test(c)&&c!==']')start=i;
    if(c==='"')string=true;
    else if(c==='['||c==='{')depth++;
    else if(c===']'||c==='}'){
      depth--;if(depth===0&&start!==null){ranges.push([start,i]);start=null}
    }else if(c===','&&depth===1){if(start===null)throw new Error('Invalid JSON record boundary');ranges.push([start,i]);start=null}
  }
  return ranges;
}
export function sourceReader(files,spec) {
  const formats=sourceFormats(spec),cache=new Map();
  return ref=>{
    if(!Object.hasOwn(files,ref.file)||typeof files[ref.file]!=='string')return {error:'Original source unavailable.'};
    const choices=formats.get(ref.file);
    if(!choices||choices.size!==1)return {error:'This source has no unambiguous record format. Inspect the original file.'};
    const format=[...choices][0],text=files[ref.file];
    try{
      if(!cache.has(ref.file)){
        if(format==='json')cache.set(ref.file,jsonRanges(text));
        else {const starts=[0],breaks=format==='csv'?/\r\n|[\r\n]/g:/\r\n|[\n\r\v\f\x1c-\x1e\x85\u2028\u2029]/g;let match;while((match=breaks.exec(text)))starts.push(match.index+match[0].length);if(starts.at(-1)===text.length)starts.pop();cache.set(ref.file,starts)}
      }
      let excerpt;
      if(format==='json'){
        if(typeof ref.pointer!=='string'||!/^\/(0|[1-9][0-9]*)$/.test(ref.pointer))throw new Error('Invalid record pointer');
        const range=cache.get(ref.file)[Number(ref.pointer.slice(1))];if(!range)throw new Error('Record is outside the source');
        excerpt=text.slice(...range).trimEnd();
      }else{
        const starts=cache.get(ref.file),a=ref.line_start,b=ref.line_end;
        if(!Number.isSafeInteger(a)||!Number.isSafeInteger(b)||a<1||b<a||b>starts.length)throw new Error('Invalid source line range');
        excerpt=text.slice(starts[a-1],starts[b]??text.length);
      }
      return {text:excerpt.slice(0,4000),shortened:excerpt.length>4000};
    }catch(error){return {error:error.message}}
  };
}
