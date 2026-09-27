// Educational example only. No user files, remote inference or scientific verdict.
const records=[{sample:'sample_014',specimen:'specimen_07'},{sample:'sample_209',specimen:'specimen_07'}];
const select=document.querySelector('#illustration-identity');
if(select){
 function render(){
  const key=select.value==='sample'?'sample':'specimen';
  const shared=Number(records[0][key]===records[1][key]);
  document.querySelector('#illustration-match').textContent=shared+' shared '+key+' ID'+(shared===1?'':'s');
  document.querySelector('#illustration-detail').textContent=key==='sample'?'Different sample IDs do not establish separate specimens.':'sample_014 and sample_209 both map to specimen_07.';
  document.querySelector('.split-illustration').dataset.identity=key;
 }
 select.disabled=false;select.addEventListener('change',render);render();
}
