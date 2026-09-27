import {sourceReader} from './source-excerpt.mjs';
// Display only executor-produced rows; this module never infers identity or overlap.
export function lineagePage(lineage, partition='all', page=0, combinedOnly=false, query='') {
  if (!['all','train','test','excluded'].includes(partition)) throw new Error('Unknown partition');
  if(typeof query!=='string'||query.length>4096)throw new Error('Search must be text up to 4,096 characters');
  const rows = lineage.filter(row => (partition === 'all' || row.partition === partition) && (!combinedOnly || row.occurrences?.length > 1) && (!query || row.sample.includes(query) || row.entity.includes(query)));
  const pages = Math.max(1, Math.ceil(rows.length / 10));
  const index = Math.min(Math.max(Number.isSafeInteger(page) ? page : 0, 0), pages - 1);
  return {rows:rows.slice(index*10,index*10+10),total:rows.length,page:index,pages,start:rows.length?index*10+1:0,end:Math.min((index+1)*10,rows.length)};
}
export function sourceLocation(ref) {
  return ref.file+' · '+(ref.pointer !== undefined ? ref.pointer : 'lines '+ref.line_start+'–'+ref.line_end);
}
export function renderLineage(parent, lineage, files, spec) {
  const readSource=sourceReader(files,spec);
  const doc=parent.ownerDocument;
  const el=(tag,text)=>{const item=doc.createElement(tag);if(text!==undefined)item.textContent=text;return item};
  const section=el('section');section.className='prepared-rows';
  section.append(el('h2','Inspect the prepared rows'),el('p','These are the computed observation and subject IDs, including lookup results. Check their meaning before confirming. This is not an overlap verdict.'));
  const searchLabel=el('label','Find observation or subject '),search=el('input');search.type='search';search.maxLength=4096;search.placeholder='Enter all or part of an ID';searchLabel.append(search);section.append(searchLabel,el('p','Matches exact text, including case and spaces. Searches these prepared rows locally.'));section.lastChild.className='muted';
  const label=el('label','Show partition '),filter=el('select');
  for(const [value,text] of [['all','All partitions'],['train','Training'],['test','Evaluation'],['excluded','Excluded']]){const option=el('option',text);option.value=value;filter.append(option)}
  label.append(filter);section.append(label);
  const combinedLabel=el('label'),combined=el('input');combined.type='checkbox';combinedLabel.className='check';combinedLabel.append(combined,doc.createTextNode('Only observations that combine repeated records'));section.append(combinedLabel);
  const status=el('p');status.className='muted';status.setAttribute('role','status');
  const table=el('table');table.append(el('caption','Computed observations'));
  const head=el('thead'),headRow=el('tr');for(const title of ['Observation','Subject','Partition']){const th=el('th',title);th.scope='col';headRow.append(th)}head.append(headRow);table.append(head);
  const body=el('tbody');table.append(body);
  const nav=el('div');nav.className='row-pagination';
  const prev=el('button','Previous rows'),next=el('button','Next rows');for(const button of [prev,next]){button.type='button';button.className='secondary'}
  nav.append(prev,next);section.append(status,table,nav);parent.append(section);
  let page=0;
  function paint(){
    const data=lineagePage(lineage,filter.value,page,combined.checked,search.value);page=data.page;
    status.textContent=data.total?`Rows ${data.start}–${data.end} of ${data.total} matching observations (${lineage.length} total). Page ${data.page+1} of ${data.pages}.`:`No observations match these filters (${lineage.length} total).`;
    prev.disabled=page===0;next.disabled=page+1>=data.pages;table.hidden=!data.total;nav.hidden=data.pages===1;body.replaceChildren();
    for(const row of data.rows){
      const tr=el('tr');for(const value of [row.sample,row.entity,row.partition]){const td=el('td');td.append(el('code',value));tr.append(td)}body.append(tr);
      const traceRow=el('tr'),cell=el('td');cell.colSpan=3;cell.className='row-sources';
      const details=el('details');details.append(el('summary',`Source locations · ${row.occurrences.length} original record${row.occurrences.length===1?'':'s'}`));
      const unique=new Map();for(const ref of row.references||[]){const text=(ref.role==='entity'?'Subject':ref.role==='sample'?'Observation':'Partition')+' · '+sourceLocation(ref);unique.set(text,{text,ref})}
      const refs=[...unique.values()],list=el('ul');for(const {text,ref} of refs.slice(0,20)){
        const item=el('li'),passage=el('details');passage.className='source-passage';passage.append(el('summary',text));let loaded=false;
        passage.addEventListener('toggle',()=>{if(!passage.open||loaded)return;loaded=true;const excerpt=readSource(ref);if(excerpt.error)passage.append(el('p',excerpt.error));else {passage.append(el('pre',excerpt.text));if(excerpt.shortened)passage.append(el('p','Showing the first 4,000 characters. The original file retains the complete record.'));}});
        item.append(passage);list.append(item);
      }details.append(list);
      if(refs.length>20)details.append(el('p',`Showing 20 of ${refs.length} source references. The exported record retains every reference.`));
      cell.append(details);traceRow.append(cell);body.append(traceRow);
    }
  }
  search.addEventListener('input',()=>{page=0;paint()});
  combined.addEventListener('change',()=>{page=0;paint()});filter.addEventListener('change',()=>{page=0;paint()});prev.addEventListener('click',()=>{page--;paint()});next.addEventListener('click',()=>{page++;paint()});paint();
  return {showCombined(){combined.checked=true;filter.value='all';search.value='';page=0;paint();combined.focus()}};
}
