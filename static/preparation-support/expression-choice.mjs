// Build only the existing executor's closed column expression language.
export function columnExpression(column, basename, prefix) {
  if (typeof column !== 'string' || !column) throw new Error('Choose a source column.');
  if (typeof basename !== 'boolean') throw new Error('Choose a filename policy.');
  const value = {column};
  if (basename) value.basename = true;
  if (prefix !== '') {
    if (typeof prefix !== 'string' || !/^[0-9]+$/.test(prefix)) throw new Error('Prefix length must be a whole number from 1 to 128.');
    const length = Number(prefix);
    if (!Number.isSafeInteger(length) || length < 1 || length > 128) throw new Error('Prefix length must be a whole number from 1 to 128.');
    value.prefix = length;
  }
  return value;
}

export function lookupExpression(file,key,value,on,tables){
 const table=tables.find(t=>t.file===file);
 if(!table||!table.columns.includes(key)||!table.columns.includes(value))throw new Error('Choose the lookup table and both matching columns.');
 if(!on||on.lookup)throw new Error('Choose a direct source key; nested lookups are unsupported.');
 return {lookup:{file,format:table.format,key_column:key,value_column:value,on}};
}

// Illustrative only: full validation and lineage remain server-owned.
export function identityExamples(expression, source) {
  if (expression.lookup) return {unavailable:'Lookup IDs are evaluated in the full policy preview.', rows:[]};
  return {rows:(source.examples || []).map(example => {
    const input = expression.row ? `${source.file}@${example.record_number}` : example.row[expression.column];
    const result = {reference:example.reference, input};
    try {
      const text = value => {
        if (typeof value !== 'string' || !value || Array.from(value).length > 4096 || value.includes('\0')) throw new Error('Not a valid text identifier');
        return value;
      };
      let value = text(input);
      if (!expression.row && expression.basename) value = text(value.split('/').at(-1));
      if (!expression.row && expression.prefix !== undefined) {
        const chars = Array.from(value), length = expression.prefix;
        if (!Number.isInteger(length) || length < 1 || length > 128 || chars.length < length) throw new Error('Prefix exceeds this identifier or is invalid');
        value = chars.slice(0,length).join('');
      }
      return {...result,value};
    } catch(error) { return {...result,error:error.message}; }
  })};
}
