// Keep the same request identity when a response is lost and the user retries.
// A changed title or record is a different save. No automatic retry is made.
export function createDraftSaver(api, randomId=()=>crypto.randomUUID().replaceAll('-','')) {
 let previous=null,requestId=null;
 return async (title,record)=>{
  const signature=JSON.stringify([title,record]);
  if(signature!==previous){previous=signature;requestId=randomId()}
  return api('/preparations','POST',{title,record,store_inputs:true,request_id:requestId});
 };
}
