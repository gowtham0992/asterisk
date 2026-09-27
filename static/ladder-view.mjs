// Pure view model for an independence ladder result. No DOM, no network: tested in node.
export const FINDINGS={
 violation:{tone:'shared',title:'Not held out'},
 held_out:{tone:'held',title:'Held out'},
 held_out_pending_confirmation:{tone:'held',title:'Held out, pending your confirmation'},
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
 if(unmapped)row.notes.push(`${plural(unmapped,'selected row')} had no ${level.name} value and were left unmapped.`);
 if(level.one_unit_per_sample)row.notes.push(`Every sample has its own ${level.name}. Confirm this column really names a ${level.name}.`);
 if(level.nests_previous?.violations)row.notes.push(`${plural(level.nests_previous.violations,'finer unit')} map to more than one ${level.name}; the levels do not nest.`);
 if(level.kind==='attribute')return {...row,tone:'attribute',state:shared?'In both partitions':'Only in one partition',notes:[...row.notes,'An attribute describes samples; sharing it is expected and is not a leak.']};
 if(shared)return {...row,tone:'shared',state:'Shared'};
 if(level.disjoint_namespaces)return {...row,tone:'unknown',state:'Not comparable',notes:[...row.notes,`Training and evaluation identifiers use different naming families (${level.disjoint_namespaces.train_tokens.join(', ')} vs ${level.disjoint_namespaces.test_tokens.join(', ')}).`]};
 if(unmapped)return {...row,tone:'unknown',state:'Incomplete'};
 return {...row,tone:'held',state:'Held out'};
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
 const byName=new Map(picked.map(f=>[f.name,f]));
 const files=[],missing=[],ambiguous=[];
 for(const name of referencedFiles(spec)){
  const base=name.split('/').pop();
  const hit=byName.get(name)||byName.get(base);
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

export const isDocumentation=name=>/\.(md|txt|rst)$/i.test(name);

// Column names of a table the person chose, read locally so they can decide which example values may be shared.
export function tableColumns(name,text){
 if(/\.json$/i.test(name)){try{const rows=JSON.parse(text);return Array.isArray(rows)&&rows[0]&&typeof rows[0]==='object'?Object.keys(rows[0]):[]}catch{return []}}
 if(/\.csv$/i.test(name)){const header=(text.split(/\r?\n/,1)[0]||'');return header?header.split(',').map(c=>c.replace(/^"|"$/g,'')):[]}
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
  levels:result.levels.map(l=>({name:l.name,kind:l.kind,status:l.status,shared:l.shared??null,test_units:l.test_units??null})),
  replay:replay?replay.provenance:null,scope:result.scope};
}

// ---- Guided ladder builder: the person defines the unit when Nemotron abstains. Mirrors the engine's grammar. ----
export const formatOf=name=>/\.json$/i.test(name)?'json':/\.csv$/i.test(name)?'csv':'lines';

export function tableRows(name,text){
 const fmt=formatOf(name);
 if(fmt==='json'){try{const rows=JSON.parse(text);return Array.isArray(rows)?rows.filter(r=>r&&typeof r==='object'):[]}catch{return []}}
 if(fmt==='lines')return text.split('\n').filter(Boolean).map(value=>({value}));
 const lines=text.split(/\r?\n/).filter(Boolean),header=(lines.shift()||'').split(',');
 return lines.map(line=>{const cells=line.split(',');return Object.fromEntries(header.map((h,i)=>[h,cells[i]??'']))});
}

// Same order and rules as app/ladder.py: basename, field, characters or prefix. null = the level would be unavailable.
export function deriveValue(value,{basename=false,field=null,characters=null,prefix=0}={}){
 if(value===undefined||value===null||value==='')return null;
 let text=String(value);
 if(basename)text=text.slice(text.lastIndexOf('/')+1);
 if(field&&field.separator){const from=Number(field.from)||1,to=Number(field.to)||from,parts=text.split(field.separator);if(parts.length<to||to<from)return null;text=parts.slice(from-1,to).join(field.separator)}
 if(characters&&Number(characters.from)){const from=Number(characters.from),to=Number(characters.to)||from;if(text.length<to||to<from)return null;text=text.slice(from-1,to)}
 else if(prefix){if(text.length<prefix)return null;text=text.slice(0,prefix)}
 return text;
}

const SPLIT_WORDS={train:'train',training:'train',learn:'train',learning:'train',dev:'excluded',val:'excluded',valid:'excluded',validation:'excluded',test:'test',testing:'test',eval:'test',evaluation:'test'};
export function guessPartition(raw){return SPLIT_WORDS[String(raw).trim().toLowerCase()]||'excluded'}
export const splitColumn=columns=>columns.find(c=>/(^|_)(split|fold|partition|subset|set)(_|$)/i.test(c))||null;

export function buildSpec({claim,unitName,sources,unit,citation}){
 const name=(unitName||'').trim().toLowerCase().replace(/[^a-z0-9_]+/g,'_').replace(/^_+|_+$/g,'')||'unit';
 const expression=unit.lookup?{lookup:{file:unit.lookup.file,format:formatOf(unit.lookup.file),key_column:unit.lookup.key,value_column:unit.lookup.value,on:{column:unit.column}}}
  :{column:unit.column,...(unit.basename?{basename:true}:{}),
   ...(unit.field&&unit.field.separator?{field:{separator:unit.field.separator,from:Number(unit.field.from)||1,...(Number(unit.field.to)>(Number(unit.field.from)||1)?{to:Number(unit.field.to)}:{})}}:{}),
   ...(unit.characters&&Number(unit.characters.from)?{characters:{from:Number(unit.characters.from),to:Number(unit.characters.to)||Number(unit.characters.from)}}:unit.prefix?{prefix:Number(unit.prefix)}:{})};
 const sampleColumn=sources[0].sample.column;
 const levels=[];
 if(sampleColumn&&sources.every(s=>s.sample.column===sampleColumn)&&name!=='record')levels.push({name:name==='observation'?'sample':'observation',kind:'observation',expression:{column:sampleColumn}});
 levels.push({name,kind:'unit',expression,...(unit.meaning?{meaning:unit.meaning.slice(0,400)}:{})});
 if(levels.length<2)levels.unshift({name:'row',kind:'observation',expression:{column:sampleColumn}});
 return {schema:'asterisk-ladder/1',claim:{text:claim,level:name},
  sources:sources.map(s=>({file:s.file,format:formatOf(s.file),sample:s.sample,partition:s.partition})),
  levels,citations:[{file:citation.file,start_line:Number(citation.start),end_line:Number(citation.end)}]};
}

// Number of lines a citation can reach: a final newline does not start another line.
export const lineCount=text=>{const t=String(text||'');return t?t.replace(/\n$/,'').split('\n').length:0};
