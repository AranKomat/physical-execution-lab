"""Source-inspected LIBERO K1 extension; NOT native-qualified on the build host.

K1 requires its documented RoboSuite 1.4 environment. RPent model serving runs
in another process/environment. Never install RPent's 1.5 simulator into this one.
"""
from __future__ import annotations
import os
import time
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from .errors import ContractError,Unavailable
from .util import digest,array_sha,vector
from .policy import pack_array
from .sources import load_k1,checked_checkout,LIBERO_REV

POLICY_CONTRACT={'cameras':('agentview','robot0_eye_in_hand'),'state_dim':8,
                 'observation_convention':'rpent_pi05_libero_rgb180_256_eef_axisangle_gripper2'}


def make_adapter(config,case,journal=None):
    if not config.get('trust_local_state_archives'):raise Unavailable('must explicitly trust official/local pickle-based state archives')
    root=checked_checkout(config['libero_root'],LIBERO_REV,'libero/libero/__init__.py')
    os.environ['LIBERO_ROOT']=str(root)
    os.environ['LIBERO_CONFIG_PATH']=str(Path(config['libero_config']).resolve())
    os.environ.setdefault('MUJOCO_GL','egl')
    load_k1(config['k1_root'])
    from robo_harness.libero_adapter import LiberoAdapter
    from .manifests import check_case
    class MeasuredAdapter(LiberoAdapter):
        action_space='libero_normalized_osc7'
        policy_contract=POLICY_CONTRACT
        def __init__(self,*a,**kw):
            self.success_latch=False;self.observe_seconds=0.0;self.observe_calls=0;self.motion_seconds=0.0
            super().__init__(*a,**kw)
        def reset(self,*a,**kw):
            self.success_latch=False
            obs=super().reset(*a,**kw)
            self.success_latch=bool(self.env.check_success())
            return obs
        def success(self):
            # Same terminal capture in ALL arms; not advertised as our treatment gain.
            self.success_latch=self.success_latch or bool(self.env.check_success())
            return self.success_latch
        def observe(self):
            start=time.perf_counter()
            obs=super().observe();self.observe_seconds+=time.perf_counter()-start;self.observe_calls+=1
            return obs
        def _servo_absolute(self,*a,**kw):
            start=time.perf_counter()
            try:return super()._servo_absolute(*a,**kw)
            finally:self.motion_seconds+=time.perf_counter()-start
        def execute_native_action7(self,action):
            if self.frame>=self.horizon or self.success():return
            a=vector(action,7,'normalized OSC action')
            if np.any(np.abs(a)>1.000001):raise ContractError('OSC bounds violated; refusing, not clipping')
            self.gripper=float((1-a[6])/2)
            start=time.perf_counter()
            self.raw,*_=self.env.step(a);self.frame+=1
            if self.on_step:self.on_step(self.observe(),a)
            self.success();self.motion_seconds+=time.perf_counter()-start
        def policy_observation(self,subgoal):
            import cv2
            images={}
            for name in self.cameras:
                # K1 display = vertical flip; RPent policy = vertical+horizontal flip.
                rgb=np.asarray(self.raw[name+'_image'],dtype=np.uint8)[::-1,::-1].copy()
                images[name]=pack_array(cv2.resize(rgb,(256,256),interpolation=cv2.INTER_AREA))
            state=np.r_[self.raw['robot0_eef_pos'],
                        Rotation.from_quat(self.raw['robot0_eef_quat']).as_rotvec(),
                        self.raw['robot0_gripper_qpos']].astype(np.float32)
            if state.shape!=(8,):raise ContractError('unexpected proprioception for pi05 encoder')
            return {'frame_id':self.frame,'subgoal':subgoal,'images':images,'state':pack_array(state),
                    'contract':dict(POLICY_CONTRACT),
                    'note':'Resize from shared actor resolution, not a separately rendered policy camera. Native qualification required.'}
    adapter=MeasuredAdapter(suite=case['suite'],task_id=case['task_id'],resolution=config.get('resolution',384),
                horizon=case['horizon'],instruction_source='environment',delta_axis=config.get('delta_axis',0.03))
    try:
        check_case(adapter,case)
        obs=adapter.reset(case['state_index'])
        if adapter.success():raise ContractError('initial state already satisfies success; audit state bank')
        if journal:
            def capture(observation,action):
                journal.append('native_step',{'frame_id':observation['frame_id'],'action':action,
                    'arms':observation['arms'],'native_success_stop':adapter.success()})
            adapter.on_step=capture
        return adapter
    except BaseException:
        adapter.close();raise
