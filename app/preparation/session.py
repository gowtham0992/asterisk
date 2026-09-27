"""Local review transitions, separate from production and the frozen evaluator."""
import copy
from datetime import datetime,timezone
from .review import prepare,executor


class ReviewSession:
    def __init__(self,spec,files):
        self.spec=copy.deepcopy(spec)
        self.files=copy.deepcopy(files)
        self.review=None
        self.confirmation=None
        self.model_proposal=None

    def preview(self,policies):
        # Even a rejected revision invalidates the previously displayed decision.
        self.review=None
        self.confirmation=None
        self.review=prepare(self.spec,self.files,policies)
        return copy.deepcopy(self.review)

    def confirm(self,review_hash,accepted):
        if self.review is None or review_hash!=self.review['review_hash']:
            raise ValueError('Preview the current policy before confirming')
        if accepted is not True:
            raise ValueError('An explicit confirmation is required')
        if self.confirmation is None:
            self.confirmation={'review_hash':review_hash,
                'statement':'I reviewed the observation identity, repeated-record policy, subject identity, partition mapping and exclusions against the supplied documentation.',
                'actor':'local user action; identity not verified',
                'recorded_at':datetime.now(timezone.utc).isoformat()}
        result={'schema_version':2,'scope':'Experimental local policy review only. No scientific verdict, verified reviewer identity or remote replay.',
                'inputs':copy.deepcopy(self.files),'review':copy.deepcopy(self.review),'confirmation':copy.deepcopy(self.confirmation)}
        if self.model_proposal is not None:
            from .model_record import verify_model_record
            verify_model_record(self.model_proposal,self.spec,self.files)
            result['model_proposal']=copy.deepcopy(self.model_proposal)
        result['record_hash']=executor.sha(executor.canonical(result))
        return result
