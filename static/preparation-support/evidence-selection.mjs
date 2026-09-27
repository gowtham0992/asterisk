// A click starts a range; a second click finishes it in either direction.
// A completed range may also be one line. No source meaning is inferred here.
export function selectLine(selection,line,total){
  if(!Number.isInteger(line)||!Number.isInteger(total)||line<1||line>total)throw new Error('Select an existing source line.');
  if(selection?.anchor){
    const start=Math.min(selection.anchor,line),end=Math.max(selection.anchor,line);
    if(end-start>=40)throw new Error('Select at most 40 lines of supporting evidence.');
    return {start,end,anchor:null};
  }
  return {start:line,end:line,anchor:line};
}
export function manualRange(start,end,total){
  if(!Number.isInteger(start)||!Number.isInteger(end)||start<1||end<start||end>total||end-start>=40)throw new Error('Choose a valid range of at most 40 lines.');
  return {start,end,anchor:null};
}
export function sourceLines(text){
  if(!text)return [];
  const lines=text.split(/\r\n|[\n\r\v\f\x1c-\x1e\x85\u2028\u2029]/);
  if(lines.at(-1)==='')lines.pop();
  return lines;
}
