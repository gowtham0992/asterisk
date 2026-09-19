"""Bounded normalization for Python notebook exports, with original line identity.

Uploaded source is evidence, not trusted instructions. Only the standalone
``%matplotlib inline`` display directive (and its standard IPython export) is
replaced. Execution magics are rejected rather than silently deleting work.
"""
import ast
import hashlib
import io
import re
import tokenize


def normalize_source(source, filename='<source>'):
    """Return (Python source, normalization record); never renumber lines.

    Callers must retain the record beside results. Unsupported source raises
    ValueError/SyntaxError, so neither static nor dynamic callers can certify a
    partially executed notebook. No source code is executed here.
    """
    lines = source.splitlines(keepends=True)
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except (tokenize.TokenError, IndentationError) as exc:
        raise ValueError(f'Unsupported notebook source in {filename}: {exc}') from exc
    string_lines = {line for token in tokens if token.type == tokenize.STRING
                    for line in range(token.start[0], token.end[0] + 1)}
    changes = []

    def replace(line, kind):
        old = lines[line - 1]
        ending = '\r\n' if old.endswith('\r\n') else '\n' if old.endswith('\n') else ''
        indent = old[:len(old) - len(old.lstrip(' \t'))]
        lines[line - 1] = indent + 'pass  # Asterisk: display-only matplotlib inline directive' + ending
        changes.append({'line': line, 'kind': kind, 'original': old.rstrip('\r\n'),
                        'replacement': lines[line - 1].rstrip('\r\n')})

    for number, line in enumerate(lines, 1):
        stripped = line.lstrip(' \t')
        if number in string_lines or not stripped.startswith(('%', '!')):
            continue
        if re.fullmatch(r'%matplotlib[ \t]+inline[ \t]*(?:#[^\r\n]*)?(?:\r?\n)?', stripped):
            # A directive continued into/from another statement is not standalone.
            if number > 1 and source.splitlines()[number - 2].rstrip().endswith('\\'):
                raise ValueError(f'Unsupported notebook magic continuation at {filename}:{number}.')
            replace(number, 'matplotlib-inline')
        else:
            raise ValueError(f'Unsupported notebook magic or shell execution at {filename}:{number}.')

    normalized = ''.join(lines)
    tree = ast.parse(normalized, filename=filename)
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'get_ipython'):
            continue
        attribute = parents.get(node)
        call = parents.get(attribute)
        statement = parents.get(call)
        supported = (not node.args and not node.keywords
                     and isinstance(attribute, ast.Attribute) and attribute.attr == 'run_line_magic'
                     and isinstance(call, ast.Call) and len(call.args) == 2 and not call.keywords
                     and all(isinstance(arg, ast.Constant) for arg in call.args)
                     and [arg.value for arg in call.args] == ['matplotlib', 'inline']
                     and isinstance(statement, ast.Expr) and statement.value is call
                     and statement.lineno == statement.end_lineno
                     and normalized.splitlines()[statement.lineno - 1].strip().rstrip(';') == ast.get_source_segment(normalized, statement))
        if not supported:
            raise ValueError(f'Unsupported IPython magic or shell execution at {filename}:{node.lineno}.')
        replace(statement.lineno, 'ipython-matplotlib-inline')
    normalized = ''.join(lines)
    # Parse after replacements as a guard against accidentally changing syntax.
    ast.parse(normalized, filename=filename)
    record = {'version': 'notebook-normalization-1',
              'original_sha256': hashlib.sha256(source.encode()).hexdigest(),
              'normalized_sha256': hashlib.sha256(normalized.encode()).hexdigest(),
              'line_map': list(range(1, len(lines) + 1)),
              'changes': sorted(changes, key=lambda change: change['line'])}
    return normalized, record
