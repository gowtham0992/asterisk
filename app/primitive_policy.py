"""V4 ships entity receipts only. Historical acceptance cannot expand this scope."""
def categories(root, today=None):
    # root/today remain compatible with archived callers; neither can re-enable
    # checkpoint or preprocessing checks in the v4 product.
    return ['entity_overlap']
