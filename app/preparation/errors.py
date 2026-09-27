"""Public preparation failure types, independent of provider SDKs."""
BLOCKED_MESSAGE = (
    'The request was blocked before contacting Nebius. No model call was made. '
    'Check the existing budget and provider configuration before creating another preview.'
)


class BeforeDispatchBlocked(RuntimeError):
    def __init__(self):
        super().__init__(BLOCKED_MESSAGE)


class ProposalRejected(ValueError):
    """A completion arrived, but local parsing or extraction refused it."""
    def __init__(self):
        super().__init__('The model returned a proposal that the local checker could not execute. No extraction was accepted. Review the source documentation or use the supported manual CSV setup; no automatic retry was made.')
