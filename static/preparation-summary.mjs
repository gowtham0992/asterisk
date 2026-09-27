const quote=value=>JSON.stringify(value);
const roles={train:'Training',test:'Evaluation',excluded:'Excluded'};
export function describeIdentity(expression){
 if(!expression)return 'Not recorded';
 if(expression.row)return 'Each source record is a separate observation';
 if(expression.lookup){const l=expression.lookup;return `${quote(l.value_column)} in ${quote(l.file)}, joined on ${quote(l.key_column)} using ${describeIdentity(l.on)}`}
 let text=`Column ${quote(expression.column)}`;
 if(expression.basename)text+=' → filename after the last /';
 if(expression.prefix)text+=` → first ${expression.prefix} characters`;
 return text;
}
export function describePartition(partition){
 return partition?.value?`All records → ${roles[partition.value]||partition.value}`:partition?`Column ${quote(partition.column)}: `+Object.entries(partition.map||{}).map(([value,role])=>`${quote(value)} → ${roles[role]||role}`).join('; '):'Not recorded';
}
export function preparationSummary(data){
 return (data.sources||[]).map(source=>{
  const policy=data.record.policies[source.file]||{},partition=policy.partition||source.partition;
  const membership=describePartition(partition);
  return {file:source.file,citations:policy.evidence||[],rows:[
   ['Observation identity',describeIdentity(policy.sample||source.sample)],
   ['Repeated observations',policy.repeats==='collapse'?'Combine records with the same observation ID':policy.repeats==='distinct'?'Keep distinct observations; repeated IDs block preparation':'Not recorded'],
   ['Subject identity',describeIdentity(policy.entity||source.entity)],
   ['Partition membership',membership],
   ['Supporting source',policy.evidence?.map(c=>`${quote(c.file)}, ${c.start_line===c.end_line?'line '+c.start_line:'lines '+c.start_line+'–'+c.end_line}`).join('; ')||'Not recorded']
  ]};
 });
}
