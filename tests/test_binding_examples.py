from app.binding_examples import source_examples
from app.receipt import preview
from tests.test_primitives import FILES, ARGS


def test_examples_keep_exact_ids_and_missing_mapping_without_a_verdict():
    files={**FILES,'map.csv':'image,subject_id\na,001\nb,\n'}
    examples=source_examples(files,ARGS)
    assert [(r['sample'],r['entity'],r['mapping_row']) for r in examples['rows']]==[('a','001',2),('b','',3),('c',None,None)]
    assert examples['rows'][0]['split_row']==2
    assert 'verdict' not in examples
    assert 'do not establish' in examples['scope']


def test_examples_bound_each_side_and_ignore_other_labels():
    files={**FILES,'split.csv':'image,part\n'+''.join(f's{i},train\n' for i in range(8))+''.join(f't{i},test\n' for i in range(8))+'ignored,other\n',
           'map.csv':'image,subject_id\n'+''.join(f's{i},u{i}\n' for i in range(8))+''.join(f't{i},v{i}\n' for i in range(8))}
    rows=source_examples(files,ARGS)['rows']
    assert [r['sample'] for r in rows]==['s0','s1','s2','t0','t1','t2']
    assert rows[3]['split_row']==10


def test_source_examples_do_not_change_binding_hash():
    original=preview('Independent specimens',FILES,ARGS)
    enriched={**original,'source_examples':source_examples(FILES,ARGS)}
    assert enriched['binding_hash']==preview('Independent specimens',FILES,ARGS)['binding_hash']
