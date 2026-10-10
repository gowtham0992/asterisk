import {renderLadder} from './ladder-render.mjs?v=quiet-1';
const $=id=>document.getElementById(id);
let started=null,record=null,interval=null,starting=false;
const sha=async text=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text)))].map(x=>x.toString(16).padStart(2,'0')).join('');
$('study-screen').addEventListener('submit',async e=>{
 e.preventDefault();if(started!==null||starting)return;
 if(!$('study-consent').checked)return;
 if($('study-experience').value!=='yes'||$('study-exposure').value!=='no'){
  $('study-status').textContent='This review needs someone with practical held-out evaluation experience who has not seen the receipt. No task has started.';return;
 }
 starting=true;$('study-start').disabled=true;
 const role=$('study-role').value;
 $('study-status').textContent='Loading the receipt. The five-minute timer has not started.';
 try{
  const response=await fetch('/static/ladders/wsibench-report.json');if(!response.ok)throw new Error();
  const text=await response.text(),result=JSON.parse(text);
  const receiptHash=await sha(text);
  renderLadder($('study-receipt'),result);
  $('study-receipt').hidden=false;$('study-answers').hidden=false;$('study-screen').hidden=true;
  started=performance.now();record={schema:'asterisk-comprehension-response/1',participant_id:crypto.randomUUID(),
   receipt_sha256:receiptHash,started_utc:new Date().toISOString(),receipt_kind:'saved public measurement',
   consent:true,experience:role,prior_exposure:false,visibility_changes:[]};
  interval=setInterval(()=>{$('study-status').textContent=Math.floor((performance.now()-started)/1000)>300?
   'Five minutes have elapsed. You can still finish; the extra time will be recorded.':`${Math.floor((performance.now()-started)/1000)} seconds elapsed.`},1000);
 }catch{$('study-status').textContent='Receipt access failed. No task has started. You can try Start reading again or tell the facilitator.'}
 finally{starting=false;$('study-start').disabled=false}
});
document.addEventListener('visibilitychange',()=>{if(record&&started!==null)record.visibility_changes.push({state:document.visibilityState,elapsed_seconds:(performance.now()-started)/1000})});
$('study-answers').addEventListener('submit',e=>{
 e.preventDefault();if(!record||started===null)return;
 clearInterval(interval);record.elapsed_seconds=(performance.now()-started)/1000;record.finished_utc=new Date().toISOString();
 record.answers=Object.fromEntries(['checked','found','unknown','next','assistance'].map(key=>[key,$('answer-'+key).value]));
 record.within_five_minutes=record.elapsed_seconds<=300;record.grading='ungraded; participant authorship and eligibility require facilitator verification';
 const url=URL.createObjectURL(new Blob([JSON.stringify(record,null,2)+'\n'],{type:'application/json'}));
 const a=document.createElement('a');a.href=url;a.download='asterisk-review-'+record.participant_id+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
 $('study-answers').hidden=true;$('study-status').textContent='Answers downloaded. Nothing was submitted. Share the file only if you choose to.';started=null;record=null;
});
$('study-withdraw').addEventListener('click',()=>{clearInterval(interval);record=null;started=null;$('study-screen').reset();$('study-answers').reset();$('study-answers').hidden=true;$('study-receipt').replaceChildren();$('study-receipt').hidden=true;$('study-screen').hidden=false;$('study-status').textContent='Withdrawn. Browser answers cleared; nothing was submitted.'});
