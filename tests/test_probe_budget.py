import importlib.util
from pathlib import Path
import concurrent.futures
spec=importlib.util.spec_from_file_location('probe_budget',Path(__file__).parents[1]/'evaluation/probe-pilot/budget.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
def test_concurrent_reservations_cannot_overspend_and_uncertain_usage_stays_reserved(tmp_path):
    b=module.Budget(tmp_path/'budget.json',{'m':(1,3)},limit=1)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        ids=list(pool.map(lambda _:b.reserve('m',100000,100000),range(8)))
    accepted=[i for i in ids if i];assert len(accepted)==2
    b.uncertain(accepted[0]);b.settle(accepted[1],10000,10000)
    assert b.state['settled_usd']==.04
    assert len(b.state['reservations'])==1
    assert b.reserve('m',0,200000) is None
    restored=module.Budget(tmp_path/'budget.json',{'m':(1,3)},limit=100)
    assert restored.state['limit_usd']==1
    assert restored.reserve('m',0,200000) is None
