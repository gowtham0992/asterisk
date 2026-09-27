import {sourceLocation} from './preparation-support/lineage-preview.mjs';
// These are raw-value repetitions, never a duplicate-observation verdict.
export function renderRepetitions(parent,source,column=null,readSource=null){
 const all=column===null?Object.keys(source.repeated_examples||{}):[column];
 const repeated=all.filter(name=>source.repeated_examples?.[name]?.length);
 if(!repeated.length)return;
 const doc=parent.ownerDocument,el=(tag,text)=>{const n=doc.createElement(tag);if(text!==undefined)n.textContent=text;return n};
 const details=el('details');details.className='preparation-repetitions';
 details.append(el('summary',column===null?'Inspect repeated values before using row identities':'Inspect records sharing this ID'));
 details.append(el('p','These exact text values repeat in the original file. They may identify subjects, observations, or ordinary categories. Read the documentation before changing the observation or retransmission policy.'));
 if(repeated.length>8)details.append(el('p',`Showing 8 of ${repeated.length} columns with repeats. Select another column to inspect its examples.`));
 for(const name of repeated.slice(0,8)){
  const group=el('section');group.append(el('h4',name));
  const examples=source.repeated_examples[name];
  group.append(el('p',`Showing ${examples.length} of ${source.identity_counts[name].repeated_values.toLocaleString()} repeated values in ${source.file}. Counts use the complete file.`));
  for(const example of examples){
   const row=el('div');row.className='preparation-repeat-example';
   row.append(el('code',JSON.stringify(example.value)),el('p',`${example.record_count.toLocaleString()} source records share this value. Showing ${example.locations.length} locations:`));
   const list=el('ul');for(const location of example.locations){
    const item=el('li'),label=`Record ${location.record_number.toLocaleString()} · ${sourceLocation(location.reference)}`;
    if(!readSource)item.append(el('span',label));
    else {
     const passage=el('details');passage.className='source-passage';passage.append(el('summary',label));let loaded=false;
     passage.addEventListener('toggle',()=>{
      if(!passage.open||loaded)return;loaded=true;
      const excerpt=readSource(location.reference);
      if(excerpt.error)passage.append(el('p',excerpt.error));
      else {
       if(source.header_reference){
        const header=readSource(source.header_reference);
        passage.append(el('p','Original CSV header'));
        if(header.error)passage.append(el('p',header.error));
        else {passage.append(el('pre',header.text));if(header.shortened)passage.append(el('p','Header shortened to 4,000 characters. Consult the original file for every column.'));}
        passage.append(el('p','Original record'));
       }
       passage.append(el('pre',excerpt.text));if(excerpt.shortened)passage.append(el('p','Showing the first 4,000 characters. Inspect the original file for the complete record.'));}
     });item.append(passage);
    }
    list.append(item);
   }
   row.append(list);group.append(row);
  }
  details.append(group);
 }
 parent.append(details);
}
