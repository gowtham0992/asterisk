import {describeIdentity} from './preparation-summary.mjs';
import {sourceLocation} from './preparation-support/lineage-preview.mjs';
const labels={sample:'Observation ID',entity:'Subject ID',partition:'Partition'};
export function renderEvidenceChanges(parent,before,after){
 const doc=parent.ownerDocument;
 const el=(tag,text)=>{const n=doc.createElement(tag);n.textContent=text;return n};
 const describe=items=>items.length?items.map(c=>`${c.file} · lines ${c.start_line}–${c.end_line}`).join('; '):'No supporting passage';
 const key=items=>JSON.stringify(items.map(c=>[c.file,c.start_line,c.end_line]).sort());
 const section=el('section','');section.className='preparation-changes';
 section.append(el('h3','Supporting evidence changes'));
 let changed=false;
 for(const [file,policy]of Object.entries(after)){
  const previous=before[file]?.evidence||[],next=policy.evidence||[];
  if(key(previous)===key(next))continue;
  changed=true;section.append(el('h4',file),el('p',`Before: ${describe(previous)}`),el('p',`After: ${describe(next)}`));
 }
 if(changed){section.append(el('p','Only the cited passages are compared here. Changing a citation does not confirm its meaning or change an existing receipt.'));parent.append(section)}
}
export function renderPreparationChanges(parent,changes){
 const doc=parent.ownerDocument;
 const el=(tag,text,cls)=>{const n=doc.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n};
 const section=el('section',undefined,'preparation-changes');section.append(el('h3','What changes in the source records'));
 if(!changes?.available){section.append(el('p',changes?.reason||'No before-and-after source comparison is available. Review the prepared rows below.'));parent.append(section);return}
 section.append(el('p',`${changes.changed_records.toLocaleString()} of ${changes.source_records.toLocaleString()} original source records change their observation ID, subject ID or partition.`));
 const counts=el('dl',undefined,'preparation-change-counts');
 for(const [field,label]of Object.entries(labels)){const row=el('div');row.append(el('dt',label),el('dd',changes.changed_fields[field].toLocaleString()));counts.append(row)}
 section.append(counts,el('p','Counts refer to original source records, not distinct observations. One record may change in more than one field. Unchanged totals do not mean unchanged assignments.','hint'));
 if(changes.changed_records){
  section.append(el('p',`Showing ${changes.examples.length} of ${changes.changed_records.toLocaleString()} changed source records. These examples do not establish that the new choices are scientifically correct.`,'hint'));
  for(const example of changes.examples){
   const details=el('details');details.append(el('summary',sourceLocation(example.source)));
   const rows=el('dl');
   for(const field of example.changed_fields){const row=el('div');row.append(el('dt',labels[field]||field));const values=el('dd');values.append(el('span','Before'),el('code',JSON.stringify(example.before[field])),el('span','After'),el('code',JSON.stringify(example.after[field])));row.append(values);rows.append(row)}details.append(rows);section.append(details);
  }
 }
 parent.append(section);
}

export function renderObservationChanges(parent,before,after){
 const doc=parent.ownerDocument;
 const el=(tag,text)=>{const n=doc.createElement(tag);n.textContent=text;return n};
 const canonical=value=>value&&typeof value==='object'?Array.isArray(value)?value.map(canonical):Object.fromEntries(Object.keys(value).sort().map(key=>[key,canonical(value[key])])):value;
 const same=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b));
 const section=el('section','');section.className='preparation-changes';
 section.append(el('h3','Review changes to what counts as an observation'));
 let changed=false;
 for(const [file,next] of Object.entries(after)){
  const previous=before[file];if(!previous)continue;
  const identityChanged=!same(previous.sample,next.sample);
  const repeatChanged=previous.repeats!==next.repeats;
  if(!identityChanged&&!repeatChanged)continue;
  changed=true;section.append(el('h4',file));
  if(identityChanged){
   section.append(el('p','Before: '+describeIdentity(previous.sample)),el('p','After: '+describeIdentity(next.sample)));
   const exact=el('details','');exact.append(el('summary','Exact observation expressions'),el('pre',JSON.stringify({before:previous.sample??null,after:next.sample??null},null,2)));section.append(exact);
   if(next.sample?.row===true&&previous.sample?.row!==true)section.append(el('p','Row numbers give every source record a new identifier. This can make conflicting or repeated observation IDs disappear from the structural check without resolving their meaning. Use row identity only when the documentation establishes that each record is a distinct observation; do not use it merely to make a blocked proposal run.'));
   else section.append(el('p','Changing observation identity can change which records count as the same measurement. Check this against the source definition, even if the prepared totals stay the same.'));
  }
  if(repeatChanged)section.append(el('p',`Repeated-record policy: ${previous.repeats??'not recorded'} → ${next.repeats??'not recorded'}. `+(next.repeats==='collapse'?'Combining records requires documented retransmission meaning, not just matching values.':'Keeping records separate does not resolve conflicting identifiers.')));
 }
 if(changed){section.append(el('p','These are policy changes, shown even when the original proposal could not produce rows. Successful execution does not validate the new scientific interpretation.'));parent.append(section)}
}
