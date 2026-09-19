"""Bound cross-file checkpoint source chains. This never executes uploaded code.

The supported subset is deliberately small: direct imports, local functions,
instance methods, assignment aliases, numeric expressions, state_dict saves and
loads, and direct model prediction/evaluation calls. Unknown calls do not prove
that their result depends on their arguments. Source evidence is conditional on
following the cited path; it is not a claim that historical execution occurred.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import PurePosixPath


def symbol(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = symbol(node.value)
        return base + '.' + node.attr if base else ''
    return ''


def symbols(node):
    return {symbol(n) for n in ast.walk(node) if isinstance(n, (ast.Name, ast.Attribute))} - {''}


def targets(node):
    values = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, (ast.AnnAssign, ast.AugAssign)) else []
    def bound(value):
        if isinstance(value, ast.Name):
            return {value.id}
        if isinstance(value, (ast.Tuple, ast.List)):
            return set().union(*(bound(v) for v in value.elts))
        return set()
    return set().union(*(bound(v) for v in values)) if values else set()


def statements(scope):
    """Walk one lexical scope, excluding nested definitions."""
    for node in ast.iter_child_nodes(scope):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        yield node
        yield from statements(node)


@dataclass(frozen=True)
class Value:
    roots: frozenset[str] = frozenset()
    models: frozenset[str] = frozenset()
    edges: tuple = ()

    def union(self, other):
        return Value(self.roots | other.roots, self.models | other.models, self.edges + other.edges)


def union(values):
    result = Value()
    for value in values:
        result = result.union(value)
    return result


@dataclass
class Unit:
    path: str
    source: str
    tree: ast.Module
    parents: dict = field(init=False)

    def __post_init__(self):
        self.parents = {child: parent for parent in ast.walk(self.tree) for child in ast.iter_child_nodes(parent)}

    def scope(self, node):
        while node in self.parents:
            node = self.parents[node]
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Module)):
                return node
        return self.tree

    def ancestors(self, node):
        result = []
        while node in self.parents:
            node = self.parents[node]
            result.append(node)
        return result

    def row(self, node, required=None):
        return {'file': self.path, 'line': node.lineno, 'end_line': node.end_lineno,
                'text': ast.get_source_segment(self.source, node),
                'required_symbols': sorted(required or symbols(node)), 'verified': True}


class Source:
    def __init__(self, files):
        self.units = {}
        self.anchors = set()
        for path, source in files.items():
            if path.endswith('.py'):
                try:
                    self.units[path] = Unit(path, source, ast.parse(source, filename=path))
                except SyntaxError:
                    pass

    def module(self, caller, name):
        suffix = name.replace('.', '/') + '.py'
        relative = str(PurePosixPath(caller.path).parent / suffix)
        choices = [u for p, u in self.units.items() if p == relative or p == suffix]
        return choices[0] if len(choices) == 1 else None

    def declaration(self, unit, name, scope=None):
        local = [n for n in (scope or unit.tree).body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == name]
        if len(local) == 1:
            return unit, local[0]
        if local:
            return None
        candidates = []
        for n in unit.tree.body:
            if not isinstance(n, ast.ImportFrom) or n.level or not n.module:
                continue
            imported = self.module(unit, n.module)
            if not imported:
                continue
            for alias in n.names:
                if alias.name == '*' or (alias.asname or alias.name) == name:
                    actual = name if alias.name == '*' else alias.name
                    candidates += [(imported, d) for d in imported.tree.body
                                   if isinstance(d, (ast.FunctionDef, ast.ClassDef)) and d.name == actual]
        return candidates[0] if len(candidates) == 1 else None

    def imported_name(self, unit, node):
        name = symbol(node)
        root, _, rest = name.partition('.')
        choices = []
        for n in unit.tree.body:
            if isinstance(n, ast.Import):
                choices += [a.name + ('.' + rest if rest else '') for a in n.names if (a.asname or a.name) == root]
            if isinstance(n, ast.ImportFrom) and not n.level:
                choices += [(n.module or '') + '.' + a.name + ('.' + rest if rest else '') for a in n.names if (a.asname or a.name) == root]
        # A local shadow makes an import binding unresolved.
        if any(root in targets(n) for n in ast.walk(unit.tree)):
            return ''
        return choices[0] if len(choices) == 1 else ''

    def definition(self, unit, scope, name, before):
        candidates = [n for n in statements(scope) if isinstance(n, (ast.Assign, ast.AnnAssign, ast.AugAssign)) and name in targets(n) and n.lineno < before]
        return max(candidates, key=lambda n: n.lineno) if candidates else None

    def key(self, unit, scope, name):
        return f'{unit.path}:{getattr(scope, "lineno", 0)}:{name}'

    def parameters(self, function, call, values, bound_self=None):
        params = list(function.args.posonlyargs) + list(function.args.args)
        if function.args.vararg or function.args.kwarg or any(isinstance(a, ast.Starred) for a in call.args):
            return None
        mapping = {}
        if bound_self is not None:
            if not params:
                return None
            mapping[params.pop(0).arg] = bound_self
        if len(call.args) > len(params):
            return None
        for parameter, value in zip(params, values):
            mapping[parameter.arg] = value
        # Keyword values are supplied at the tail in source order.
        allowed = {p.arg for p in params} | {p.arg for p in function.args.kwonlyargs}
        for keyword, value in zip(call.keywords, values[len(call.args):]):
            if keyword.arg not in allowed or keyword.arg in mapping:
                return None
            mapping[keyword.arg] = value
        return mapping

    def value(self, unit, scope, node, before, bindings=None, model=None, seen=frozenset(), depth=0, return_index=None):
        bindings = bindings or {}
        if node is None or depth > 12:
            return Value()
        if isinstance(node, ast.Name):
            marker = (unit.path, getattr(scope, 'lineno', 0), node.id, before)
            if marker in seen:
                return Value()
            definition = self.definition(unit, scope, node.id, before)
            if self.key(unit, scope, node.id) in self.anchors and definition is not None and not isinstance(definition.value, (ast.Name, ast.Tuple, ast.List)):
                roots = {self.key(unit, scope, node.id)}
                # Declared loader roles remain distinct outputs, but an alias
                # that explicitly refers to another declared role cannot hide it.
                for referred in symbols(definition.value):
                    if referred != node.id and self.key(unit, scope, referred) in self.anchors:
                        roots.update(self.value(unit, scope, ast.Name(id=referred), definition.lineno, bindings, model, seen | {marker}, depth + 1).roots)
                return Value(frozenset(roots))
            if self.key(unit, scope, node.id) == model and not (definition is not None and isinstance(definition.value, ast.Name)):
                return Value(frozenset({model}))
            if definition is not None:
                if isinstance(definition, ast.AugAssign):
                    previous = self.value(unit, scope, ast.Name(id=node.id), definition.lineno, bindings, model, seen | {marker}, depth + 1)
                    added = self.value(unit, scope, definition.value, definition.lineno, bindings, model, seen | {marker}, depth + 1)
                    return previous.union(added)
                # Tuple outputs get distinct source identities. Explicit tuples
                # preserve the corresponding alias rather than mixing all slots.
                if isinstance(definition, ast.Assign) and len(definition.targets) == 1 and isinstance(definition.targets[0], (ast.Tuple, ast.List)):
                    elts = definition.targets[0].elts
                    index = next((i for i, item in enumerate(elts) if isinstance(item, ast.Name) and item.id == node.id), None)
                    if index is not None and isinstance(definition.value, (ast.Tuple, ast.List)) and index < len(definition.value.elts):
                        return self.value(unit, scope, definition.value.elts[index], definition.lineno, bindings, model, seen | {marker}, depth + 1)
                    assigned = self.value(unit, scope, definition.value, definition.lineno, bindings, model, seen | {marker}, depth + 1, return_index=index)
                    if assigned.roots or assigned.models:
                        return assigned
                    return Value(frozenset({self.key(unit, scope, node.id)}))
                if isinstance(definition.value, ast.Name):
                    return self.value(unit, scope, definition.value, definition.lineno, bindings, model, seen | {marker}, depth + 1)
                result = self.value(unit, scope, definition.value, definition.lineno, bindings, model, seen | {marker}, depth + 1)
                if result.roots or result.models:
                    return result
            if node.id in bindings and definition is None:
                return bindings[node.id]
            loops = [n for n in statements(scope) if isinstance(n, ast.For) and n.lineno < before <= n.end_lineno and node.id in {x.id for x in ast.walk(n.target) if isinstance(x, ast.Name)}]
            if loops:
                loop = max(loops, key=lambda n: n.lineno)
                return self.value(unit, scope, loop.iter, loop.lineno, bindings, model, seen | {marker}, depth + 1)
            return Value(frozenset({self.key(unit, scope, node.id)}))
        if isinstance(node, ast.Constant):
            return Value()
        if isinstance(node, ast.Attribute):
            return self.value(unit, scope, node.value, before, bindings, model, seen, depth + 1)
        if isinstance(node, ast.Subscript):
            return self.value(unit, scope, node.value, before, bindings, model, seen, depth + 1)
        if isinstance(node, (ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.Compare, ast.List, ast.Tuple, ast.Dict, ast.IfExp)):
            return union(self.value(unit, scope, child, before, bindings, model, seen, depth + 1) for child in ast.iter_child_nodes(node))
        if not isinstance(node, ast.Call):
            return Value()
        values = [self.value(unit, scope, arg, before, bindings, model, seen, depth + 1) for arg in node.args]
        values += [self.value(unit, scope, kw.value, before, bindings, model, seen, depth + 1) for kw in node.keywords]
        inputs = union(values)
        receiver = node.func.value if isinstance(node.func, ast.Attribute) else node.func
        receiver_value = self.value(unit, scope, receiver, before, bindings, model, seen, depth + 1)
        method = node.func.attr if isinstance(node.func, ast.Attribute) else None
        if model and model in receiver_value.roots and (method is None or method in ('predict', 'predict_proba', 'evaluate', 'score')):
            return Value(inputs.roots, inputs.models | {model}, inputs.edges)
        imported = self.imported_name(unit, node.func)
        allowed = imported.startswith(('torch.', 'numpy.', 'scipy.stats.', 'sklearn.metrics.')) or imported in ('tqdm.tqdm', 'tqdm.auto.tqdm')
        if allowed or symbol(node.func) in ('len', 'float', 'int', 'sum', 'abs', 'min', 'max'):
            return inputs
        if method in ('view', 'reshape', 'float', 'double', 'to', 'cpu', 'detach', 'numpy', 'flatten', 'squeeze', 'mean', 'sum', 'item'):
            return receiver_value.union(inputs)
        if isinstance(node.func, ast.Name):
            declaration = self.declaration(unit, node.func.id)
            if declaration and isinstance(declaration[1], ast.FunctionDef):
                target_unit, function = declaration
                mapping = self.parameters(function, node, values)
                if mapping is None:
                    return Value()
                returns = [n.value for n in statements(function) if isinstance(n, ast.Return)]
                if return_index is not None:
                    if any(not isinstance(value, (ast.Tuple, ast.List)) or return_index >= len(value.elts) for value in returns):
                        return Value()
                    returns = [value.elts[return_index] for value in returns]
                result = union(self.value(target_unit, function, value, getattr(value, 'lineno', function.end_lineno), mapping, model, seen, depth + 1) for value in returns)
                edge = {'file': unit.path, 'line': node.lineno, 'callee_file': target_unit.path,
                        'callee_line': function.lineno, 'bindings': {p: sorted(v.roots) for p, v in mapping.items()}}
                return Value(result.roots, result.models, result.edges + (edge,))
        return Value()

    def calls_model(self, unit, scope, call, model, bindings=None, depth=0):
        if depth > 4:
            return False
        receiver = call.func.value if isinstance(call.func, ast.Attribute) else call.func
        method_name = call.func.attr if isinstance(call.func, ast.Attribute) else None
        bound = self.value(unit, scope, receiver, call.lineno, bindings, model)
        if model in bound.roots and (method_name is None or method_name in ('predict', 'predict_proba', 'evaluate', 'score')):
            return True
        if isinstance(call.func, ast.Name):
            declaration = self.declaration(unit, call.func.id)
            if declaration and isinstance(declaration[1], ast.FunctionDef):
                target_unit, function = declaration
                values = [self.value(unit, scope, a, call.lineno, bindings, model) for a in call.args]
                values += [self.value(unit, scope, k.value, call.lineno, bindings, model) for k in call.keywords]
                mapping = self.parameters(function, call, values)
                if mapping is not None:
                    return any(self.calls_model(target_unit, function, c, model, mapping, depth + 1)
                               for c in statements(function) if isinstance(c, ast.Call))
        return False

    def instance(self, unit, scope, name, before):
        definition = self.definition(unit, scope, name, before)
        if definition is None or not isinstance(definition.value, ast.Call) or not isinstance(definition.value.func, ast.Name):
            return None
        declaration = self.declaration(unit, definition.value.func.id)
        if declaration and isinstance(declaration[1], ast.ClassDef):
            return declaration
        return None


def method(cls, name):
    choices = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == name]
    return choices[0] if len(choices) == 1 else None


def compare_guard(cls, expr, score, best):
    """Check a comparison directly, or every statically assigned comparator."""
    if isinstance(expr, ast.Compare):
        return score in symbols(expr) and best in symbols(expr) and any(isinstance(op, (ast.Lt, ast.LtE, ast.Gt, ast.GtE)) for op in expr.ops)
    if not isinstance(expr, ast.Call) or not isinstance(expr.func, ast.Attribute) or symbol(expr.func.value) != 'self':
        return False
    choices = [method(cls, expr.func.attr)]
    if choices == [None]:
        assigned = [n.value.attr for n in ast.walk(cls) if isinstance(n, ast.Assign) and any(symbol(t) == symbol(expr.func) for t in n.targets)
                    and isinstance(n.value, ast.Attribute) and symbol(n.value.value) == 'self']
        choices = [method(cls, name) for name in assigned]
    if not choices or any(c is None for c in choices):
        return False
    for function in choices:
        params = [a.arg for a in function.args.args][1:]
        if _rebound(function, set(params) | {'self'}) or len(params) != len(expr.args):
            return False
        mapping = dict(zip(params, map(symbol, expr.args)))
        returns = [n.value for n in statements(function) if isinstance(n, ast.Return)]
        if not returns or any(not isinstance(r, ast.Compare) or not any(isinstance(op, (ast.Lt, ast.LtE, ast.Gt, ast.GtE)) for op in r.ops)
                              or not {score, best} <= {mapping.get(s, s) for s in symbols(r)} for r in returns):
            return False
    return True


def artifact(expr):
    """Stable checkpoint identity, restricted to a literal or self attribute."""
    if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
        return ('literal', expr.value)
    if isinstance(expr, ast.Attribute) and isinstance(expr.value, ast.Name) and expr.value.id == 'self':
        return ('member', expr.attr)
    return None


def _rebound(function, identifiers):
    """Relevant helper parameters must keep their actual caller binding."""
    for node in ast.walk(function):
        bound = targets(node)
        if isinstance(node, (ast.For, ast.AsyncFor, ast.comprehension, ast.NamedExpr)):
            bound |= {n.id for n in ast.walk(node.target) if isinstance(n, ast.Name)}
        if isinstance(node, ast.withitem) and node.optional_vars:
            bound |= {n.id for n in ast.walk(node.optional_vars) if isinstance(n, ast.Name)}
        if isinstance(node, ast.ExceptHandler) and node.name:
            bound.add(node.name)
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node is not function:
            bound.add(node.name)
        if bound & set(identifiers):
            return True
    return False


def saved_state(source, unit, cls, call, model_parameter, depth=0):
    if depth > 3 or _rebound(unit.scope(call), {model_parameter, 'self'}):
        return None
    if source.imported_name(unit, call.func) == 'torch.save' and len(call.args) >= 2:
        state, dest = call.args[:2]
        if isinstance(state, ast.Dict):
            for key, value in zip(state.keys, state.values):
                if isinstance(key, ast.Constant) and isinstance(key.value, str) and isinstance(value, ast.Call) and symbol(value.func) == model_parameter + '.state_dict' and not value.args:
                    identity = artifact(dest)
                    if identity:
                        return {'node': call, 'artifact': identity, 'key': key.value, 'bindings': []}
    if isinstance(call.func, ast.Attribute) and symbol(call.func.value) == 'self':
        function = method(cls, call.func.attr)
        if not function:
            return None
        params = [a.arg for a in function.args.args][1:]
        mapping = dict(zip(params, map(symbol, call.args)))
        model_params = [p for p, v in mapping.items() if v == model_parameter]
        if len(model_params) != 1:
            return None
        for inner in statements(function):
            if isinstance(inner, ast.Call):
                result = saved_state(source, unit, cls, inner, model_params[0], depth + 1)
                if result and not any(isinstance(a, (ast.If, ast.For, ast.While, ast.Try)) for a in unit.ancestors(inner) if a is not cls and a is not function):
                    result['bindings'].append({'file': unit.path, 'line': call.lineno, 'callee_file': unit.path, 'callee_line': function.lineno, 'bindings': mapping})
                    return result
    return None


def restored_state(source, unit, cls, name, call_model_index):
    function = method(cls, name)
    if not function:
        return None
    params = [p.arg for p in function.args.args][1:]
    if call_model_index >= len(params) or _rebound(function, {params[call_model_index], 'self'}):
        return None
    for node in statements(function):
        if not isinstance(node, ast.Call) or symbol(node.func) != params[call_model_index] + '.load_state_dict' or len(node.args) != 1:
            continue
        state = node.args[0]
        if not isinstance(state, ast.Subscript) or not isinstance(state.value, ast.Call) or source.imported_name(unit, state.value.func) != 'torch.load' or not state.value.args:
            continue
        if not isinstance(state.slice, ast.Constant) or not isinstance(state.slice.value, str):
            continue
        identity = artifact(state.value.args[0])
        if identity and not any(isinstance(a, (ast.If, ast.For, ast.While, ast.Try)) for a in unit.ancestors(node) if a is not cls and a is not function):
            return {'node': node, 'artifact': identity, 'key': state.slice.value, 'function': function}
    return None


def _stable_artifact(cls, identity):
    if identity[0] != 'member':
        return True
    name = 'self.' + identity[1]
    return not any(symbol(target) == name for function in cls.body if isinstance(function, ast.FunctionDef) and function.name != '__init__'
                   for n in statements(function) if isinstance(n, ast.Assign) for target in n.targets)


def _updates(source, unit, cls, function, score_parameter, model_parameter):
    if _rebound(function, {score_parameter, model_parameter, 'self'}):
        return
    for condition in statements(function):
        if not isinstance(condition, ast.If):
            continue
        for update in condition.body:
            if not isinstance(update, ast.Assign) or len(update.targets) != 1 or symbol(update.value) != score_parameter:
                continue
            best = symbol(update.targets[0])
            if not best.startswith('self.') or not compare_guard(cls, condition.test, score_parameter, best):
                continue
            for later in condition.body:
                if later.lineno <= update.lineno:
                    continue
                for call in [later.value] if isinstance(later, (ast.Expr, ast.Assign)) else []:
                    if isinstance(call, ast.Call):
                        persisted = saved_state(source, unit, cls, call, model_parameter)
                        if persisted and _stable_artifact(cls, persisted['artifact']):
                            yield update, persisted


def _test_in_training(source, unit, scope, test_roots, model, bindings=None, depth=0):
    if depth > 4:
        return True
    for call in statements(scope):
        if not isinstance(call, ast.Call):
            continue
        method_name = call.func.attr if isinstance(call.func, ast.Attribute) else ''
        relevant = method_name in ('fit', 'fit_transform', 'partial_fit', 'backward') or any(k.arg == 'callbacks' for k in call.keywords)
        if any(k.arg == 'callbacks' and not (isinstance(k.value, ast.Constant) and k.value.value is None or isinstance(k.value, (ast.Tuple, ast.List)) and not k.value.elts) for k in call.keywords):
            return True  # Unresolved callback execution cannot establish clear.
        if relevant:
            expressions = list(call.args) + [k.value for k in call.keywords]
            if isinstance(call.func, ast.Attribute):
                expressions.append(call.func.value)
            value = union(source.value(unit, scope, e, call.lineno, bindings, model) for e in expressions)
            if test_roots & value.roots:
                return True
        expressions=list(call.args)+[k.value for k in call.keywords]
        input_value=union(source.value(unit,scope,e,call.lineno,bindings,model) for e in expressions)
        local=source.declaration(unit,call.func.id) if isinstance(call.func,ast.Name) else None
        # An unresolved function receiving both model and held-out data may train.
        # Known model evaluation methods are selection evidence, not training calls.
        if not local and model in input_value.roots and test_roots & input_value.roots:
            return True
        if isinstance(call.func, ast.Name):
            declaration = source.declaration(unit, call.func.id)
            if declaration and isinstance(declaration[1], ast.FunctionDef):
                target_unit, function = declaration
                values = [source.value(unit, scope, a, call.lineno, bindings, model) for a in call.args]
                values += [source.value(unit, scope, k.value, call.lineno, bindings, model) for k in call.keywords]
                mapping = source.parameters(function, call, values)
                if mapping is not None and _test_in_training(source, target_unit, function, test_roots, model, mapping, depth + 1):
                    return True
    return False


def _compatible(unit, left, right):
    def conditions(node):
        result = {}
        child = node
        while child in unit.parents:
            parent = unit.parents[child]
            if isinstance(parent, ast.If):
                in_body = child in parent.body
                result[parent] = in_body
                if isinstance(parent.test, ast.Constant) and bool(parent.test.value) != in_body:
                    return None
            child = parent
        return result
    a, b = conditions(left), conditions(right)
    return a is not None and b is not None and all(a[k] == b[k] for k in a.keys() & b.keys())


def _assignment_pairs(node):
    if not isinstance(node, ast.Assign) or len(node.targets) != 1:
        return []
    target = node.targets[0]
    if isinstance(target, ast.Name):
        return [(target.id, node.value)]
    if isinstance(target, (ast.Tuple, ast.List)) and isinstance(node.value, (ast.Tuple, ast.List)) and len(target.elts) == len(node.value.elts):
        return [(t.id, v) for t, v in zip(target.elts, node.value.elts) if isinstance(t, ast.Name)]
    return []


def _inline_candidates(source, unit, args):
    """Direct best-score / state snapshot / restore source pattern."""
    mode = args['selection_role']
    model_name, test_name = args['model_symbol'], args['test_symbol']
    selected_name = test_name if mode == 'test' else args['validation_symbol']
    results = []
    for selection in ast.walk(unit.tree):
        if not isinstance(selection, ast.Assign) or not isinstance(selection.value, ast.Call) or len(targets(selection)) != 1:
            continue
        scope = unit.scope(selection)
        model = source.key(unit, scope, model_name)
        source.anchors.update({source.key(unit, scope, selected_name), source.key(unit, scope, test_name)})
        definition = source.definition(unit, scope, selected_name, selection.lineno)
        if definition is None:
            continue
        selected = source.value(unit, scope, ast.Name(id=selected_name), selection.lineno, model=model)
        heldout = source.value(unit, scope, ast.Name(id=test_name), selection.lineno, model=model)
        value = source.value(unit, scope, selection.value, selection.lineno, model=model)
        if model not in value.models or not selected.roots & value.roots or mode == 'validation' and (selected.roots & heldout.roots or heldout.roots & value.roots):
            continue
        score_name = next(iter(targets(selection)))
        for condition in statements(scope):
            if not isinstance(condition, ast.If) or condition.lineno <= selection.lineno or not isinstance(condition.test, ast.Compare):
                continue
            if not _compatible(unit, selection, condition):
                continue
            compared = symbols(condition.test)
            if score_name not in compared or not any(isinstance(op, (ast.Lt, ast.LtE, ast.Gt, ast.GtE)) for op in condition.test.ops):
                continue
            updates = [(n, t) for n in condition.body for t, v in _assignment_pairs(n) if symbol(v) == score_name and t in compared]
            snapshots = [(n, t, v) for n in condition.body for t, v in _assignment_pairs(n)
                         if isinstance(v, ast.Call) and isinstance(v.func, ast.Attribute)
                         and symbol(v.func.value) == model_name and v.func.attr in ('get_weights', 'state_dict') and not v.args]
            if len(updates) != 1 or len(snapshots) != 1 or source.definition(unit, scope, score_name, condition.lineno) is not selection:
                continue
            update, _ = updates[0]
            snapshot, state_name, state_call = snapshots[0]
            restore_method = 'set_weights' if state_call.func.attr == 'get_weights' else 'load_state_dict'
            for restore in statements(scope):
                if not isinstance(restore, ast.Call) or restore.lineno <= condition.end_lineno or symbol(restore.func) != model_name + '.' + restore_method or len(restore.args) != 1 or symbol(restore.args[0]) != state_name:
                    continue
                if source.definition(unit, scope, state_name, restore.lineno) is not snapshot or not _compatible(unit, selection, restore) or not _compatible(unit, snapshot, restore):
                    continue
                for final in statements(scope):
                    if not isinstance(final, ast.Call) or final.lineno <= restore.lineno or not _compatible(unit, restore, final) or not source.calls_model(unit, scope, final, model):
                        continue
                    final_value = source.value(unit, scope, final, final.lineno, model=model)
                    if model not in final_value.models or not heldout.roots & final_value.roots:
                        continue
                    if any(model_name in targets(n) and selection.lineno < n.lineno < final.lineno for n in statements(scope)):
                        continue
                    if mode == 'validation' and _test_in_training(source, unit, scope, heldout.roots, model):
                        continue
                    links = [unit.row(n) for n in (definition, selection, update, restore, final)]
                    for i, row in enumerate(links, 1):
                        row['link'] = i
                    edges = [{'file': unit.path, 'line': selection.lineno, 'bindings': {'score': score_name}},
                             {'file': unit.path, 'line': snapshot.lineno, 'bindings': {'model': model_name, 'snapshot': state_name}},
                             {'file': unit.path, 'line': restore.lineno, 'bindings': {'snapshot': state_name, 'model': model_name}}]
                    results.append({'available': True, 'file': unit.path, 'links': links, 'bound_edges': edges,
                                    'roles_verified': [True] * 5, 'failed_links': [], 'selection_role': mode,
                                    'test_in_fit_or_callback': False, 'training_path_resolved': False, 'violation': mode == 'test', 'clear': mode == 'validation',
                                    'missing': [], 'limitations': ['Static source path only; no historical execution claim.', 'validation and test disjointness not established', 'Unresolved external training calls are outside this selection-path check.']})
    return results


def structural_candidates(files, args):
    """Report call input slots, never infer which input is scientifically held out."""
    path=args.get('file') or args.get('entry_file')
    source=Source(files)
    if path not in source.units:return []
    unit=source.units[path];model=args.get('model_symbol','');rows=[]
    for call in ast.walk(unit.tree):
        if not isinstance(call,ast.Call):continue
        # Calls receiving the selected model, or methods on that model, expose
        # candidate data slots. Exclude assignment outputs by construction.
        receives=any(model in symbols(a) for a in call.args) or (isinstance(call.func,ast.Attribute) and model in symbols(call.func.value))
        receives=receives or any(model in symbols(k.value) for k in call.keywords)
        if not receives:continue
        for slot,value in [(str(i),a) for i,a in enumerate(call.args)]+[(k.arg or '**',k.value) for k in call.keywords]:
            for name in sorted(symbols(value)-{model}):
                if name.isidentifier():rows.append({'file':path,'line':call.lineno,'call':ast.unparse(call.func),'argument_slot':slot,'symbol':name})
    return rows[:80]


def symbol_chain(files, args):
    """Discover and verify a five-link chain using caller/callee bindings.

    ``file`` and explicit model/test/validation symbol roles anchor the query.
    Optional links assert file/line/required_symbols against the discovered
    chain; they cannot supply or manufacture an edge. Ambiguous candidates are
    insufficient. The check is scoped to the cited selection path.
    """
    path = args.get('file') or args.get('entry_file')
    mode = args.get('selection_role')
    if mode == 'auto':
        results = [symbol_chain(files, {**args, 'selection_role': role}) for role in ('test', 'validation') if role == 'test' or args.get('validation_symbol')]
        passing = [r for r in results if r.get('violation') or r.get('clear')]
        if len(passing) == 1:
            return passing[0]
        return {'available': True, 'file': path, 'links': [], 'bound_edges': [], 'violation': False, 'clear': False,
                'selection_role': 'auto', 'missing': ['unambiguous declared test or validation selection chain'], 'candidate_count': len(passing),'structural_candidates':structural_candidates(files,args),'candidate_scope':'Syntactic call inputs only; scientific roles require review.'}
    model_name, test_name, validation_name = (args.get(k, '') for k in ('model_symbol', 'test_symbol', 'validation_symbol'))
    if mode not in ('test', 'validation') or not all(isinstance(x, str) and x.isidentifier() for x in (model_name, test_name)):
        raise ValueError('Provide selection_role, model_symbol and test_symbol as simple source identifiers.')
    selected_name = test_name if mode == 'test' else validation_name
    if not isinstance(selected_name, str) or not selected_name.isidentifier():
        raise ValueError('Provide the selected label or loader identifier.')
    source = Source(files)
    if path not in source.units:
        return {'available': False, 'violation': False, 'clear': False, 'missing': ['parseable entry source']}
    unit = source.units[path]
    candidates = _inline_candidates(source, unit, args)
    for selection in ast.walk(unit.tree):
        if not isinstance(selection, ast.Assign) or not isinstance(selection.value, ast.Call):
            continue
        scope = unit.scope(selection)
        model = source.key(unit, scope, model_name)
        source.anchors.update({source.key(unit, scope, selected_name), source.key(unit, scope, test_name)})
        selected = source.value(unit, scope, ast.Name(id=selected_name), selection.lineno, model=model)
        heldout = source.value(unit, scope, ast.Name(id=test_name), selection.lineno, model=model)
        selected_definition = source.definition(unit, scope, selected_name, selection.lineno)
        if not selected_definition or not selected.roots:
            continue
        score = source.value(unit, scope, selection.value, selection.lineno, model=model)
        if model not in score.models or not selected.roots & score.roots:
            continue
        # A validation-named alias to the declared test input cannot clear.
        if mode == 'validation' and (selected.roots & heldout.roots or heldout.roots & score.roots):
            continue
        score_names = targets(selection)
        for step_call in statements(scope):
            if not isinstance(step_call, ast.Call) or not _compatible(unit, selection, step_call) or step_call.lineno <= selection.lineno or not isinstance(step_call.func, ast.Attribute) or not isinstance(step_call.func.value, ast.Name):
                continue
            instance_name = step_call.func.value.id
            declaration = source.instance(unit, scope, instance_name, step_call.lineno)
            if not declaration:
                continue
            helper_unit, cls = declaration
            function = method(cls, step_call.func.attr)
            if not function or step_call.keywords:
                continue
            params = [p.arg for p in function.args.args][1:]
            if len(params) != len(step_call.args):
                continue
            score_indices = [i for i, arg in enumerate(step_call.args) if isinstance(arg, ast.Name) and arg.id in score_names]
            model_indices = [i for i, arg in enumerate(step_call.args) if symbol(arg) == model_name]
            if len(score_indices) != 1 or len(model_indices) != 1:
                continue
            score_index, model_index = score_indices[0], model_indices[0]
            target = selection.targets[0] if len(selection.targets) == 1 else None
            if isinstance(target, (ast.Tuple, ast.List)):
                result_index = next((i for i, item in enumerate(target.elts) if symbol(item) == symbol(step_call.args[score_index])), None)
                component = source.value(unit, scope, selection.value, selection.lineno, model=model, return_index=result_index)
                if model not in component.models or not selected.roots & component.roots:
                    continue
            # A later overwrite disconnects an apparent same-name score edge.
            if source.definition(unit, scope, step_call.args[score_index].id, step_call.lineno) is not selection:
                continue
            for update, persisted in _updates(source, helper_unit, cls, function, params[score_index], params[model_index]):
                for restore in statements(scope):
                    if not isinstance(restore, ast.Call) or not _compatible(unit, step_call, restore) or restore.lineno <= step_call.lineno or not isinstance(restore.func, ast.Attribute) or symbol(restore.func.value) != instance_name or restore.keywords:
                        continue
                    indices = [i for i, arg in enumerate(restore.args) if symbol(arg) == model_name]
                    if len(indices) != 1:
                        continue
                    restored = restored_state(source, helper_unit, cls, restore.func.attr, indices[0])
                    if not restored or restored['artifact'] != persisted['artifact'] or restored['key'] != persisted['key']:
                        continue
                    for final in statements(scope):
                        if not isinstance(final, ast.Call) or not _compatible(unit, restore, final) or final.lineno <= restore.lineno:
                            continue
                        if not source.calls_model(unit, scope, final, model):
                            continue
                        evaluated = source.value(unit, scope, final, final.lineno, model=model)
                        if model not in evaluated.models or not heldout.roots & evaluated.roots:
                            continue
                        if any(isinstance(n, ast.stmt) and selection.lineno < n.lineno < final.lineno and ({model_name, instance_name} & targets(n) or isinstance(n, ast.Assign) and any(symbol(t).startswith(instance_name + '.') for t in n.targets)) for n in statements(scope)):
                            continue
                        if mode == 'validation' and _test_in_training(source, unit, scope, heldout.roots, model):
                            continue
                        links = [unit.row(selected_definition, {selected_name}), unit.row(selection),
                                 helper_unit.row(update, {symbol(update.targets[0]), params[score_index]}),
                                 helper_unit.row(persisted['node'], {params[model_index] + '.state_dict'} if symbol(persisted['node'].func) == params[model_index] + '.state_dict' else None),
                                 unit.row(final)]
                        for i, row in enumerate(links, 1):
                            row['link'] = i
                        edges = list(score.edges) + [{'file': path, 'line': step_call.lineno, 'callee_file': helper_unit.path,
                            'callee_line': function.lineno, 'bindings': dict(zip(params, map(symbol, step_call.args)))}] + persisted['bindings']
                        edges += [{'file': path, 'line': restore.lineno, 'callee_file': helper_unit.path,
                                   'callee_line': restored['function'].lineno, 'bindings': {'model': model_name},
                                   'artifact': list(restored['artifact']), 'state_key': restored['key']}]
                        edges += list(evaluated.edges)
                        candidates.append({'available': True, 'file': path, 'links': links, 'bound_edges': edges,
                            'restore': helper_unit.row(restored['node']), 'restore_call': unit.row(restore),
                            'roles_verified': [True] * 5, 'failed_links': [], 'selection_role': mode,
                            'test_in_fit_or_callback': False, 'training_path_resolved': False, 'violation': mode == 'test', 'clear': mode == 'validation',
                            'missing': [], 'limitations': ['Static source path only; no historical execution claim.',
                                                          'validation and test disjointness not established', 'Unresolved external training calls are outside this selection-path check.']})
    requested = args.get('links')
    if requested:
        if not isinstance(requested, list) or len(requested) != 5:
            raise ValueError('Exactly five links required when explicit links are supplied.')
        candidates = [candidate for candidate in candidates if all(
            isinstance(want, dict) and want.get('file', path) == found['file'] and want.get('line') == found['line']
            and isinstance(want.get('required_symbols'), list) and want['required_symbols']
            and set(want['required_symbols']) <= symbols(ast.parse(found['text']))
            for want, found in zip(requested, candidate['links']))]
    unique = {tuple((r['file'], r['line']) for r in c['links']): c for c in candidates}
    if len(unique) == 1:
        return next(iter(unique.values()))
    return {'available': True, 'file': path, 'links': [], 'bound_edges': [], 'roles_verified': [False] * 5,
            'failed_links': [1, 2, 3, 4, 5], 'selection_role': mode, 'violation': False, 'clear': False,
            'missing': ['unambiguous bound checkpoint chain' if unique else 'label-to-score, conditional update, bound state save/restore, and final model evaluation chain'],
            'candidate_count': len(unique),'structural_candidates':structural_candidates(files,args),'candidate_scope':'Syntactic call inputs only; scientific roles require review.'}
