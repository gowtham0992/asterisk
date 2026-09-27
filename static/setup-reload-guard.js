// Protect tab-memory-only work on reload/close without blocking hash navigation.
// Browser policy controls whether the native warning is shown after interaction.
export function protectLocalDrafts(target,hasPending){
 const onUnload=event=>{if(!hasPending())return;event.preventDefault();event.returnValue=''};
 target.addEventListener('beforeunload',onUnload);
 return ()=>target.removeEventListener('beforeunload',onUnload);
}
