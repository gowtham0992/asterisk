"""Regression coverage for bound, cross-file checkpoint source chains."""
from app.checkpoint import symbol_chain

MAIN = '''from helper import Keeper, assess
training, validation, heldout = load_sets()
model = Network()
keeper = Keeper("weights.bin")
for epoch in range(5):
    train(model, training)
    score = assess(model, validation)
    keeper.consider(score, model)
keeper.restore(model)
answer = assess(model, heldout)
'''
HELPER = '''import torch
class Keeper:
    def __init__(self, filename):
        self.filename = filename
        self.best = None
    def consider(self, score, candidate):
        if self.best is None:
            self.best = score
            self.persist(candidate)
        elif score < self.best:
            self.best = score
            self.persist(candidate)
    def persist(self, candidate):
        torch.save({"weights": candidate.state_dict()}, self.filename)
    def restore(self, candidate):
        candidate.load_state_dict(torch.load(self.filename)["weights"])

def assess(network, examples):
    predicted = network(examples[0])
    return torch.mean((predicted - examples[1]) ** 2)
'''
ARGS = {'file':'main.py','model_symbol':'model','test_symbol':'heldout',
        'validation_symbol':'validation','selection_role':'validation'}

def test_bound_imported_checkpoint_chain_distinguishes_selection_role():
    result = symbol_chain({'main.py':MAIN,'helper.py':HELPER}, ARGS)
    assert result['clear'], result
    assert not result['violation']
    assert len(result['links']) == 5
    assert result['bound_edges']

def check(main=MAIN, helper=HELPER, **args):
    return symbol_chain({'main.py': main, 'helper.py': helper}, {**ARGS, **args})


def test_auto_uses_bound_data_roles_and_detects_test_selection():
    bad = check(main=MAIN.replace('score = assess(model, validation)', 'score = assess(model, heldout)'), selection_role='auto')
    good = check(selection_role='auto')
    assert bad['violation'] and not bad['clear']
    assert good['clear'] and not good['violation']
    assert bad['selection_role'] == 'test'
    assert all(edge['bindings'] for edge in good['bound_edges'])


def test_names_can_be_changed_without_changing_the_chain():
    main = MAIN.replace('Keeper', 'ArtifactWriter').replace('assess', 'calculate').replace('keeper', 'store').replace('consider', 'update').replace('restore', 'reload')
    helper = HELPER.replace('Keeper', 'ArtifactWriter').replace('assess', 'calculate').replace('consider', 'update').replace('restore', 'reload')
    assert check(main, helper)['clear']


def test_logger_is_not_weight_persistence():
    out = check(helper=HELPER.replace('torch.save({"weights": candidate.state_dict()}, self.filename)', 'print(candidate.state_dict(), self.filename)'))
    assert not out['clear'] and not out['violation']


def test_other_model_or_checkpoint_cannot_complete_chain():
    for main, helper in [
        (MAIN.replace('keeper.restore(model)', 'keeper.restore(other)'), HELPER),
        (MAIN.replace('answer = assess(model, heldout)', 'answer = assess(other, heldout)'), HELPER),
        (MAIN, HELPER.replace('candidate.state_dict()', 'unrelated.state_dict()')),
        (MAIN, HELPER.replace('torch.load(self.filename)', 'torch.load("elsewhere.bin")')),
        (MAIN, HELPER.replace('["weights"]', '["different_weights"]')),
    ]:
        result = check(main, helper)
        assert not result['clear'] and not result['violation'], result


def test_reassigned_score_and_model_disconnect_the_chain():
    for main in [
        MAIN.replace('    keeper.consider', '    score = 0\n    keeper.consider'),
        MAIN.replace('keeper.restore(model)', 'model = Network()\nkeeper.restore(model)'),
        MAIN.replace('keeper.restore(model)', 'keeper = Keeper("weights.bin")\nkeeper.restore(model)'),
    ]:
        assert not check(main)['clear']


def test_test_input_alias_cannot_claim_validation_clear():
    for definition in ['validation = heldout', 'validation = heldout.copy()']:
        main = MAIN.replace('model = Network()', definition + '\nmodel = Network()')
        assert not check(main)['clear']


def test_fake_comparator_and_wrong_import_fail_closed():
    helper = HELPER.replace('elif score < self.best:', 'elif self.prefer(score, self.best):')
    helper = helper.replace('    def persist', '    def prefer(self, score, previous):\n        return True\n    def persist')
    assert not check(helper=helper)['clear']
    assert not check(helper=HELPER.replace('import torch', 'import logging as torch'))['clear']


def test_hidden_or_dead_persistence_is_insufficient():
    helper = HELPER.replace('        torch.save', '        if False:\n            torch.save')
    assert not check(helper=helper)['clear']
    main = MAIN.replace('answer = assess(model, heldout)', 'if False:\n    answer = assess(model, heldout)')
    assert not check(main)['clear']


def test_final_must_evaluate_restored_model_not_format_an_old_score():
    main = MAIN.replace('keeper.restore(model)', 'old = assess(model, heldout)\nkeeper.restore(model)').replace('answer = assess(model, heldout)', 'answer = abs(old)')
    assert not check(main)['clear']


def test_returned_score_slot_must_depend_on_model_prediction():
    main = MAIN.replace('score = assess(model, validation)', 'score, unused = assess(model, validation)')
    helper = HELPER.replace('return torch.mean((predicted - examples[1]) ** 2)', 'return 0, torch.mean((predicted - examples[1]) ** 2)')
    assert not check(main, helper)['clear']
    assert check(main.replace('score, unused', 'unused, score'), helper)['clear']


def test_test_fit_or_unresolved_callback_prevents_clear():
    for added in ['model.fit(heldout)', 'model.fit(training, callbacks=[Callback(heldout)])']:
        main = MAIN.replace('keeper.restore(model)', added + '\nkeeper.restore(model)')
        assert not check(main)['clear']


def test_explicit_cross_file_links_assert_discovered_evidence():
    result = check()
    links = [{k: row[k] for k in ('file', 'line', 'required_symbols')} for row in result['links']]
    assert check(links=links)['clear']
    links[2]['file'] = 'main.py'
    assert not check(links=links)['clear']


def test_helper_can_delegate_comparator_through_explicit_method_aliases():
    helper = HELPER.replace('        self.best = None', '        self.best = None\n        if mode:\n            self.compare = self.lower\n        else:\n            self.compare = self.higher')
    helper = helper.replace('elif score < self.best:', 'elif self.compare(score, self.best):')
    helper = helper.replace('    def persist', '    def lower(self, current, old):\n        return current < old\n    def higher(self, current, old):\n        return current > old\n    def persist')
    assert check(helper=helper)['clear']
    helper = helper.replace('return current > old', 'return True')
    assert not check(helper=helper)['clear']


def test_loader_loop_and_accumulated_metric_preserve_bound_input():
    helper = HELPER[:HELPER.index('def assess')] + '''def assess(network, examples):
    total = 0
    for features, labels in examples:
        predicted = network(features)
        total += torch.mean((predicted - labels) ** 2)
    return total / len(examples)
'''
    assert check(helper=helper)['clear']


def test_unresolved_helper_does_not_infer_metric_from_argument_names():
    helper = HELPER[:HELPER.index('def assess')] + '''def assess(network, examples):
    predicted = network(examples[0])
    return opaque_metric(predicted, examples[1])
'''
    assert not check(helper=helper)['clear']

INLINE = '''heldout = evaluation_pack[1]
score = model.evaluate(evaluation_pack[0], heldout)
if score > best:
    best, weights = score, model.get_weights()
model.set_weights(weights)
model.evaluate(evaluation_pack[0], heldout)
'''


def test_direct_inline_state_chain_and_repair_are_discovered_without_links():
    assert check(main=INLINE, selection_role='auto')['violation']
    clean = INLINE.replace('heldout = evaluation_pack[1]', 'validation = validation_pack[1]').replace('score = model.evaluate(evaluation_pack[0], heldout)', 'score = model.evaluate(validation_pack[0], validation)')
    assert check(main=clean, selection_role='auto')['clear']
    torch_version = INLINE.replace('get_weights', 'state_dict').replace('set_weights', 'load_state_dict')
    assert check(main=torch_version, selection_role='auto')['violation']
    for damaged in [
        INLINE.replace('model.set_weights(weights)', 'print(weights)'),
        INLINE.replace('model.set_weights(weights)', 'other.set_weights(weights)'),
        INLINE.replace('model.set_weights(weights)', 'weights = something_else\nmodel.set_weights(weights)'),
        INLINE.replace('best, weights = score, model.get_weights()', 'best, weights = score, other.get_weights()'),
        INLINE.replace('best, weights = score, model.get_weights()', 'best, weights = 0, model.get_weights()'),
    ]:
        result = check(main=damaged, selection_role='auto')
        assert not result['clear'] and not result['violation']


def test_helper_parameter_rebinding_cannot_forge_model_or_score_binding():
    mutations = [
        HELPER.replace('        torch.save', '        candidate = unrelated\n        torch.save'),
        HELPER.replace('        candidate.load_state_dict', '        candidate = unrelated\n        candidate.load_state_dict'),
        HELPER.replace('    def consider(self, score, candidate):', '    def consider(self, score, candidate):\n        score = 0'),
        HELPER.replace('    def consider(self, score, candidate):', '    def consider(self, score, candidate):\n        score += 1'),
        HELPER.replace('        torch.save', '        for candidate in others:\n            pass\n        torch.save'),
    ]
    for helper in mutations:
        result = check(helper=helper)
        assert not result['clear'] and not result['violation']


def test_checkpoint_destination_mutation_and_comparator_rebinding_fail_closed():
    main = MAIN.replace('keeper.restore(model)', 'keeper.filename = "different.bin"\nkeeper.restore(model)')
    assert not check(main)['clear']
    helper = HELPER.replace('elif score < self.best:', 'elif self.lower(score, self.best):')
    helper = helper.replace('    def persist', '    def lower(self, current, old):\n        current = 0\n        return current < old\n    def persist')
    assert not check(helper=helper)['clear']


def test_inline_dead_conditional_snapshot_cannot_support_verdict():
    dead = INLINE.replace('if score > best:\n    best, weights = score, model.get_weights()', 'if False:\n    if score > best:\n        best, weights = score, model.get_weights()')
    result = check(main=dead, selection_role='auto')
    assert not result['clear'] and not result['violation']

def test_unresolved_external_trainer_with_heldout_cannot_clear():
    assert not check(main=MAIN.replace('train(model, training)','external_trainer(model, heldout)'))['clear']

def test_misbound_output_reports_input_candidates_without_assigning_roles():
    result=check(test_symbol='answer',selection_role='auto')
    assert not result['clear'] and not result['violation']
    names={r['symbol'] for r in result['structural_candidates']}
    assert {'validation','heldout'}<=names
    assert 'answer' not in names
    assert check(selection_role='auto')['clear']
