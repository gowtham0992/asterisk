"""Explicit startup wiring; importing the app never enables preparation spending."""
import os


def configure(app, *, environ=None, factory=None):
    environ = os.environ if environ is None else environ
    enabled = environ.get('ASTERISK_PREPARATION_NEBIUS', '0')
    if enabled not in ('0', '1'):
        raise RuntimeError('ASTERISK_PREPARATION_NEBIUS must be 0 or 1')
    if enabled == '0':
        return  # Preserve explicitly injected developer/test providers.
    if factory is None:
        from .provider import configured
        factory = configured
    try:
        provider = factory()
    except Exception:
        raise RuntimeError(
            'Native preparation cannot start: check the Nebius credential, '
            'explicit preparation budget, or existing research ledger and cost baseline. '
            'No preparation upload was made.'
        ) from None
    app.state.preparation_complete = provider
