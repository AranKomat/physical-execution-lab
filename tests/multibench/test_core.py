import copy
from dataclasses import asdict
import json
import numpy as np
import pytest
from k1lab.errors import ContractError
from k1lab.util import load_json,digest,atomic_json
from k1lab.journal import verify
from k1lab.multibench.types import Action,Proposal,PolicyIdentity,StepResult
from k1lab.multibench.governor import SparseGovernor,MonitorConfig
from k1lab.multibench.actor import decode,Decision
from k1lab.multibench.runner import run_episode,usage_summary
from k1lab.multibench.synthetic import ToyEnv,ToyPolicy,ToyReviewer
from k1lab.multibench.transport import encode_obs,decode_obs,PolicyDispatcher
from k1lab.multibench.latency import benchmark


def obs():return ToyEnv().observation()
def progress():return {'completed_claims':[],'currently_attempting':'move','uncertain_or_invalidated':[]}
def decision(mode='accept',steps=4,actions=None):return {'mode':mode,'steps':steps,'actions':actions or [],'execution':'progressing','intent':'aligned','evidence':'Current robot state observed.','progress':progress()}
def case():return {'case_id':'toy','task':'fixture','task_group':'fixture','benchmark':'synthetic','partition':'dev'}
def config(mode='sparse'):return {'name':mode,'mode':mode,'max_decision_steps':6,'max_correction_steps':5,'max_reviews':100,'monitor':{'max_unreviewed_steps':12,'max_unreviewed_chunks':3},'wall_limit_s':50}


def test_actor_observation_whitelist():
    o=obs();o.signals={'native_score':1,'object_pose':[1,2,3],'tracking_lost':True};o.native={'object_gt':'hidden'}
    text=json.dumps(o.actor_state());assert 'native_score' not in text and 'object_gt' not in text and 'object_pose' not in text
    assert o.actor_state()['sensor_signals']=={'tracking_lost':True}

@pytest.mark.parametrize('space,n',[('x5_joint14',14),('x5_eef16_wxyz',16),('robocasa12',12)])
def test_wrong_shape_rejected(space,n):
    with pytest.raises(ContractError):Action(space,[0.]*(n-1))
@pytest.mark.parametrize('bad',[float('nan'),float('inf'),-float('inf')])
def test_nonfinite_action(bad):
    a=np.zeros(14);a[0]=bad
    with pytest.raises(ContractError):Action('x5_joint14',a)
@pytest.mark.parametrize('value',[[True]*14,['0']*14])
def test_non_numeric_action(value):
    with pytest.raises(ContractError):Action('x5_joint14',value)
@pytest.mark.parametrize('g',[-.1,1.1])
def test_gripper_no_silent_clip(g):
    a=np.zeros(14);a[6]=g
    with pytest.raises(ContractError):Action('x5_joint14',a)

def test_quaternion_invalid():
    with pytest.raises(ContractError):Action('x5_eef16_wxyz',np.zeros(16))

def test_proposal_binds_observation_and_clock():
    o=obs();p=ToyPolicy();p.reset();q=p.propose(o);q.validate(o,p.identity)
    q.step=1
    with pytest.raises(ContractError):q.validate(o,p.identity)
    q.step=0;other=PolicyIdentity(**(asdict(p.identity)|{'native_hz':30}));q.policy_identity=other.identity
    with pytest.raises(ContractError):q.validate(o,other)

def test_wire_roundtrip_no_hidden_state():
    o=obs();o.native={'object_gt':True};wire=encode_obs(o);r=decode_obs(wire)
    assert o.stamp==r.stamp and r.native=={}
    wire['reward']=1
    with pytest.raises(ContractError):decode_obs(wire)

def test_initial_and_periodic_semantic_check():
    g=SparseGovernor(MonitorConfig(max_unreviewed_steps=10));g.reviewed(0)
    assert g.review_reasons('sparse',9)==[]
    assert 'periodic_semantic_review' in g.review_reasons('sparse',10)
    assert g.allowance(9,5,'sparse')==1
    g.reset();assert g.review_reasons('sparse',0)==['initial_semantic_review']

def test_smooth_motion_not_semantic_certificate():
    g=SparseGovernor(MonitorConfig(max_unreviewed_steps=6));g.reviewed(0)
    e=ToyEnv()
    for i in range(6):e.step(Action('x5_joint14',np.zeros(14)));g.observe(e.observation())
    assert 'periodic_semantic_review' in g.review_reasons('sparse',6)

def test_gripper_transition_is_not_attachment():
    g=SparseGovernor();g.reviewed(0);o=obs();o.step=6
    a=np.zeros(14);g.observe(o,executed_action=Action('x5_joint14',a));o.step=7;a[6]=1
    g.observe(o,executed_action=Action('x5_joint14',a))
    assert any('not_grasp_confirmation' in x for x in g.pending)

def test_stagnation_is_review_not_task_failure():
    g=SparseGovernor(MonitorConfig(stall_window=4));g.reviewed(0);e=ToyEnv(stall=True)
    for i in range(6):g.observe(e.observation());e.step(Action('x5_joint14',np.zeros(14)))
    assert g.pending==['robot_motion_stagnation_requires_review','robot_motion_stagnation_requires_review']

def test_rotational_progress_not_stationary():
    g=SparseGovernor(MonitorConfig(stall_window=4));g.reviewed(0);o=obs()
    from scipy.spatial.transform import Rotation
    for i in range(6):
        o.step=i;o.eef['left']['quaternion_xyzw']=Rotation.from_euler('z',i*.1).as_quat().tolist();g.observe(o)
    assert not g.pending

def test_numerical_risk_without_semantic_guess():
    o=obs();p=ToyPolicy().propose(o);p.actions[0].values[0]=2
    assert SparseGovernor().proposal_risks(p,o)==['large_first_joint_target_jump']

@pytest.mark.parametrize('mutation',[{'mode':'magic'},{'steps':True},{'mode':'stop','steps':2},{'evidence':''},{'progress':{}},{'unexpected':1}])
def test_invalid_decision_rejected(mutation):
    o=obs();p=ToyPolicy().propose(o)
    with pytest.raises(ContractError):decode(decision()|mutation,o,p,'x5_eef16_wxyz',15)

def test_uncertainty_not_authority_to_takeover():
    o=obs();p=ToyPolicy().propose(o);a=[0,0,.3,1,0,0,0,1]*2
    with pytest.raises(ContractError):decode(decision('correct',1,[a]),o,p,'x5_eef16_wxyz',5)
    d=decision('correct',1,[a])|{'execution':'failed'}
    assert decode(d,o,p,'x5_eef16_wxyz',5).mode=='correct'
    a[0]=1
    with pytest.raises(ContractError):decode(d|{'actions':[a]},o,p,'x5_eef16_wxyz',5)

def test_robocasa_no_unqualified_base_control():
    o=obs();p=ToyPolicy().propose(o);a=[0]*12;a[11]=-1
    d=decision('correct',1,[a])|{'intent':'misaligned'}
    assert decode(d,o,p,'robocasa12',5)
    a[8]=1
    with pytest.raises(ContractError):decode(d|{'actions':[a]},o,p,'robocasa12',5)

@pytest.mark.parametrize('mode',['motor_only','review_every_chunk','sparse','direct_dense','direct_sparse'])
def test_episode_paths_run_and_audit(mode,tmp_path):
    c=config(mode)
    if mode.startswith('direct'):c.update(max_decision_steps=5)
    p=None if mode.startswith('direct') else ToyPolicy()
    result=run_episode(ToyEnv(18),p,None if mode=='motor_only' else ToyReviewer(),case(),c,tmp_path/mode)
    assert result['success'] and result['native_steps']==18
    assert result['evidence_kind']=='synthetic'
    assert verify(tmp_path/mode/'events.jsonl')['events']>0
    assert 'native_score' not in json.dumps(load_json(tmp_path/mode/'receipts.json'))

def test_sparse_not_automatic_every_boundary(tmp_path):
    a=run_episode(ToyEnv(36),ToyPolicy(),ToyReviewer(),case(),config('review_every_chunk'),tmp_path/'a')
    b=run_episode(ToyEnv(36),ToyPolicy(),ToyReviewer(),case(),config('sparse'),tmp_path/'b')
    assert a['metrics']['review_calls']>b['metrics']['review_calls']
    assert a['native_steps']==b['native_steps']

def test_explicit_policy_clipping_is_counted(tmp_path):
    class ClippedPolicy(ToyPolicy):
        def propose(self,obs):
            proposal=super().propose(obs)
            proposal.diagnostics['gripper_clips']=2
            return proposal
    r=run_episode(ToyEnv(12),ClippedPolicy(),None,case(),config('motor_only'),tmp_path/'r')
    assert r['metrics']['gripper_clips']==2*r['metrics']['policy_calls']

def test_model_stop_is_not_success(tmp_path):
    class Reviewer(ToyReviewer):
        def review(self,*args,**kw):return Decision('stop',0,[],evidence='Not enough evidence.',progress=progress())
    r=run_episode(ToyEnv(),ToyPolicy(),Reviewer(),case(),config(),tmp_path/'r')
    assert not r['success'] and r['termination']=='model_stop_incomplete' and r['native_steps']==0

def test_every_physical_ack_and_interruption_reset(tmp_path):
    p=ToyPolicy(6);c=config();c['monitor']['max_unreviewed_steps']=8
    r=run_episode(ToyEnv(24),p,ToyReviewer(),case(),c,tmp_path/'r')
    assert r['success'] and p.acks==24 and r['metrics']['discarded_policy_actions']>0

def test_no_retry_on_uncertain_step(tmp_path):
    class Broken(ToyEnv):
        calls=0
        def step(self,*a,**kw):self.calls+=1;raise TimeoutError('ACK lost')
    e=Broken();r=run_episode(e,ToyPolicy(),ToyReviewer(),case(),config(),tmp_path/'r')
    assert e.calls==1 and r['status']=='infrastructure_or_contract_error' and not r['success']

def test_no_overwrite(tmp_path):
    run_episode(ToyEnv(6),ToyPolicy(),None,case(),config('motor_only'),tmp_path/'r')
    with pytest.raises(FileExistsError):run_episode(ToyEnv(6),ToyPolicy(),None,case(),config('motor_only'),tmp_path/'r')

def test_policy_dispatcher_owner_and_replay():
    d=PolicyDispatcher(ToyPolicy())
    def request(op,seq,args={}):
        r={'owner':'a','seq':seq,'op':op,'args':args};return {'request':r,'request_sha256':digest(r)}
    d.dispatch(request('acquire',0));d.dispatch(request('reset',1))
    with pytest.raises(ContractError):d.dispatch(request('reset',1))
    d.dispatch(request('observe',2,{'observation':encode_obs(obs())}))
    out=d.dispatch(request('propose',3,{'observation':encode_obs(obs())}))
    assert len(out['result']['actions'])==6

def test_microbench_stateful_cancels_without_physics():
    p=ToyPolicy();r=benchmark(p,[obs()],warmup=1,repeats=4)
    assert r['samples']==4 and r['native_execution_measured'] is False
    assert p.acks==0 and r['nominal_ms_per_exposed_action']>=0

def test_usage_reasoning_subset_not_double_count():
    class C:usages=[{'prompt_tokens':100,'completion_tokens':10,'prompt_tokens_details':{'cached_tokens':90},'completion_tokens_details':{'reasoning_tokens':7}}];n=1
    class R:client=C()
    r=usage_summary(R());assert r['output_tokens']==10 and r['reasoning_tokens']==7
    assert usage_summary(None)['api_requests']==0


def test_usage_total_unknown_when_a_request_failed_without_usage():
    class C:
        usages=[{'prompt_tokens':100,'completion_tokens':10,
                 'completion_tokens_details':{'reasoning_tokens':7}}]
        n=2
    class R:client=C()
    result=usage_summary(R())
    assert result['api_requests']==2 and result['unreported_requests']==1
    assert not result['all_request_usage_rows_present']
    assert result['input_tokens'] is result['output_tokens'] is result['reasoning_tokens'] is None
    assert result['known_usage_subtotals']['input_tokens']==100
    assert result['known_usage_subtotals']['output_tokens']==10


def test_failed_review_wait_is_counted_without_retry(tmp_path):
    class Clock:
        now=0.
        def __call__(self):return self.now
    clock=Clock()
    class Reviewer(ToyReviewer):
        calls=0
        def review(self,*args,**kwargs):
            self.calls+=1
            clock.now+=2.5
            raise TimeoutError('provider unavailable')
    reviewer=Reviewer()
    result=run_episode(ToyEnv(),ToyPolicy(),reviewer,case(),config(),tmp_path/'r',clock=clock)
    assert reviewer.calls==1 and result['native_steps']==0
    assert result['status']=='infrastructure_or_contract_error'
    assert result['timing']['review_s']==result['elapsed_s']==2.5
    assert result['metrics']['proposed_policy_actions']==6
    assert result['metrics']['unresolved_policy_actions']==6
    assert result['metrics']['discarded_policy_actions']==0


def test_successful_proposal_accounting_has_no_unresolved_actions(tmp_path):
    result=run_episode(ToyEnv(13),ToyPolicy(),None,case(),config('motor_only'),tmp_path/'r')
    metrics=result['metrics']
    assert result['success'] and metrics['unresolved_policy_actions']==0
    assert metrics['proposed_policy_actions']==metrics['motor_steps']+metrics['discarded_policy_actions']
