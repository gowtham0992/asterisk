"""Bounded source excerpts: preserve original lines and complete CSV records."""
import csv
import io


def source_previews(files):
    if not files:
        return []
    # Each artifact gets space regardless of upload order. Short files donate
    # their unused space to later artifacts, but cannot starve earlier ones.
    remaining = 60000
    previews = []
    for index, (name, text) in enumerate(files.items()):
        limit = min(12000, remaining // (len(files) - index))
        is_csv = name.lower().endswith('.csv')
        lines = list(io.StringIO(text, newline='')) if is_csv else text.splitlines(keepends=True)
        end = 0
        reason = None
        if is_csv:
            reader = csv.reader(io.StringIO(text, newline=''), strict=True)
            try:
                for _ in range(6):  # header and five logical records
                    if next(reader, None) is None:
                        break
                    candidate = reader.line_num
                    if sum(map(len, lines[:candidate])) > limit:
                        reason = 'A complete CSV record exceeds this file’s context allowance.'
                        break
                    end = candidate
            except csv.Error:
                end = 0
                reason = 'Malformed CSV; repair quoting before proposing a binding.'
        else:
            used = 0
            for line in lines:
                if used + len(line) > limit:
                    reason = 'Remaining source lines exceed this file’s context allowance.'
                    break
                used += len(line)
                end += 1
        preview = ''.join(lines[:end])
        remaining -= len(preview)
        previews.append({'file': name, 'preview': preview, 'truncated': preview != text,
                         'start_line': 1 if preview else None,
                         'end_line': len(preview.splitlines()) if preview else None,
                         'omission_reason': reason})
    return previews
