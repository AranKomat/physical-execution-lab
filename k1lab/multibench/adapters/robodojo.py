"""GPT-as-Policy's pinned single-owner RPC, using legal RGB + proprio only.

Joint policies use native joint control. Optional Xiaomi EEF proposals go through
bounded robot-only DLS and are explicitly a controller variant, NOT the original
XPolicyLab Xiaomi evaluation. No implicit joint/EEF retargeting is allowed.
"""
from __future__ import annotations
from pathlib import Path
import sys
import os
import uuid
import numpy as np
from scipy.spatial.transform import Rotation
from k1lab.errors import ContractError,Unavailable,TransportUncertain
from k1lab.util import load_json,file_sha
from ..types import Observation,StepResult

CAMERAS=('cam_high','cam_left_wrist','cam_right_wrist')
REV='8f3d362b077d8efb77e2a7274d5b2c20e2243846'


def check_checkout(root,revision):
    import subprocess
    root=Path(root).resolve()
    actual=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
    if actual!=revision:raise ContractError(f'source mismatch {root}: {actual} != {revision}')
    if subprocess.check_output(['git','-C',str(root),'status','--porcelain','--untracked-files=no'],text=True).strip():
        raise ContractError('tracked upstream source modified; pin a new audited revision')
    return root


class RoboDojoRPC:
    correction_space='x5_eef16_wxyz'
    pose_frame='environment_origin/link6'
    correction_description='Both arms: xyz metres, quaternion wxyz, opening 0 closed/1 open; local DLS per actual ACK.'
    evidence_kind='native_unqualified'

    def __init__(self, config, *, rpc=None):
        self.config=dict(config)
        # Operational locators may vary per episode without changing the frozen algorithm.
        if os.environ.get('K1LAB_NATIVE_OUTCOME_PATH'):self.config['native_outcome_path']=os.environ['K1LAB_NATIVE_OUTCOME_PATH']
        if os.environ.get('K1LAB_SIM_PORT'):self.config['sim_port']=int(os.environ['K1LAB_SIM_PORT'])
        config=self.config
        self.poisoned=False;self._done=False;self._success=False;self._step=0
        self._last_action=None;self.source=None;self.runtime_fingerprint=config.get('runtime_fingerprint',{})
        self.allow_eef_policy=bool(config.get('allow_xiaomi_eef_via_dls',False))
        if rpc is None:
            root=check_checkout(config['gpt_as_policy_root'],REV);sys.path.insert(0,str(root))
            from hybrid_rollout.robodojo.robodojo_server.protocol import RPCClient
            rpc=RPCClient('127.0.0.1',int(config.get('sim_port',19113)),timeout=float(config.get('timeout_s',600)))
        self.rpc=rpc;self.meta=rpc.request('metadata')
        self.horizon=int(self.meta['max_episode_steps']);self.hz=1/float(self.meta['control_dt'])
        if self.meta['action_dim']!=14 or self.meta.get('frame')!='environment_origin':
            raise ContractError('wrong RoboDojo native profile')
        self.episode=None

    def _call(self, op, **kw):
        if self.poisoned:raise TransportUncertain('RoboDojo connection poisoned; do not retry mutation')
        try:return self.rpc.request(op,episode_id=self.episode,step_id=self._step,**kw)
        except Exception as e:
            self.poisoned=True
            raise TransportUncertain(f'RoboDojo {op} unresolved; no reset or retry in this episode') from e

    def _observe(self):
        raw=self._call('teacher_observation')
        state=np.asarray(raw['states'],np.float32)
        eef={}
        for i,arm in enumerate(('left','right')):
            q=np.asarray(raw['eef_quaternions_wxyz'][i])
            eef[arm]={'xyz':np.asarray(raw['eef_positions'][i]).tolist(),'quaternion_xyzw':q[[1,2,3,0]].tolist(),
                      'gripper_opening_command':float(state[7*i+6]),
                      'gripper_is_measurement':False}
        # Identity-bearing state is robot-only; no scene object transforms or score queries.
        self.obs=Observation(self.episode,self._step,str(raw['instruction']),
                             {c:np.asarray(raw[c],np.uint8) for c in CAMERAS},state,eef,self.hz,native=raw)
        return self.obs

    def reset(self, case):
        if self.episode is not None:raise ContractError('one episode per server; no rollback')
        if self.meta['task']!=case.get('runtime_task',case['task']):raise ContractError('server task mismatch')
        reset=self.rpc.request('reset',seed=int(case['layout_id']),source='student',policy_version='multibench-explicit')
        self.episode=reset['episode_id'];self._step=int(reset['step_id'])
        meta=reset.get('metadata',{})
        if case.get('eval_seed') is not None and meta.get('eval_seed')!=case['eval_seed']:
            raise ContractError('layout GROUP eval_seed mismatch (different from layout_id)')
        declared=meta.get('evaluation_case') or {}
        if case.get('layout_sha256') and declared.get('layout_sha256')!=case['layout_sha256']:
            raise ContractError('launch source server with frozen evaluation case and matching layout hash')
        try:
            from hybrid_rollout.robodojo.prompt_context import task_context
            self.public_task_requirements=task_context(case.get('runtime_task',case['task']))
        except ImportError:self.public_task_requirements={}
        self._call('begin_combination',teacher_model=self.config.get('model','gpt-6.1-sol'),
                   evaluation_method='multibench_independent',training_steps=0,
                   task_memory=False,controller_variant='x5_eef_via_dls' if self.allow_eef_policy else 'joint_native_dls_corrections')
        return self._observe()

    @staticmethod
    def targets(action):
        a=action.values
        return {arm:{'position':a[o:o+3].tolist(),'quaternion_wxyz':(a[o+3:o+7]/np.linalg.norm(a[o+3:o+7])).tolist(),
                     'gripper_closed':bool(a[o+7] < .5), 'gripper_opening':float(a[o+7])}
                for arm,o in (('left',0),('right',8))}

    def step(self, action, correction=False):
        if self._done:raise ContractError('cannot step after terminal')
        source='gpt_eef' if correction else 'student'
        if self.source!=source:
            self._call('switch_control_source',source=source,reason='bounded matched experiment');self.source=source
        if action.space=='x5_joint14':
            if correction:raise ContractError('reviewer cannot emit joint actions')
            command=action.values
        elif action.space=='x5_eef16_wxyz':
            if not correction and not self.allow_eef_policy:
                raise Unavailable('Xiaomi EEF -> DLS controller variant requires explicit qualification/opt-in')
            proposal=self._call('eef_joint_target',targets=self.targets(action))
            command=np.asarray(proposal['action'],np.float32)
        else:raise ContractError('incompatible RoboDojo action convention')
        result=self._call('chunk_step',actions=np.asarray([command],np.float32))
        rows=result['steps']
        if len(rows)!=1 or rows[0].get('valid') is not True:raise ContractError('one valid native ACK required')
        row=rows[0]
        if result['episode_id']!=self.episode or result['step_id']!=self._step+1:
            self.poisoned=True;raise ContractError('native ACK counters differ')
        self._step=result['step_id'];self._done=bool(row['terminated'] or row['truncated'])
        self._success=bool(row['success']);self._last_action=action
        obs=self._observe()
        return StepResult(obs,self._done and not bool(row['truncated']),self._success,bool(row['truncated']))

    def correction_reached(self,action):
        if action.space!='x5_eef16_wxyz':return False
        for arm,o in (('left',0),('right',8)):
            p=self.obs.eef[arm]
            if np.linalg.norm(np.asarray(p['xyz'])-action.values[o:o+3])>.003:return False
            target=Rotation.from_quat(action.values[o+3:o+7][[1,2,3,0]])
            if (target*Rotation.from_quat(p['quaternion_xyzw']).inv()).magnitude()>.035:return False
            # Opening is a command, not physical closure. Do not early-stop while changing it.
            if abs(p['gripper_opening_command']-float(action.values[o+7]))>.01:return False
        return True

    def preview(self,proposal):
        if proposal.actions[0].space=='x5_joint14':
            # Upstream FK accepts exactly H50. Evaluate arbitrary actual horizons
            # in blocks, padding only the *robot kinematics request* with repeats
            # of its final existing joint target. Drop all padding from the reply.
            # Policy commands, execution horizons, and recurrent ACKs are untouched.
            values=np.stack([a.values for a in proposal.actions])
            trajectory=[];checks=[]
            for begin in range(0,len(values),50):
                block=values[begin:begin+50]; n=len(block)
                padded=np.concatenate([block,np.repeat(block[-1:],50-n,axis=0)])
                data=self._call('fk_preview',actions=padded)
                part=data.get('trajectory',[])
                if len(part)!=50:raise ContractError('source H50 robot FK response malformed')
                for i,item in enumerate(part[:n]):trajectory.append(dict(item,index=begin+i))
                checks.append(data.get('measured_fk_check'))
            indices=np.unique(np.linspace(0,len(trajectory)-1,min(8,len(trajectory))).astype(int))
            return {'sampled_robot_fk':[trajectory[i] for i in indices],
                    'measured_fk_checks':checks,'not_contact_simulation':True,
                    'fk_compatibility':{'source_request_horizon':50,'actual_policy_horizon':len(values),
                     'padding':'repeat final target for FK input only; padded outputs discarded; zero physics steps'}}
        return {'native_eef_proposal':True,'not_contact_simulation':True}

    def finish(self,reason):
        if self.episode is None or self.poisoned:return {'success':False,'score':None}
        result=self._call('finish_pilot',reason=reason)
        score=None
        # Optional shared source recorder file: evaluate AFTER finish; never before decisions.
        path=self.config.get('native_outcome_path')
        if path and Path(path).is_file():
            summary=Path(path).with_name('summary.json')
            if not summary.is_file() or load_json(summary).get('episode_id')!=self.episode:
                raise ContractError('native outcome is not bound to this episode')
            native=load_json(path)
            if native.get('valid_for_success_rate'):score=native.get('native_score')
        return {'success':bool(result['success']),'score':score}

    def describe(self):
        return {'benchmark':'robodojo','source_revision':REV,'control_hz':self.hz,
                'horizon':self.horizon,'depth':False,'object_state_to_actor':False,
                'controller':'native joint targets + robot-only DLS',
                'xiaomi_eef_via_dls_variant':self.allow_eef_policy,'metadata':self.meta}
    def close(self):self.rpc.close()
