import pytest
from k1lab.errors import ContractError
from k1lab.journal import Journal
from k1lab.util import atomic_json,load_json
from scripts.multibench.audit_native_episode import audit


def episode(root,success=True,seed=0,steps=(1,)):
    atomic_json(root/'controller/result.json',{
        'status':'native_completed','success':success,'native_score':float(success),
        'native_steps':1,'case_id':'fixture','metrics':{
            'policy_calls':1,'motor_steps':1,'discarded_policy_actions':2}})
    atomic_json(root/'native/evaluation_outcome.json',{
        'complete':True,'native_success':success,'native_score':float(success),
        'native_control_steps':1,'evaluation_case':{'case_id':'fixture','policy_rng_seed':0}})
    atomic_json(root/'native/native_evaluation.json',{
        'registered':True,'condition_group_counts':{'check_list':[1]}})
    with Journal(root/'controller/events.jsonl') as journal:
        journal.append('policy_proposal',{'actions':[{}, {}, {}],'diagnostics':{
            'policy_rng_seed':seed,'raw_gripper_min':0.,'raw_gripper_max':1.,
            'max_gripper_clip_delta':0.}})
        for step in steps:journal.append('control_ack',{'step':step})


@pytest.mark.parametrize('success',[True,False])
def test_audit_accepts_complete_success_and_failure(tmp_path,success):
    episode(tmp_path,success)
    result=audit(tmp_path)
    assert result['success'] is success and result['sequential_acks']==1


def test_audit_refuses_live_result_before_reading_evaluator(tmp_path):
    atomic_json(tmp_path/'controller/result.json',{'status':'incomplete'})
    with pytest.raises(ContractError,match='terminal'):audit(tmp_path)


@pytest.mark.parametrize('seed,steps,match',[(1,(1,),'seed'),(0,(1,1),'ACK')])
def test_audit_rejects_bad_provenance(tmp_path,seed,steps,match):
    episode(tmp_path,seed=seed,steps=steps)
    with pytest.raises(ContractError,match=match):audit(tmp_path)


def test_audit_rejects_vacuous_native_conditions(tmp_path):
    episode(tmp_path)
    atomic_json(tmp_path/'native/native_evaluation.json',{
        'registered':True,'condition_group_counts':{'check_list':[0]}})
    with pytest.raises(ContractError,match='vacuous'):audit(tmp_path)


def test_audit_rejects_result_score_disagreement(tmp_path):
    episode(tmp_path)
    path=tmp_path/'controller/result.json';data=load_json(path);data['native_score']=.5
    atomic_json(path,data)
    with pytest.raises(ContractError,match='score'):audit(tmp_path)


@pytest.mark.parametrize('index,seed,checkpoint,match',[
    (0,0,'bound',None),(1,0,'bound','indices'),
    (0,1,'bound','seed'),(0,0,'wrong','checkpoint')])
def test_pi05_source_provenance(tmp_path,index,seed,checkpoint,match):
    episode(tmp_path)
    (tmp_path/'controller/events.jsonl').unlink()
    with Journal(tmp_path/'controller/events.jsonl') as journal:
        journal.append('policy_proposal',{'actions':[{}, {}, {}],
            'diagnostics':{'inference_index':index}})
        journal.append('control_ack',{'step':1})
    identity=tmp_path/'source.json';provider=tmp_path/'provider.json'
    atomic_json(identity,{'backend':'OpenPI/JAX','policy_rng_seed':seed,
        'checkpoint_sha256':checkpoint})
    atomic_json(provider,{'backend':'pi05','native_checkpoint_sha256':'bound',
        'identity':{'prediction_horizon':3}})
    if match:
        with pytest.raises(ContractError,match=match):
            audit(tmp_path,source_identity=identity,provider=provider)
    else:
        result=audit(tmp_path,source_identity=identity,provider=provider)
        assert result['raw_gripper_min'] is None
        assert result['policy_rng_seed']==0
