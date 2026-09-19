import pytest
from scripts.run_consequence_experiment import solve,ridge

def test_pivoted_solver_known_solution():
    assert solve([[0,2],[1,3]],[4,7])==pytest.approx([1,2])

def test_ridge_closed_form_and_training_only_standardization():
    # Train mean=1, population scale=1: beta=sum(z*y)/(sum(z*z)+1)=4/3.
    r=ridge([[0],[2],[100]],[0,4,-999],[0,1],[2])
    assert r['training_mean']==[1] and r['training_scale']==[1]
    assert r['coefficients']==pytest.approx([4/3])
    assert r['mae']==pytest.approx(abs(2+99*4/3+999))


def test_size_control_keeps_leaked_rows_and_matches_removed_count():
    from scripts.run_consequence_experiment import size_matched_training
    subjects=['held','other','other','third','held'];parts=['train','train','train','train','test']
    train,dropped=size_matched_training(subjects,parts,{'held'},2,42)
    assert len(train)==2 and 0 in train and 4 not in train
    assert len(dropped)==2 and all(subjects[i]!='held' for i in dropped)
    assert size_matched_training(subjects,parts,{'held'},2,42)==(train,dropped)
