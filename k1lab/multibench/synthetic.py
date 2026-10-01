"""Offline wiring exercise. No learned model, collision physics or benchmark claim."""
from __future__ import annotations
from pathlib import Path
import numpy as np
from .types import Observation,Action,Proposal,PolicyIdentity,StepResult
from .actor import Decision
from .runner import run_episode
from .report import render
from k1lab.util import atomic_json


class ToyEnv:
    evidence_kind='synthetic'
    correction_space='x5_eef16_wxyz'
    pose_frame='synthetic_metres'
    runtime_fingerprint={'backend':'toy_cpu_no_physics'}
    def __init__(self,horizon=36,stall=False):
        self.horizon=horizon;self.n=0;self.xyz=np.array([0.,0.,.3]);self.stall=stall;self.episode='toy';self.done=False
    def observation(self):
        rgb=np.zeros((24,32,3),np.uint8);rgb[10:14,min(28,int(self.xyz[0]*100)):min(28,int(self.xyz[0]*100))+3]=180
        state=np.zeros(14,np.float32);state[0]=self.xyz[0];state[[6,13]]=1
        return Observation(self.episode,self.n,'Move the synthetic robot. This is not a benchmark task.',
            {k:rgb.copy() for k in ('cam_high','cam_left_wrist','cam_right_wrist')},state,
            {a:{'xyz':self.xyz.tolist(),'quaternion_xyzw':[0,0,0,1],'gripper_opening_command':1.}
             for a in ('left','right')},25.)
    def reset(self,case):self.episode=case['case_id'];return self.observation()
    def step(self,action,correction=False):
        self.n+=1
        if not self.stall:self.xyz[0]+=.006
        self.done=self.n>=self.horizon
        success=self.done and not self.stall
        return StepResult(self.observation(),success,success,self.done and not success,float(success))
    def preview(self,p):return {'kind':'synthetic_robot_only'}
    def finish(self,r):return {'success':self.done and not self.stall,'score':float(self.done and not self.stall)}
    def close(self):pass
    def describe(self):return {'benchmark':'synthetic','horizon':self.horizon,'control_hz':25.,'physics':False}


class ToyPolicy:
    def __init__(self,prefix=6):
        self.identity=PolicyIdentity('toy','0'*64,'toy-v1','x5_joint14','none; scripted fixture',25.,prefix,'toy-no-sensors',prefix,True)
        self.pending=0;self.last=None;self.acks=0;self.resets=0
    def reset(self):self.pending=0;self.last=None;self.resets+=1
    def observe(self,obs):
        if self.last==obs.stamp:return
        if self.pending:self.pending-=1;self.acks+=1
        self.last=obs.stamp
    def propose(self,obs):
        if self.pending:raise RuntimeError('unacknowledged fixture actions')
        self.observe(obs);self.pending=self.identity.execute_steps
        a=obs.state.copy();a[0]+=.006
        return Proposal(obs.stamp,obs.step,self.identity.identity,[Action('x5_joint14',a.copy()) for _ in range(self.pending)])
    def invalidate(self,r):self.reset()
    def synchronize(self):pass
    def memory(self):return {'fixture':True}
    def close(self):pass


class ToyReviewer:
    def reset(self):pass
    def review(self,obs,proposal,reasons,receipt,contract,direct=False):
        if direct:
            values=[]
            for arm in ('left','right'):
                values.extend(np.asarray(obs.eef[arm]['xyz'])+[.02,0,0]);values.extend([1,0,0,0]);values.append(1.)
            return Decision('correct',contract['max_decision_steps'],[Action('x5_eef16_wxyz',values)],
                'progressing','aligned','Authored fixture action, no LLM.',{'completed_claims':[],'currently_attempting':'fixture','uncertain_or_invalidated':[]})
        return Decision('accept',min(len(proposal.actions),contract['max_decision_steps']),[],
                        'progressing','aligned','Authored fixture acceptance, no LLM.',{'completed_claims':[],'currently_attempting':'fixture','uncertain_or_invalidated':[]})
    def close(self):pass


def run(output):
    root=Path(output);root.mkdir(parents=True,exist_ok=False)
    cases=[{'case_id':f'toy_{i}','task':f'toy_task_{i}','task_group':f'toy_task_{i}',
            'benchmark':'synthetic','partition':'dev','stall':i==2} for i in range(3)]
    results=[]
    for mode in ('motor_only','review_every_chunk','sparse','direct_dense','direct_sparse'):
        for c in cases:
            direct=mode.startswith('direct')
            cfg={'name':mode,'mode':mode,'model':{'model':'SCRIPTED_NOT_LLM'},'max_decision_steps':5 if mode=='direct_dense' else 12 if direct else 6,
                 'max_correction_steps':12,'max_reviews':100,'monitor':{'max_unreviewed_steps':18,'max_unreviewed_chunks':3,'stall_window':12},'wall_limit_s':60}
            results.append(run_episode(ToyEnv(stall=c['stall']),None if direct else ToyPolicy(),
                None if mode=='motor_only' else ToyReviewer(),c,cfg,root/mode/c['case_id']))
    atomic_json(root/'cases.json',cases);render(cases,results,root)
    return {'episodes':len(results),'evidence_kind':'synthetic','report':str(root/'report.html')}
