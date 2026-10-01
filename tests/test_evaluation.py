import pytest
from k1lab.evaluation import wilson,exact_discordant,compare,full_rows,summarize
from k1lab.errors import ContractError
from k1lab.manifests import seal,validate
from k1lab.util import digest


def case(i=0,partition='dev',suite='libero_goal_task'):
    return {'id':f'{suite}_{i}','suite':suite,'task_id':i,'partition':partition,'state_index':0,'horizon':300,
            'state_sha256':'a'*64,'state_file_sha256':'b'*64,'bddl_sha256':'c'*64}
def row(c,success=True):return {'case_id':c['id'],'state_sha256':c['state_sha256'],'native_success':success,
                               'native_steps':30,'elapsed_seconds':2.,'termination':'task_end','domain':'synthetic','comparison_signature':'same'}

def test_wilson_edges():
    assert wilson(0,10)[0]==0
    assert wilson(10,10)[1]==1
    assert exact_discordant(0,0)==1

def test_missing_counts_failure_and_horizon_penalty():
    c=case();rows=full_rows([c],[]);s=summarize(rows)
    assert s['episodes']==1 and s['missing']==1 and s['failure_penalized_steps_per_case']==300

def test_duplicate_not_dropped():
    c=case()
    with pytest.raises(ContractError):full_rows([c],[row(c),row(c)])

def test_state_mismatch():
    c=case()
    with pytest.raises(ContractError):full_rows([c],[row(c)|{'state_sha256':'d'*64}])

def test_paired_difference():
    cases=[case(i) for i in range(4)];left=[row(c,i<2) for i,c in enumerate(cases)];right=[row(c,i<3) for i,c in enumerate(cases)]
    r=compare(cases,left,right,bootstrap=100)
    assert r['difference_pp']==25 and r['right_only_wins']==1 and 'synthetic' in r['claim_scope']

def test_not_same_signature_not_compared():
    c=case()
    with pytest.raises(ContractError):compare([c],[row(c)],[row(c)|{'comparison_signature':'changed_model'}])

def test_models_changed_not_compared():
    c=case()
    with pytest.raises(ContractError):compare([c],[row(c)|{'resolved_models':['A']}],[row(c)|{'resolved_models':['B']}])

def test_domains_not_pooled():
    c=case()
    with pytest.raises(ContractError):compare([c],[row(c)],[row(c)|{'domain':'native_libero_pro'}])

def test_hash_and_task_split():
    m=seal({'format':1,'cases':[case(0),case(1,'test')]});assert validate(m)==m
    m['cases'][0]['state_index']=1
    with pytest.raises(ContractError):validate(m)

def test_task_and_swap_must_stay_in_same_partition():
    m=seal({'format':1,'cases':[case(0),case(0,'test','libero_goal_swap')]})
    with pytest.raises(ContractError):validate(m)

def test_bad_steps_not_accepted():
    c=case()
    with pytest.raises(ContractError):full_rows([c],[row(c)|{'native_steps':301}])
