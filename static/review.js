(() => {
 const form=document.getElementById('review-form'),start=document.getElementById('start'),pause=document.getElementById('pause'),timer=document.getElementById('timer'),status=document.getElementById('review-status');
 let startedAt=null,runningSince=null,activeMs=0,finished=false;
 const active=()=>activeMs+(runningSince===null?0:performance.now()-runningSince);
 const paint=()=>{timer.textContent=startedAt?Math.floor(active()/1000)+' active seconds · '+(finished?'finished':runningSince===null?'paused':'running'):'Not started'};
 start.addEventListener('click',()=>{if(startedAt)return;startedAt=new Date().toISOString();runningSince=performance.now();start.disabled=true;pause.disabled=false;paint()});
 pause.addEventListener('click',()=>{if(finished)return;if(runningSince!==null){activeMs+=performance.now()-runningSince;runningSince=null;pause.textContent='Resume'}else{runningSince=performance.now();pause.textContent='Pause'}paint()});
 setInterval(paint,1000);
 form.addEventListener('submit',event=>{event.preventDefault();if(!startedAt){status.textContent='Start the review timer before committing notes.';return}if(finished)return;
  activeMs=active();runningSince=null;finished=true;pause.disabled=true;form.querySelector('[type=submit]').disabled=true;
  const values=Object.fromEntries(new FormData(form));const committed=new Date().toISOString();
  const note={schema_version:1,...values,independent:values.independent==='yes',consent:values.consent==='yes',labels_unseen:values.labels_unseen==='yes',started_at:startedAt,committed_at:committed,active_seconds:Math.round(activeMs/1000),wall_seconds:Math.round((Date.parse(committed)-Date.parse(startedAt))/1000),receipt_reference:document.body.dataset.receiptReference||null,status:'recorded_self_report',limitation:'Self-reported notes and local timer; actor identity and independence are not authenticated. No expected labels or automatic pass assessment.'};
  const url=URL.createObjectURL(new Blob([JSON.stringify(note,null,2)],{type:'application/json'})),link=document.createElement('a');link.href=url;link.download='asterisk-review-notes.json';link.textContent='Download notes again';status.replaceChildren('Notes committed locally. ',link);link.click();form.querySelectorAll('input,select,textarea').forEach(field=>field.disabled=true);paint();
 });
 window.addEventListener('beforeunload',event=>{if(startedAt&&!finished){event.preventDefault();event.returnValue=''}});
})();
