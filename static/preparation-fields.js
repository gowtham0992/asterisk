import {describePartition} from './preparation-summary.mjs';
import {renderRepetitions} from './preparation-repetitions.mjs?v=repeat-excerpts-2';
import {columnExpression,identityExamples,lookupExpression} from './preparation-support/expression-choice.mjs';
import {mountEvidencePicker} from './preparation-evidence-picker.js?v=preparation-search-1';
export function createPolicyFields({node,invalidate,message,restoredLabel="Keep saved",readSource=null}) {
let fieldSequence=0;
function select(label,options,parent){const id='field-'+fieldSequence++;const l=node('label',label);l.htmlFor=id;const s=node('select');s.id=id;s.required=true;s.append(new Option('Choose…',''));for(const [value,text]of options)s.append(new Option(text,value));parent.append(l,s);return s;}
function number(label,parent){const id='line-'+fieldSequence++;const l=node('label',label);l.htmlFor=id;const n=node('input');n.id=id;n.type='number';n.min='1';n.max='100000';parent.append(l,n);return n;}
const evidencePicker=(doc,start,end,files,parent)=>mountEvidencePicker({node,invalidate,message,doc,start,end,files,parent});
function expression(e){if(e.row)return 'Each source record';if(e.lookup)return `${e.lookup.value_column} in ${e.lookup.file}, matched by ${e.lookup.key_column}`;return e.column+(e.basename?' → filename':'')+(e.prefix?` → first ${e.prefix} characters`:'');}
function describeSource(source,parent){parent.append(node('p',`Subject identity: ${expression(source.entity)}`,'muted'));const p=source.partition;parent.append(node('p',p.value?`Partition: ${p.value}`:`Partition column: ${p.column}. `+Object.entries(p.map).map(([a,b])=>`${a} → ${b}`).join('; '),'muted'));}
function identityChoice(label,source,original,saved,parent,allowRows=false,allowLookup=true){
 const options=[...(saved?[['restored',restoredLabel+': '+expression(saved)]]:[]),...(saved&&restoredLabel==='Keep proposed'?[]:[['original','Keep proposed: '+expression(original)]]),...(allowRows?[['row','Each source record is a separate observation']]:[]),...source.columns.map(c=>['col:'+c,'Column: '+c]),...(allowLookup?[['lookup','Look up the identity in another table']]:[])];
 const choice=select(label,options,parent);
 const transforms=node('div',undefined,'identity-transforms');transforms.hidden=true;
 const filenameLabel=node('label',undefined,'check'),filename=node('input');filename.type='checkbox';filename.setAttribute('aria-label',label+' — use the filename after the last /');filenameLabel.append(filename,document.createTextNode('Use filename after the last /'));
 const prefix=number(label+' — keep first characters (optional)',transforms);prefix.max='128';prefix.placeholder='Keep the full value';prefix.setAttribute('aria-label',label+' — keep first characters (optional)');transforms.querySelector('label').textContent='Keep first characters (optional)';
 transforms.prepend(filenameLabel);transforms.append(node('p','Filename extraction runs first, then the character prefix. A prefix longer than any ID is rejected. These operations do not establish what the identity means.','muted'));parent.append(transforms);
 choice.addEventListener('change',()=>{transforms.hidden=!choice.value.startsWith('col:');if(transforms.hidden){filename.checked=false;prefix.value=''}invalidate()});
 const lookup=node('div',undefined,'identity-transforms');lookup.hidden=true;let lookupRead=null;
 if(allowLookup){
  const tables=source.lookup_tables||[],table=select(label+' — lookup table',tables.map(t=>[t.file,t.file]),lookup),key=select('Matching key in lookup table',[],lookup),value=select('Identity value in lookup table',[],lookup);
  const on=identityChoice('Source key to match',source,original?.lookup?.on||{row:true},null,lookup,true,false);
  table.addEventListener('change',()=>{for(const field of [key,value]){field.replaceChildren(new Option('Choose…',''));for(const column of tables.find(t=>t.file===table.value)?.columns||[])field.append(new Option(column,column))}invalidate()});
  lookupRead=()=>lookupExpression(table.value,key.value,value.value,on(),tables);parent.append(lookup);
 }
 choice.addEventListener('change',()=>{lookup.hidden=choice.value!=='lookup';for(const control of lookup.querySelectorAll('select'))control.required=!lookup.hidden;if(lookup.hidden)for(const field of lookup.querySelectorAll('input[type=number]'))field.value='';});
 for(const control of lookup.querySelectorAll('select'))control.required=false;
 if(saved)choice.value='restored';
 const read=()=>{if(!choice.value)throw new Error('Choose '+label.toLowerCase()+'.');if(choice.value==='restored')return saved;if(choice.value==='original')return original;if(choice.value==='row')return {row:true};if(choice.value==='lookup')return lookupRead();return columnExpression(choice.value.slice(4),filename.checked,prefix.value)};
 const examples=node('div',undefined,'identity-examples');examples.hidden=true;parent.append(examples);
 function paintExamples(){
  examples.replaceChildren();examples.hidden=!choice.value;if(!choice.value)return;
  try{
   const selected=read();
   if(selected.row)examples.append(node('p','One source record = one observation. Repeated measurements or retransmissions will remain separate, even when another column repeats. Check the documentation before keeping this choice.','identity-accounting'));
   else if(!selected.lookup&&!selected.basename&&!selected.prefix){
    const counts=source.identity_counts?.[selected.column];
    if(counts)examples.append(node('p',`${source.record_count.toLocaleString()} source records · ${counts.distinct_values.toLocaleString()} distinct text IDs · ${counts.records_with_repeated_values.toLocaleString()} records sharing a repeated ID · ${counts.unusable_records.toLocaleString()} unusable IDs. Repetition alone does not establish whether records are the same observation.`,'identity-accounting'));
   }
   if(selected.row)renderRepetitions(examples,source,null,readSource);
   else if(!selected.lookup&&!selected.basename&&!selected.prefix)renderRepetitions(examples,source,selected.column,readSource);
  }catch{}
  examples.append(node('p','Example IDs · first '+Math.min(3,source.record_count||0)+' of '+(source.record_count||0)+' records','eyebrow'));
  try{const preview=identityExamples(read(),source);if(preview.unavailable)examples.append(node('p',preview.unavailable,'muted'));else for(const row of preview.rows){const line=node('div',undefined,'identity-example');line.append(node('code',row.input===undefined?'(missing)':JSON.stringify(row.input)),node('span','→'),node('code',row.error||JSON.stringify(row.value),row.error?'error':''));examples.append(line)}
  examples.append(node('p','Illustration only. Run the full policy preview to check every record.','muted'));}catch(error){examples.append(node('p',error.message,'error'))}
 }
 for(const control of [choice,filename,prefix])control.addEventListener('input',paintExamples);
 lookup.addEventListener('input',paintExamples);choice.addEventListener('change',paintExamples);paintExamples();
 return read;
}
function bindingChoices(source,parent,saved){
 const subject=node('section',undefined,'preparation-decision-group');subject.append(node('p','02 / Subject','eyebrow'),node('h3','What must stay independent?'),node('p','Choose the identity named by the research claim, such as a patient, lesion or manufactured unit. Different observations of that subject must resolve to the same ID.','hint'));parent.append(subject);
 const entity=identityChoice('Which identity represents the subject?',source,source.entity,saved?.entity,subject);
 const split=node('section',undefined,'preparation-decision-group');split.append(node('p','03 / Partition','eyebrow'),node('h3','Where does each observation belong?'),node('p','Assign every observed label to training, evaluation or exclusion. Labels are exact, including their capitalization and spaces.','hint'));parent.append(split);
 const partition=select('Where is partition membership recorded?',[...(saved?.partition?[['restored',restoredLabel+' partition mapping']]:[]),...(saved?.partition&&restoredLabel==='Keep proposed'?[]:[['original','Keep the proposed partition mapping']]),['constant','All records belong to one partition'],...Object.keys(source.partition_values||{}).map(c=>['col:'+c,'Column: '+c])],split);
 if(saved)partition.value=saved.partition?'restored':'original';
 const mapping=node('div',undefined,'partition-choices');let fields=[];
 const inherited=node('p',undefined,'identity-accounting');inherited.setAttribute('aria-live','polite');split.append(inherited);
 function showInherited(){const selected=partition.value==='restored'?saved.partition:partition.value==='original'?source.partition:null;inherited.hidden=!selected;inherited.textContent=selected?describePartition(selected):'';}
 showInherited();
 const roles=[['train','Training'],['test','Evaluation'],['excluded','Exclude from comparison']];
 partition.addEventListener('change',()=>{showInherited();fields=[];mapping.replaceChildren();if(partition.value==='constant')fields.push([null,select('Partition for all records',roles,mapping)]);else if(partition.value.startsWith('col:'))for(const value of source.partition_values[partition.value.slice(4)])fields.push([value,select('Label '+JSON.stringify(value),roles,mapping)]);invalidate();});
 split.append(mapping,node('p','Every observed label needs an explicit role. This editor lists columns with at most 40 distinct text labels. Column identities support filename and prefix transforms. Lookup joins require an explicit source key, mapping key and identity column. Missing or conflicting mappings block the full preview.','muted'));
 return ()=>{if(!partition.value||fields.some(([,field])=>!field.value))throw new Error('Choose subject identity and every partition role.');return {entity:entity(),partition:partition.value==='restored'?saved.partition:partition.value==='original'?source.partition:partition.value==='constant'?{value:fields[0][1].value}:{column:partition.value.slice(4),map:Object.fromEntries(fields.map(([value,field])=>[value,field.value]))}}};
}

return {select,number,evidencePicker,identityChoice,bindingChoices,describeSource};
}
