"""Validate client-reported CSV projection against received bytes only.

Original hashes and withheld names are client assertions. No original is received
or authenticated, and no claim of anonymization is made.
"""
import copy
import csv
import hashlib
import io
import json
import re


def validate_projection(value, files):
    if value is None:
        return None
    if not isinstance(value, list) or len(value) > 80 or len(json.dumps(value).encode()) > 100_000:
        raise ValueError('Invalid projection record')
    seen = set()
    for item in value:
        required = {'file', 'original_sha256', 'projected_sha256', 'included', 'withheld', 'records'}
        if not isinstance(item, dict) or set(item) != required:
            raise ValueError('Invalid projection fields')
        name = item['file']
        if not isinstance(name, str) or name not in files or name in seen or not name.lower().endswith(('.csv','.json')):
            raise ValueError('Invalid projected file')
        seen.add(name)
        for key in ('original_sha256', 'projected_sha256'):
            if not isinstance(item[key], str) or not re.fullmatch('[0-9a-f]{64}', item[key]):
                raise ValueError('Invalid projection hash')
        included, withheld = item['included'], item['withheld']
        for names in (included, withheld):
            if not isinstance(names, list) or len(names) > 80 or any(not isinstance(n, str) or not 1 <= len(n) <= 1000 for n in names) or len(set(names)) != len(names):
                raise ValueError('Invalid projected column list')
        if not included or set(included) & set(withheld) or len(included) + len(withheld) > 80:
            raise ValueError('Projection column lists disagree')
        content = files[name]
        if hashlib.sha256(content.encode('utf-8')).hexdigest() != item['projected_sha256']:
            raise ValueError('Projected bytes differ from the supplied record')
        if name.lower().endswith('.csv'):
            try:
                reader = csv.reader(io.StringIO(content.removeprefix('\ufeff'), newline=''), strict=True)
                if next(reader, None) != included:
                    raise ValueError('Projected header differs from selected columns')
                count = 0
                for row in reader:
                    if len(row) != len(included):
                        raise ValueError('Projected record has inconsistent columns')
                    count += 1
            except csv.Error as exc:
                raise ValueError('Malformed projected CSV') from exc
        else:
            def unique(pairs):
                result = {}
                for key, value in pairs:
                    if key in result: raise ValueError('Duplicate JSON key')
                    result[key] = value
                return result
            def invalid_constant(value):
                raise ValueError('Nonfinite JSON value')
            rows = json.loads(content, object_pairs_hook=unique, parse_constant=invalid_constant)
            if not isinstance(rows, list) or not rows or len(rows) > 100000:
                raise ValueError('Projected JSON must contain records')
            for row in rows:
                if not isinstance(row, dict) or list(row) != included or any(isinstance(v, (dict, list)) for v in row.values()):
                    raise ValueError('Projected JSON fields differ from selected scalar fields')
            count = len(rows)
        if type(item['records']) is not int or not 0 <= item['records'] <= 100000 or item['records'] != count:
            raise ValueError('Projected record count differs')
    return copy.deepcopy(value)


def receipt_projection(files):
    """Find portable context in manual inputs or a retained preparation export."""
    records = []
    issues = []
    for name, content in files.items():
        if re.fullmatch(r'asterisk-projection-record(?:-\d+)?\.json', name):
            try:
                if len(content.encode()) > 100_000:
                    raise ValueError('Projection record exceeds limit')
                record = json.loads(content)
                if record.get('format') != 'asterisk-client-projection' or record.get('version') != 1:
                    raise ValueError('Unknown projection record')
                records.extend(validate_projection(record['files'], files) or [])
            except (ValueError, TypeError, KeyError, AttributeError, RecursionError):
                issues.append('A supplied projection record does not match these inputs; its original-file claims are not displayed.')
        elif name == 'preparation-review.json':
            try:
                from .receipt_context import retained_preparation
                checked = retained_preparation(files)
                if not checked or checked.get('error'):
                    raise ValueError('Preparation does not match these tables')
                record = json.loads(content)
                manifest = record.get('model_proposal', {}).get('approved_payload', {}).get('client_projection')
                if manifest is not None:
                    records.extend(validate_projection(manifest, record['inputs']) or [])
                # Only direct companions and their source tables are followed.
                # A nested preparation record cannot trigger recursive traversal.
                nested = {n: t for n, t in record['inputs'].items() if n != 'preparation-review.json'}
                nested_records, nested_issues = receipt_projection(nested)
                records.extend(nested_records)
                issues.extend(nested_issues)
            except (ValueError, TypeError, KeyError, AttributeError, RecursionError):
                issues.append('Projection context in the preparation record could not be checked.')
    # Same metadata may occur in both a companion and a retained preparation.
    unique = {json.dumps(item, sort_keys=True): item for item in records}
    return list(unique.values()), list(dict.fromkeys(issues))
