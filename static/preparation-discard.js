let active=null;
export function confirmDiscard(){
 if(active)return active;
 const previous=document.activeElement;
 active=new Promise(resolve=>{
  const dialog=document.createElement('dialog');dialog.className='preparation-discard-dialog';
  dialog.setAttribute('aria-labelledby','discard-preparation-title');dialog.setAttribute('aria-describedby','discard-preparation-description');
  const label=document.createElement('p');label.className='eyebrow';label.textContent='Unsaved preparation';
  const title=document.createElement('h2');title.id='discard-preparation-title';title.textContent='Keep your preparation work?';
  const text=document.createElement('p');text.id='discard-preparation-description';text.textContent='Your current preparation work has not been saved as a draft. Leaving can lose selected files, typed details or reviewed choices. Keep editing to preserve this page, or discard changes to continue. Any previously saved draft stays unchanged.';
  const actions=document.createElement('div');actions.className='actions';
  const keep=document.createElement('button');keep.type='button';keep.className='primary';keep.textContent='Keep editing';keep.autofocus=true;
  const discard=document.createElement('button');discard.type='button';discard.className='secondary';discard.textContent='Discard changes';
  let settled=false;
  const finish=value=>{if(settled)return;settled=true;dialog.close();dialog.remove();active=null;if(!value&&previous?.isConnected)previous.focus();resolve(value)};
  keep.addEventListener('click',()=>finish(false));discard.addEventListener('click',()=>finish(true));
  dialog.addEventListener('cancel',event=>{event.preventDefault();finish(false)});
  actions.append(keep,discard);dialog.append(label,title,text,actions);document.body.append(dialog);dialog.showModal();keep.focus();
 });
 return active;
}
