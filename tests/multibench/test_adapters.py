from copy import deepcopy
from types import SimpleNamespace
import collections
import numpy as np
import pytest
from k1lab.errors import ContractError,Unavailable,TransportUncertain
from k1lab.multibench.types import Observation,Action,Proposal,PolicyIdentity
from k1lab.multibench.adapters.robodojo import RoboDojoRPC
from k1lab.multibench.adapters.xpolicylab import XPolicyModel,to_xpl,decode_xpl
from k1lab.multibench.adapters.robocasa import RoboCasaEnv,XiaomiRoboCasaPolicy
from k1lab.multibench.adapters.pi05 import Pi05Policy


def observation(step=0,episode='e',hz=25):
    return Observation(episode,step,'move the visible object',
        {c:np.zeros((8,8,3),np.uint8) for c in ('cam_high','cam_left_wrist','cam_right_wrist')},
        np.zeros(14,np.float32),
        {a:dict(xyz=[0.,0.,.3],quaternion_xyzw=[0.,0.,0.,1.],gripper_opening_command=0.) for a in ('left','right')},hz)


def ident(space='x5_joint14',execute=3,hz=25):
    return dict(name='fake',checkpoint_sha256='a'*64,revision='r',action_space=space,
        benchmark_training='test double',native_hz=hz,execute_steps=execute,preprocessing_id='test',stateful=True)


def joint():return Action('x5_joint14',np.zeros(14))
def eef():return Action('x5_eef16_wxyz',[0,0,.3,1,0,0,0,.2,0,0,.3,1,0,0,0,.7])


class RPC:
    def __init__(self):self.calls=[];self.tick=0;self.closed=False;self.fail=None
    def request(self,op,**kw):
        self.calls.append((op,deepcopy(kw)))
        if op==self.fail:raise IOError('uncertain')
        if op=='metadata':return dict(task='test',max_episode_steps=10,control_dt=.04,action_dim=14,frame='environment_origin')
        if op=='reset':return dict(episode_id='e',step_id=0,metadata=dict(eval_seed=0))
        if op=='teacher_observation':return dict(states=np.zeros(14,np.float32),
            eef_positions=np.array([[0,0,.3],[0,0,.3]]),eef_quaternions_wxyz=np.array([[1,0,0,0],[1,0,0,0]]),
            instruction='native actual instruction',remaining_steps=10-self.tick,
            **{c:np.zeros((8,8,3),np.uint8) for c in ('cam_high','cam_left_wrist','cam_right_wrist')})
        if op=='eef_joint_target':
            for arm in ('left','right'):
                t=kw['targets'][arm]
                assert type(t['gripper_closed']) is bool
                assert abs(np.linalg.norm(t['quaternion_wxyz'])-1)<1e-4
            return dict(action=np.zeros(14),diagnostics={})
        if op=='chunk_step':
            assert kw['actions'].shape==(1,14);self.tick+=1
            return dict(episode_id='e',step_id=self.tick,steps=[dict(valid=True,terminated=self.tick==3,
                truncated=False,success=self.tick==3)])
        if op=='fk_preview':
            assert kw['actions'].shape==(50,14)
            return dict(trajectory=[dict(index=i,joints=r.tolist()) for i,r in enumerate(kw['actions'])],measured_fk_check={'passed':True})
        if op=='finish_pilot':return {'success':self.tick==3}
        return {}
    def close(self):self.closed=True


def dojo(rpc=None,**cfg):
    x=RoboDojoRPC(cfg,rpc=rpc or RPC());x.reset(dict(task='test',layout_id=0,eval_seed=0));return x


def test_dojo_legal_observation():
    x=dojo();o=x.obs
    assert set(o.rgb)=={'cam_high','cam_left_wrist','cam_right_wrist'}
    assert o.eef['left']['gripper_is_measurement'] is False
    assert 'native_score' not in str(o.actor_state())
    assert x.hz==25 and o.instruction=='native actual instruction'


def test_dojo_targets_preserve_continuous_gripper():
    t=RoboDojoRPC.targets(eef())
    assert t['left']['gripper_closed'] is True and t['right']['gripper_closed'] is False
    assert t['left']['gripper_opening']==pytest.approx(.2)
    assert t['right']['gripper_opening']==pytest.approx(.7)


def test_dojo_target_normalizes_near_unit_at_boundary():
    a=eef();a.values[3]=1.001
    assert np.linalg.norm(RoboDojoRPC.targets(a)['left']['quaternion_wxyz'])==pytest.approx(1)


def test_dojo_native_joint_exact_ack():
    x=dojo()
    assert x.step(joint()).observation.step==1
    assert not x.step(joint()).success
    assert x.step(joint()).success
    with pytest.raises(ContractError):x.step(joint())


def test_dojo_eef_requires_controller_variant():
    x=dojo()
    with pytest.raises(Unavailable):x.step(eef())
    assert not any(op=='chunk_step' for op,_ in x.rpc.calls)
    assert x.step(eef(),correction=True).observation.step==1


def test_dojo_explicit_xiaomi_eef_variant():
    x=dojo(allow_xiaomi_eef_via_dls=True)
    assert x.step(eef()).observation.step==1
    assert x.describe()['xiaomi_eef_via_dls_variant']


@pytest.mark.parametrize('n',[1,10,16,32,50,67])
def test_dojo_fk_h50_compatibility_does_not_extend_real_actions(n):
    x=dojo();pi=PolicyIdentity(**ident(execute=n))
    p=Proposal(x.obs.stamp,0,pi.identity,[joint() for _ in range(n)])
    d=x.preview(p)
    assert len(p.actions)==n and x.rpc.tick==0
    assert all(r['index']<n for r in d['sampled_robot_fk'])
    assert d['fk_compatibility']['actual_policy_horizon']==n
    assert len([o for o,_ in x.rpc.calls if o=='fk_preview'])==(n+49)//50


def test_dojo_rpc_uncertain_poison_no_retry():
    r=RPC();x=dojo(r);r.fail='chunk_step'
    with pytest.raises(TransportUncertain):x.step(joint())
    n=len(r.calls)
    with pytest.raises(TransportUncertain):x.step(joint())
    assert len(r.calls)==n


def test_dojo_second_reset_forbidden():
    x=dojo()
    with pytest.raises(ContractError):x.reset(dict(task='test',layout_id=0))


def test_dojo_layout_group_not_reset_seed():
    x=RoboDojoRPC({},rpc=RPC())
    with pytest.raises(ContractError):x.reset(dict(task='test',layout_id=0,eval_seed=1))


def test_to_xpl_native_layout():
    o=observation();o.state=np.arange(14,dtype=np.float32)
    x=to_xpl(o)
    assert x['vision']['cam_head']['color'].shape==(8,8,3)
    assert x['state']['left_arm_joint_state'].tolist()==list(range(6))
    assert x['state']['right_arm_joint_state'].tolist()==list(range(7,13))
    assert x['state']['left_ee_pose'][3:].tolist()==[1,0,0,0]


def native_rows(n=3,ee=False):
    return [{**{f'{a}_ee_joint_state':np.array([.5]) for a in ('left','right')},
            **{f'{a}_ee_pose' if ee else f'{a}_arm_joint_state':np.array([0,0,.3,1,0,0,0]) if ee else np.zeros(6) for a in ('left','right')}} for _ in range(n)]


def test_decode_joint_vs_eef_not_interchangeable():
    assert decode_xpl(native_rows(), 'x5_joint14')[0][0].values.shape==(14,)
    assert decode_xpl(native_rows(ee=True), 'x5_eef16_wxyz')[0][0].values.shape==(16,)
    with pytest.raises(KeyError):decode_xpl(native_rows(), 'x5_eef16_wxyz')


def test_explicit_gripper_clip_count():
    rows=native_rows();rows[0]['left_ee_joint_state']=np.array([1.1])
    with pytest.raises(ContractError):decode_xpl(rows,'x5_joint14')
    acts,clips=decode_xpl(rows,'x5_joint14',True)
    assert clips==1 and acts[0].values[6]==1


class XModel:
    def __init__(self):self.obs=[];self.reset_count=0
    def reset(self):self.reset_count+=1
    def update_obs(self,o):self.obs.append(o)
    def get_action(self):return native_rows()


def xpolicy():
    model=XModel();return XPolicyModel({'policy':'internw0_delta','identity':ident()},model=model),model

def test_clipped_provider_retains_raw_gripper_diagnostics():
    model=XModel();rows=native_rows();rows[0]['left_ee_joint_state']=np.array([1.1])
    model.get_action=lambda:rows
    policy=XPolicyModel({'policy':'g05','identity':ident(),'gripper_clip':True},model=model)
    proposal=policy.propose(observation())
    assert proposal.diagnostics['gripper_clips']==1
    assert proposal.diagnostics['raw_gripper_max']==pytest.approx(1.1)
    assert proposal.diagnostics['max_gripper_clip_delta']==pytest.approx(.1)


def test_xpl_ack_exactly_once_no_dedup_drift():
    p,m=xpolicy();p.reset();o=observation();p.observe(o);p.propose(o)
    assert len(m.obs)==1 and p.pending==3
    for i in range(1,4):p.observe(observation(i))
    assert len(m.obs)==4 and p.pending==0
    p.propose(observation(3));assert len(m.obs)==4


def test_xpl_must_not_propose_unexecuted_queue():
    p,m=xpolicy();p.reset();p.propose(observation())
    with pytest.raises(ContractError):p.propose(observation())


def test_xpl_cannot_skip_ack():
    p,_=xpolicy();p.reset();p.propose(observation())
    with pytest.raises(ContractError):p.observe(observation(2))


def test_xpl_reset_on_intervention_not_fake_execute():
    p,m=xpolicy();p.reset();p.propose(observation());p.observe(observation(1))
    before=m.reset_count;p.invalidate('correction');assert m.reset_count==before+1 and p.pending==0
    p.observe(observation(2));p.propose(observation(2));assert p.pending==3


def test_xpl_cross_episode_rejected():
    p,_=xpolicy();p.reset();p.propose(observation())
    with pytest.raises(ContractError):p.observe(observation(1,'wrong'))


class Helper:
    CAMERA_KEYS=('video.left','video.right','video.wrist')
    @staticmethod
    def sample_history(queue,n,interval):
        x=list(queue);return np.stack([x[max(0,len(x)-1-(n-1-i)*interval)] for i in range(n)])
    @staticmethod
    def observation_to_state(raw):return np.full(14,raw['counter'],np.float32)
    @staticmethod
    def collect_images(raw):return {k:raw[k] for k in Helper.CAMERA_KEYS}


def rcobs(step=0):
    return Observation('r',step,'native task',{k:np.full((8,8,3),step,np.uint8) for k in Helper.CAMERA_KEYS},
           np.full(14,step,np.float32),{'arm':dict(xyz=[0,0,.3],quaternion_xyzw=[0,0,0,1])},20)


class RCClient:
    def __init__(self,n=32):self.calls=[];self.n=n;self.closed=False
    def infer(self,s,i,instruction):
        self.calls.append((s.copy(),deepcopy(i),instruction));return np.zeros((self.n,12),np.float32)
    def close(self):self.closed=True


def rcpolicy(n=32):
    client=RCClient(n);config={'identity':ident('robocasa12',16,20),'obs_history':4,'obs_interval':2}
    return XiaomiRoboCasaPolicy(config,client,Helper),client


def test_rc_actual_history_initial_padding_then_stride():
    p,c=rcpolicy();p.propose(rcobs())
    assert c.calls[0][0].shape==(4,14) and np.all(c.calls[0][0]==0)
    for i in range(1,7):p.observe(rcobs(i))
    q=p.propose(rcobs(6))
    assert c.calls[-1][0][:,0].tolist()==[0,2,4,6] and len(q.actions)==16
    assert q.diagnostics['raw_predicted_horizon']==32


def test_rc_correction_preserves_real_history():
    p,c=rcpolicy();p.observe(rcobs());p.observe(rcobs(1));p.invalidate('correction');p.observe(rcobs(2))
    p.propose(rcobs(2));assert c.calls[-1][0][-1,0]==2 and len(p.states)==3


def test_rc_skipped_observations_rejected():
    p,c=rcpolicy();p.observe(rcobs())
    with pytest.raises(ContractError):p.observe(rcobs(2))


def test_rc_source_short_chunk_rejected():
    p,c=rcpolicy(8)
    with pytest.raises(ContractError):p.propose(rcobs())


class RCGym:
    def __init__(self):self.i=0;self.actions=[];self.seed=None;self.unwrapped=SimpleNamespace(env=SimpleNamespace(control_freq=20))
    def raw(self):return {'counter':self.i,'annotation.human.task_description':'native test',
        'state.end_effector_position_relative':np.array([0,0,.3]),'state.end_effector_rotation_relative':np.array([0,0,0,1]),
        'state.gripper_qpos':np.zeros(2),**{k:np.zeros((8,8,3),np.uint8) for k in Helper.CAMERA_KEYS}}
    def reset(self,seed):self.seed=seed;return self.raw(),{}
    def step(self,a):self.actions.append(a);self.i+=1;return self.raw(),0.,False,False,{'success':self.i==2}
    def close(self):pass


def test_rc_source_seed_action_converter_native_success():
    g=RCGym();e=RoboCasaEnv({'convert_action':lambda a:{'action':a},'task_horizon':lambda t:10},g,Helper)
    o=e.reset({'task':'T','horizon':10,'split':'pretrain','environment_seed':7,'episode_seed':57})
    assert g.seed==57 and e.pose_frame.startswith('robot_base_relative')
    assert not e.step(Action('robocasa12',np.zeros(12))).success
    r=e.step(Action('robocasa12',np.zeros(12)));assert r.success and r.score is None
    with pytest.raises(ContractError):e.step(Action('robocasa12',np.zeros(12)))


def test_rc_horizon_mismatch_rejected():
    e=RoboCasaEnv({'convert_action':lambda a:a,'task_horizon':lambda t:10},RCGym(),Helper)
    with pytest.raises(ContractError):e.reset({'task':'T','horizon':5})


class PiClient:
    metadata={'checkpoint_sha256':'b'*64}
    def infer(self,raw,path):
        assert set(raw)=={'cam_high','cam_left_wrist','cam_right_wrist','states','instruction'}
        np.savez(path,actions=np.zeros((50,14)));return np.zeros((50,14)),{'inference_index':0}
    def close(self):pass


def test_pi05_keeps_h50_and_artifacts(tmp_path):
    p=Pi05Policy({'identity':ident(execute=15),'artifact_dir':str(tmp_path),'native_checkpoint_sha256':'b'*64},PiClient())
    q=p.propose(observation());assert len(q.actions)==50 and (tmp_path/'proposal_000000.npz').exists()


def test_pi05_source_hash_independent_manifest(tmp_path):
    with pytest.raises(ContractError):Pi05Policy({'identity':ident(),'artifact_dir':str(tmp_path),'native_checkpoint_sha256':'c'*64},PiClient())
