from evaluation.run import score


def test_wrong_entity_fails_even_when_overlap_count_matches():
    case={'expected':{'proposal_status':'ready','rule':{'entity_column':'patient'},'result':{'shared_entities':1}}}
    assert score(case,{'status':'ready','rule':{'entity_column':'diagnosis'}},{'shared_entities':1})


def test_missing_coverage_cannot_score_as_clear():
    case={'expected':{'proposal_status':'ready','result':{'status':'incomplete'}}}
    assert score(case,{'status':'ready','rule':{}},{'status':'clear'})


def test_blanket_abstention_fails_answerable_case():
    case={'expected':{'proposal_status':'ready'}}
    assert score(case,{'status':'insufficient'},None)
