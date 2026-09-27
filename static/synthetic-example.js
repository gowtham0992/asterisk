// Instructional fixture only. Never supplies a measurement or a receipt verdict.
const rows=[{sample:'a',partition:'train',subject:'S1'},{sample:'b',partition:'test',subject:'S1'},{sample:'c',partition:'test',subject:'S2'}];
export function specimenExample(){
 return {walkthrough:'specimen-v1',saved_binding:{split_file:'splits.csv',mapping_file:'entities.csv',sample_column:'sample',mapping_sample_column:'sample',partition_column:'partition',entity_column:'subject_id',train_values:['train'],test_values:['test']},title:'Shared specimens',evaluation_intent:{target:'unseen_entities',unit:'specimens'},claim:'Evaluation specimens must be absent from training.',model:'super',files:[
  {name:'splits.csv',content:'sample,partition\n'+rows.map(r=>r.sample+','+r.partition).join('\n')+'\n'},
  {name:'entities.csv',content:'sample,subject_id\n'+rows.map(r=>r.sample+','+r.subject).join('\n')+'\n'},
  {name:'README.md',content:'subject_id identifies the physical specimen. Evaluation specimens must be absent from training. Original synthetic demonstration.\n'}]};
}
export function syntheticExample({el,btn,onStart}){
 const body=el('div',{class:'example-explanation'});
 const root=el('details',{class:'synthetic-explainer'},el('summary',{},el('span',{class:'eyebrow'},'UNDERSTAND THE CHECK'),el('strong',{},'Three samples. One shared specimen.'),el('span',{},'Explore the example →')),body);
 let initialized=false;
 root.addEventListener('toggle',()=>{
  if(!root.open)return;if(initialized){root.scrollIntoView({block:'start'});return}initialized=true;
  body.append(el('p',{class:'example-context'},'A study wants to evaluate specimens it has never trained on. These are all three rows in this synthetic example.'),
   el('div',{class:'example-source-table'},el('table',{},el('caption',{},'Split and identity files joined by sample ID'),el('thead',{},el('tr',{},...['Sample','Partition','Specimen'].map(t=>el('th',{scope:'col'},t)))),el('tbody',{},...rows.map(r=>el('tr',{},el('th',{scope:'row'},el('code',{},r.sample)),el('td',{},r.partition==='train'?'Training':'Evaluation'),el('td',{},el('code',{class:r.subject==='S1'?'example-shared':''},r.subject))))))),
   el('div',{class:'example-lesson'},el('span',{class:'eyebrow'},'FOLLOW THE IDENTITY'),el('h3',{},'Different samples. The same specimen.'),el('p',{},'Sample a is in training. Sample b is in evaluation. Both come from S1, so S1 is not unseen at evaluation time. Sample c comes from a different specimen, S2.')),
   el('p',{class:'hint'},'The README defines subject_id as the physical specimen. Without that definition, matching IDs would not establish what they represent.'),
   el('details',{class:'example-originals'},el('summary',{},'Read the three original files'),...specimenExample().files.map(f=>el('section',{},el('h4',{},f.name),el('pre',{tabindex:'0'},f.content)))),
   el('div',{class:'example-next'},el('p',{},'This illustration is not a saved check or a Sandbox result. To inspect the full workflow, use these files and review the columns yourself.'),btn('Use these example files',()=>onStart(specimenExample()),'secondary')),
   el('p',{class:'example-scope'},'Synthetic teaching example · Opening it saves nothing and makes no model call.'));
  root.scrollIntoView({block:'start'});
 });
 return root;
}
