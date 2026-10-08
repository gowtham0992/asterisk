import {inspectCSV} from './csv-projection.mjs';
// Pure view model for an independence ladder result. No DOM, no network: tested in node.
export const FINDINGS={
 violation:{tone:'shared',title:'Not held out'},
 held_out:{tone:'held',title:'Held out'},
 held_out_pending_confirmation:{tone:'held',title:'No shared values, pending your confirmation'},
 not_established:{tone:'unknown',title:'Not established'},
 insufficient:{tone:'unknown',title:'Insufficient evidence'},
};
const plural=(n,word)=>`${n.toLocaleString('en-US')} ${word}${n===1?'':'s'}`;

export function levelRow(level,claimLevel){
 const base={name:level.name,kind:level.kind,meaning:level.meaning||'',isClaim:level.name===claimLevel,witnesses:level.witnesses||[],notes:[]};
 if(level.status!=='measured')return {...base,tone:'unknown',state:'Unavailable',percent:null,detail:level.reason||'This level could not be derived.'};
 const {shared,test_units:units,affected_test_rows:affected,test_rows:rows,unmapped_rows:unmapped}=level;
 const percent=level.test_units_seen_in_train_percent;
 const detail=`${plural(shared,'evaluation '+level.name)} of ${units.toLocaleString('en-US')} also in training · ${affected.toLocaleString('en-US')} of ${rows.toLocaleString('en-US')} evaluation rows affected`;
 const row={...base,percent,detail};
 if(level.kind==='unit'&&level.evaluation_unit_ratio>=.95)row.notes.push('Nearly every evaluation row has its own unit value. Check that this is not a per-sample identifier.');
 if(!shared&&level.folded_shared_units)row.notes.push(`${level.folded_shared_units} shared values when ignoring case and surrounding whitespace. Review their meaning; exact matching is unchanged.`);
 if(unmapped)row.notes.push(`${plural(unmapped,'selected row')} had no ${level.name} value and were left unmapped.`);
 if(level.one_unit_per_sample)row.notes.push(`Every sample has its own ${level.name}. Confirm this column really names a ${level.name}.`);
 if(level.nests_previous?.violations)row.notes.push(`${plural(level.nests_previous.violations,'finer unit')} map to more than one ${level.name}; the levels do not nest.`);
 if(level.kind==='attribute')return {...row,tone:'attribute',state:shared?'In both partitions':'Only in one partition',notes:[...row.notes,'An attribute describes samples; sharing it is expected and is not a leak.']};
 if(shared)return {...row,tone:'shared',state:'Shared'};
 if(level.disjoint_namespaces)return {...row,tone:'unknown',state:'Not comparable',notes:[...row.notes,`Training and evaluation identifiers use different naming families (${level.disjoint_namespaces.train_tokens.join(', ')} vs ${level.disjoint_namespaces.test_tokens.join(', ')}).`]};
 if(unmapped)return {...row,tone:'unknown',state:'Incomplete'};
 return {...row,tone:'held',state:'No shared values'};
}

export function ladderView(result){
 const claimLevel=result.finding.level;
 const finding=FINDINGS[result.finding.status]||{tone:'unknown',title:result.finding.status};
 const population=result.population||{};
 return {
  claim:result.claim.text,claimLevel,
  finding:{...finding,status:result.finding.status,reason:result.finding.reason,warning:result.finding.warning||''},
  headline:result.headline,
  rows:result.levels.map(level=>levelRow(level,claimLevel)),
  population:`${(population.train||0).toLocaleString('en-US')} training · ${(population.test||0).toLocaleString('en-US')} evaluation · ${(population.excluded||0).toLocaleString('en-US')} excluded rows`,
  agreements:(result.agreements||[]).map(a=>a.disagreements===null?`${a.levels.join(' and ')}: not compared, one level is unavailable`:a.disagreements?`${a.levels.join(' and ')} disagree on ${plural(a.disagreements,'sample')}`:`${a.levels.join(' and ')} agree on every sample`),
  scope:result.scope||'',specHash:result.spec_hash||'',inputs:Object.entries(result.input_hashes||{}),
 };
}

// Files a spec reads: observation sources, lookup tables anywhere in an expression, and cited documentation.
export function referencedFiles(spec){
 const names=new Set();
 const walk=expr=>{if(!expr||typeof expr!=='object')return;if(expr.lookup){names.add(expr.lookup.file);walk(expr.lookup.on)}};
 for(const source of spec?.sources||[]){if(source.file)names.add(source.file);walk(source.sample)}
 for(const level of spec?.levels||[]){walk(level.expression);for(const expr of Object.values(level.by_source||{}))walk(expr)}
 for(const citation of spec?.citations||[])if(citation.file)names.add(citation.file);
 return [...names];
}

// Match chosen files to the names a spec expects; a spec may name "dir/file.csv" and the person picks "file.csv".
export function matchFiles(spec,picked){
 const byName=new Map(),duplicates=new Set();
 for(const file of picked){if(byName.has(file.name))duplicates.add(file.name);else byName.set(file.name,file)}
 const files=[],missing=[],ambiguous=[];
 for(const name of referencedFiles(spec)){
  const base=name.split('/').pop();
  const selectedName=byName.has(name)?name:base;
  if(duplicates.has(selectedName)){ambiguous.push(name);continue}
  const hit=byName.get(selectedName);
  if(!hit){missing.push(name);continue}
  files.push({name,file:hit});
 }
 const used=new Map();for(const {name,file} of files){if(used.has(file)&&used.get(file)!==name)ambiguous.push(name);used.set(file,name)}
 return {files,missing,ambiguous};
}

// A person may confirm the claim level's meaning when that is the only thing standing between the data and "held out".
export function confirmable(result){
 const f=result.finding,row=(result.levels||[]).find(l=>l.name===f.level);
 if((result.confirmed_levels||[]).includes(f.level)||!row||row.kind==='observation')return null;
 const onlyMeaning=f.confirmable===true;
 return onlyMeaning?{level:f.level,meaning:row.meaning||'',perSample:!!row.one_unit_per_sample}:null;
}

// A role suggestion only: never grants example-value sharing or confirms an identity.
export function isDocumentation(name,text=''){
 if(/\.(md|rst)$/i.test(name))return true;
 if(!/\.txt$/i.test(name))return false;
 const lines=text.trim().split(/\r?\n/).filter(line=>line.trim());
 // Require every nonempty line to be a filename, optionally followed by a numeric label.
 // Plain identifiers and mixed prose remain documentation until the person changes the role.
 const filename=/^[^\s]+\.[a-z0-9]{1,10}(?:[ \t]+[0-9]+)?$/i;
 return !(lines.length>0&&lines.every(line=>filename.test(line.trim())));
}

// Column names of a table the person chose, read locally so they can decide which example values may be shared.
export function tableColumns(name,text){
 if(/\.json$/i.test(name)){try{const rows=JSON.parse(text);return Array.isArray(rows)&&rows[0]&&typeof rows[0]==='object'?Object.keys(rows[0]):[]}catch{return []}}
 if(/\.csv$/i.test(name)){try{return inspectCSV(text).headers}catch{return []}}
 return ['value'];
}

// Plain-English reading of an extraction expression, so a person can check what each level means.
export function describeExpression(expr){
 if(!expr||typeof expr!=='object')return 'unreadable expression';
 if(expr.row)return 'each source row';
 if(expr.lookup){const q=expr.lookup;return `"${q.value_column}" from ${q.file}, matched on "${q.key_column}" = ${describeExpression(q.on)}`}
 let text=`column "${expr.column}"`;
 if(expr.basename)text+=', file name after the last /';
 if(expr.field){const f=expr.field,to=f.to??f.from;text+=to>f.from?`, fields ${f.from}–${to} split on "${f.separator}"`:`, field ${f.from} split on "${f.separator}"`}
 if(expr.characters){const c=expr.characters,to=c.to??c.from;text+=to>c.from?`, characters ${c.from}–${to}`:`, character ${c.from}`}
 if(expr.prefix)text+=`, first ${expr.prefix} characters`;
 return text;
}

// Documentation lines a proposal cites, quoted from the person's own files.
export function citedLines(citations,files){
 return (citations||[]).map(c=>{const lines=(files[c.file]||'').split('\n');return {file:c.file,start:c.start_line,end:c.end_line,text:lines.slice(c.start_line-1,c.end_line).join('\n')}});
}

// A portable record of one chain: proposal, spec, measurement, confirmation and replay. Hashes, not file contents.
export function receipt({claim,proposal,spec,result,replay,createdAt}){
 return {schema:'asterisk-ladder-receipt/1',created_at:createdAt,claim,
  proposal:proposal?{defined_by:proposal.defined_by||(proposal.proposal?.status==='abstain'?'person':'model'),provider:proposal.provider,model:proposal.model,payload_sha256:proposal.payload_sha256,attempts:proposal.attempts.length,repaired:proposal.attempts.length>1,total_tokens:proposal.total_tokens}:null,
  spec,finding:result.finding,headline:result.headline,confirmed_levels:result.confirmed_levels||[],spec_hash:result.spec_hash,input_hashes:result.input_hashes,
  result,levels:result.levels,
  replay:replay?replay.provenance:null,scope:result.scope};
}

// ---- Guided ladder builder: the person defines the unit when Nemotron abstains. Mirrors the engine's grammar. ----
export const formatOf=name=>/\.json$/i.test(name)?'json':/\.csv$/i.test(name)?'csv':'lines';

export function tableRows(name,text){
 const fmt=formatOf(name);
 if(fmt==='json'){try{const rows=JSON.parse(text);return Array.isArray(rows)?rows.filter(r=>r&&typeof r==='object'):[]}catch{return []}}
 if(fmt==='lines')return text.split('\n').filter(Boolean).map(value=>({value}));
 const table=inspectCSV(text);
 const decode=value=>value.startsWith('"')?value.slice(1,-1).replaceAll('""','"'):value;
 return table.rows.slice(1).map(row=>Object.fromEntries(table.headers.map((h,i)=>[h,decode(row.fields[i])])));

}

// Same order and rules as app/ladder.py: basename, field, characters or prefix. null = the level would be unavailable.
export function deriveValue(value,{basename=false,field=null,characters=null,prefix=0}={}){
 if(value===undefined||value===null||value==='')return null;
 let text=String(value);
 if(basename)text=text.slice(text.lastIndexOf('/')+1);
 if(field&&field.separator){const from=Number(field.from)||1,to=Number(field.to)||from,parts=text.split(field.separator);if(parts.length<to||to<from)return null;text=parts.slice(from-1,to).join(field.separator)}
 const chars=Array.from(text);
 if(characters&&Number(characters.from)){const from=Number(characters.from),to=Number(characters.to)||from;if(chars.length<to||to<from)return null;text=chars.slice(from-1,to).join('')}
 else if(prefix){if(chars.length<prefix)return null;text=chars.slice(0,prefix).join('')}
 return text;
}

const SPLIT_WORDS={train:'train',training:'train',learn:'train',learning:'train',dev:'excluded',val:'excluded',valid:'excluded',validation:'excluded',test:'test',testing:'test',eval:'test',evaluation:'test'};
export function guessPartition(raw){return SPLIT_WORDS[String(raw).trim().toLowerCase()]||'excluded'}
export const splitColumn=columns=>columns.find(c=>/(^|_)(split|fold|partition|subset|set)(_|$)/i.test(c))||null;

export function buildSpec({claim,unitName,sources,unit,citation}){
 const name=(unitName||'').trim().toLowerCase().replace(/[^a-z0-9_]+/g,'_').replace(/^_+|_+$/g,'')||'unit';
 const derived={column:unit.column,...(unit.basename?{basename:true}:{}),
   ...(unit.field&&unit.field.separator?{field:{separator:unit.field.separator,from:Number(unit.field.from)||1,...(Number(unit.field.to)>(Number(unit.field.from)||1)?{to:Number(unit.field.to)}:{})}}:{}),
   ...(unit.characters&&Number(unit.characters.from)?{characters:{from:Number(unit.characters.from),to:Number(unit.characters.to)||Number(unit.characters.from)}}:unit.prefix?{prefix:Number(unit.prefix)}:{})};
 const expression=unit.lookup?{lookup:{file:unit.lookup.file,format:formatOf(unit.lookup.file),key_column:unit.lookup.key,value_column:unit.lookup.value,on:derived}}:derived;
 if(!sources.length)throw Error('Choose at least one table of observations.');
 const sample=sources[0].sample;
 const overrides=Object.fromEntries(sources.slice(1).filter(s=>JSON.stringify(s.sample)!==JSON.stringify(sample)).map(s=>[s.file,s.sample]));
 const levels=[{name:name==='observation'?'sample':'observation',kind:'observation',expression:sample,...(Object.keys(overrides).length?{by_source:overrides}:{})}];
 levels.push({name,kind:'unit',expression,...(unit.meaning?{meaning:unit.meaning.slice(0,400)}:{})});

 return {schema:'asterisk-ladder/1',claim:{text:claim,level:name},
  sources:sources.map(s=>({file:s.file,format:formatOf(s.file),sample:s.sample,partition:s.partition})),
  levels,citations:[{file:citation.file,start_line:Number(citation.start),end_line:Number(citation.end)}]};
}

// Number of lines a citation can reach: a final newline does not start another line.
export const lineCount=text=>{const t=String(text||'');return t?t.replace(/\n$/,'').split('\n').length:0};

// Validate the whole selection before reading, and return it atomically.
export async function readSelectedFiles(files){
 const names=new Set();let bytes=0;
 for(const file of files){
  if(names.has(file.name))throw Error(`Two files are named ${file.name}. Rename one before choosing them.`);
  names.add(file.name);bytes+=file.size;
  if(file.size>16_000_000||bytes>16_000_000)throw Error('Choose at most 16 MB of files in total.');
 }
 return Object.fromEntries(await Promise.all(files.map(async file=>[file.name,await file.text()])));
}

export function partitionLabels(rows,column){
 const counts=new Map();
 for(const row of rows){if(!(column in row))throw Error(`Partition column "${column}" is missing from a row.`);const raw=String(row[column]);counts.set(raw,(counts.get(raw)||0)+1)}
 if(counts.size>12)throw Error('The guided builder supports at most 12 partition labels. Choose another partition column or use an explicit JSON specification.');
 return [...counts].map(([raw,count])=>({raw,count}));
}


// Read a two-level definition into the guided editor only when every rule can round-trip.
// Complex definitions remain available in the complete JSON editor, never flattened.
export function bindingSeed(spec){
 if(!spec)return null;
 const level=spec.levels?.find(l=>l.name===spec.claim?.level);
 const observations=spec.levels?.filter(l=>l.kind==='observation')||[];
 if(spec.levels?.length!==2||observations.length!==1||level?.kind!=='unit'||level.by_source)return null;
 const expr=level.expression,derived=expr?.lookup?.on||expr;
 const allowed=['column','basename','prefix','field','characters'];
 if(!derived?.column||Object.keys(derived).some(k=>!allowed.includes(k)))return null;
 if(expr.lookup&&Object.keys(expr).some(k=>k!=='lookup'))return null;
 if(spec.sources.some(s=>!s.sample?.column||Object.keys(s.sample).length!==1||s.filter||s.deduplicate))return null;
 const observation=observations[0];
 if(spec.sources.some(s=>JSON.stringify(observation.by_source?.[s.file]||observation.expression)!==JSON.stringify(s.sample)))return null;
 return {name:level.name,meaning:level.meaning||'',unit:{...derived,
  ...(expr.lookup?{lookup:{file:expr.lookup.file,key:expr.lookup.key_column,value:expr.lookup.value_column}}:{})},
  sources:spec.sources,citation:spec.citations?.[0]||null};
}

export function preserveBinding(original,next){
 if(!original)return next;
 if(!bindingSeed(original))throw Error('Use the complete definition editor for this specification.');
 const observation=original.levels.find(l=>l.kind==='observation');
 const unit=original.levels.find(l=>l.name===original.claim.level);
 const freshObservation=next.levels.find(l=>l.kind==='observation');
 const freshUnit=next.levels.find(l=>l.name===next.claim.level);
 const citations=[...(original.citations||[]),...next.citations].filter((c,i,a)=>a.findIndex(x=>JSON.stringify(x)===JSON.stringify(c))===i);
 return {...original,claim:{...original.claim,...next.claim},sources:next.sources,
  ...(original.agreements?{agreements:original.agreements.map(pair=>pair.map(name=>name===unit.name?freshUnit.name:name))}:{}),
  levels:original.levels.map(l=>l===observation?{...l,expression:freshObservation.expression,by_source:freshObservation.by_source||{}}:
   l===unit?{...l,...freshUnit,meaning:freshUnit.meaning||''}:l),citations};
}

export function bindingQuestions(spec){
 const level=spec.levels.find(l=>l.name===spec.claim.level);
 return [
  {question:'What does one row represent?',answers:spec.sources.map(s=>`${s.file}: one recorded observation, identified by ${describeExpression(s.sample)}.`)},
  {question:'What identifies the subject that must be unseen?',answers:[`The claim requires unseen ${level.name} values. Their identifier is ${level.expression.lookup?`column "${level.expression.lookup.value_column}" in ${level.expression.lookup.file}`:describeExpression(level.expression)}.`,...(level.meaning?[`Proposer’s description (unverified): ${level.meaning}`]:[])]},
  {question:'How is that subject linked to each row?',answers:spec.sources.map(s=>`${s.file}: ${describeExpression(level.by_source?.[s.file]||level.expression)}.`)}
 ];
}

// A preview cannot choose among conflicting lookup rows; only the server measures.
export function bindingPreview(sources,unit,rows){
 let lookup=null;
 if(unit.lookup){
  lookup=new Map();
  for(const row of rows[unit.lookup.file]||[]){
   const key=row[unit.lookup.key],value=row[unit.lookup.value];
   if(key===undefined||key===null||key==='')continue;
   const k=String(key),v=value===undefined||value===null||value===''?null:String(value);
   lookup.set(k,lookup.has(k)&&lookup.get(k)!==v?null:v);
  }
 }
 return sources.map(file=>{
  const values=(rows[file]||[]).map(row=>{const raw=row[unit.column],derived=deriveValue(raw,unit);return {raw:String(raw??''),value:lookup?(lookup.get(derived)??null):derived}});
  return {file,rows:values.length,distinct:new Set(values.map(r=>r.value).filter(v=>v!==null)).size,unmapped:values.filter(r=>r.value===null).length,examples:values.slice(0,6)};
 });
}
