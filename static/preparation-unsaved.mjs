import {confirmDiscard} from './preparation-discard.js';
// No inputs are persisted here. Only connected editors can block a page unload.
export function createUnsavedRegistry(target) {
 const entries=new Map();let listening=false;
 const pending=()=>{
  for(const [node,dirty]of entries)if(!node.isConnected)entries.delete(node);
  return [...entries.values()].some(Boolean);
 };
 const unload=event=>{if(pending()){event.preventDefault();event.returnValue=''}};
 function sync(){
  const needed=pending();
  if(needed&&!listening){target.addEventListener('beforeunload',unload);listening=true}
  if(!needed&&listening){target.removeEventListener('beforeunload',unload);listening=false}
 }
 return {track(node){
  return {changed(){entries.set(node,true);sync()},saved(){entries.delete(node);sync()},dispose(){entries.delete(node);sync()}};
 },pending,async requestLeave(confirm){
  if(!pending())return true;
  if(!await confirm())return false;
  entries.clear();sync();return true;
 }};
}
let registry;
export function trackUnsaved(node){
 registry??=createUnsavedRegistry(window);
 return registry.track(node);
}

export function mayLeavePreparation(){
 return registry?registry.requestLeave(confirmDiscard):true;
}
// Cancelling a hash transition preserves the connected editor and its inputs.
export function createPreparationRouteGuard({currentHash,restoreHash,mayLeave}){
 let accepted=currentHash(),sequence=0;
 return async ()=>{
  const version=++sequence,allowed=await mayLeave();
  if(version!==sequence)return false;
  if(!allowed){restoreHash(accepted);return false}
  accepted=currentHash();return true;
 };
}
