"""Human confirmation is a separate, recorded assumption, never a model tool."""
from copy import deepcopy
from datetime import datetime, timezone
from .primitives import gate, digest

def pending_binding(result):
    verdict=result.get('verdict') or {}
    if verdict.get('category')!='entity_overlap':return None
    decision=gate('entity_overlap',list(result.get('primitive_measurements',{}).values()),verdict.get('citations',[]))
    if decision['verdict']!='clear_pending_confirmation':return None
    binding={**decision['binding'],'claim':result.get('original_claim') or result['claim']}
    return {**binding,'binding_hash':digest(binding)}

def confirm_binding(result, binding_hash):
    binding=pending_binding(result)
    if not binding or binding['binding_hash']!=binding_hash:raise ValueError('Binding changed or no pending entity binding exists. Reload and review.')
    if result.get('binding_confirmation'):raise ValueError('This binding has already been confirmed.')
    updated=deepcopy(result)
    updated['verdict_before_confirmation']=deepcopy(result['verdict'])
    updated['binding_confirmation']={**binding,'confirmed':True,'confirmed_at':datetime.now(timezone.utc).isoformat(),'origin':'human_review'}
    verdict=updated['verdict'];verdict['verdict']='clear'
    verdict['gate']={**verdict['gate'],'verdict':'clear','missing':[],'confirmation_required':True,'binding_hash':binding_hash}
    verdict['missing_evidence']=[x for x in verdict.get('missing_evidence',[]) if x!='human confirmation of the entity binding']
    verdict['limitations']=list(dict.fromkeys(verdict.get('limitations',[])+['Identity semantics are human-confirmed, not independently established by the checker.']))
    return updated
