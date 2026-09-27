import csv
import io
from app.proposal_context import source_previews


def test_multiline_csv_preview_preserves_five_complete_records_and_source_bytes():
    text='id,note\r\n'+''.join(f'{i},"line one\r\nline two"\r\n' for i in range(8))
    item=source_previews({'rows.csv':text})[0]
    assert len(list(csv.reader(io.StringIO(item['preview']))))==6
    assert text.startswith(item['preview'])
    assert item['end_line']==11
    assert item['truncated'] is True


def test_context_reserves_space_for_late_documentation():
    files={f'file{i}.py':'# source\n'*2000 for i in range(10)}
    files['protocol.md']='patient_id identifies the patient, not the scanner.\n'
    items=source_previews(files)
    assert next(x for x in items if x['file']=='protocol.md')['preview']==files['protocol.md']
    assert sum(len(x['preview']) for x in items)<=60000
    assert all(x['preview'] for x in items)


def test_oversized_csv_record_is_omitted_without_partial_quoted_row():
    item=source_previews({'data.csv':'id,note\n1,"'+('x'*13000)+'"\n'})[0]
    assert item['preview']=='id,note\n'
    assert item['truncated']
    assert item['omission_reason']


def test_malformed_csv_is_explicit_and_not_presented_as_valid_rows():
    item=source_previews({'data.csv':'id,note\n1,"unclosed'})[0]
    assert item['preview']==''
    assert item['omission_reason']=='Malformed CSV; repair quoting before proposing a binding.'


def test_text_previews_do_not_create_fake_partial_source_lines():
    text='a\n'+'b'*13000+'\n'
    item=source_previews({'readme.md':text})[0]
    assert item['preview']=='a\n'
    assert item['start_line']==1 and item['end_line']==1


def test_unicode_line_separator_inside_csv_cell_does_not_shift_record_boundary():
    text='id,note\n'+''.join(f'{i},"first\u2028second"\n' for i in range(8))
    item=source_previews({'data.csv':text})[0]
    assert len(list(csv.reader(io.StringIO(item['preview']))))==6
    assert item['preview']==''.join(text.splitlines(keepends=True)[:11])
