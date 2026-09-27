from app.preparation.catalog import sources
from tests.test_preparation_package import prepared


def test_identity_counts_include_repetitions_beyond_the_preview():
    session=prepared()
    files={'data.csv':'sample,subject,split\na,p1,train\nb,p2,train\nc,p3,test\na,p1,train\n',
           'notes.txt':session.files['notes.txt']}
    source=sources(session.spec,files)[0]
    assert len(source['examples'])==3
    assert source['identity_counts']['sample']=={
        'text_records':4,'distinct_values':3,'repeated_values':1,
        'records_with_repeated_values':2,'unusable_records':0}
    # Counts do not rewrite the proposal or decide which identity is scientific.
    assert source['sample']==session.spec['sources'][0]['sample']


def test_identity_counts_do_not_coerce_missing_or_numeric_identifiers():
    spec={'sources':[{'file':'data.json','format':'json','sample':{'row':True},
                     'entity':{'column':'subject'},'partition':{'value':'train'}}]}
    files={'data.json':'[{"subject":"7"},{"subject":7},{"subject":""},{"other":"x"},{"subject":"  "}]'}
    source=sources(spec,files)[0]
    assert source['identity_counts']['subject']=={
        'text_records':2,'distinct_values':2,'repeated_values':0,
        'records_with_repeated_values':0,'unusable_records':3}
    assert source['record_count']==5


def test_repetition_examples_find_later_occurrences_and_bound_display_only():
    session=prepared()
    records=''.join(f'{name},p,train\n' for name in ['a','b','c','d','a','b','a','c','a'])
    source=sources(session.spec,{'data.csv':'sample,subject,split\n'+records})[0]
    examples=source['repeated_examples']['sample']
    assert len(examples)==3
    assert examples[0]=={'value':'a','record_count':4,'locations':[
        {'record_number':1,'reference':{'file':'data.csv','line_start':2,'line_end':2}},
        {'record_number':5,'reference':{'file':'data.csv','line_start':6,'line_end':6}},
        {'record_number':7,'reference':{'file':'data.csv','line_start':8,'line_end':8}}]}
    assert source['identity_counts']['sample']['records_with_repeated_values']==8


def test_repeat_locations_preserve_multiline_csv_and_exact_whitespace():
    session=prepared()
    source=sources(session.spec,{'data.csv':'sample,subject,split\n"a\nb",p,train\n a,p,test\n"a\nb",p,train\na,p,test\n'})[0]
    assert source['repeated_examples']['sample']==[{'value':'a\nb','record_count':2,'locations':[
        {'record_number':1,'reference':{'file':'data.csv','line_start':2,'line_end':3}},
        {'record_number':3,'reference':{'file':'data.csv','line_start':5,'line_end':6}}]}]


def test_csv_header_reference_uses_parser_record_boundaries():
    session=prepared()
    for header,expected_end in [('sample,subject,split\r\n',1),('"sample\nidentifier",subject,split\r\n',2),('"sample ""quoted""",subject,split\r',1)]:
        source=sources(session.spec,{'data.csv':header+'a,p,train\rb,q,test\r'})[0]
        assert source['header_reference']=={'file':'data.csv','line_start':1,'line_end':expected_end}
        assert source['examples'][0]['reference']['line_start']==expected_end+1
    spec={'sources':[{'file':'data.json','format':'json','sample':{'row':True},'entity':{'column':'subject'},'partition':{'value':'train'}}]}
    assert sources(spec,{'data.json':'[{"subject":"p"}]'})[0]['header_reference'] is None
