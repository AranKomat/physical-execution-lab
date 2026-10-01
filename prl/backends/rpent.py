"""Source-inspected RPent LIBERO integration; requires native GPU qualification.

Pinned contract: RLinf/RPent d2595ff270c7d66dbb2effb803f5e6d4d8e08f82.
Uses upstream LiberoEnvClient, Pi05VLAClient and LiberoPrimitives. No model, RPC
service or simulator is started by importing this module. Only a newly owned
simulator is used; there is intentionally no real-hardware backend.
"""
from __future__ import annotations
import argparse
import os
import sys
import subprocess
from pathlib import Path
from ..contracts import Observation, Target
from ..errors import Unavailable, ValidationError, UncertainExecution, Interrupted
from ..util import plain, atomic_json, file_digest, digest, norm, sub

RPENT_REV='d2595ff270c7d66dbb2effb803f5e6d4d8e08f82'


def load_rpent(path):
    root=Path(path).expanduser().resolve()
    if not (root/'robots/libero/tools.py').is_file():
        raise Unavailable('RPent checkout missing; run scripts/bootstrap.py with network access')
    try:
        rev=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
    except (OSError,subprocess.CalledProcessError) as e:
        raise Unavailable('RPent must be a pinned git checkout') from e
    if rev!=RPENT_REV: raise ValidationError(f'RPent revision mismatch: {rev}')
    dirty=subprocess.check_output(['git','-C',str(root),'status','--porcelain','--untracked-files=no'],text=True)
    if dirty.strip(): raise ValidationError('RPent tracked source is modified; record a new reviewed pin')
    sys.path.insert(0,str(root))
    os.environ['PYTHONPATH']=str(root)+os.pathsep+os.environ.get('PYTHONPATH','')
    return root


def state_fingerprint(state):
    import numpy as np
    a=np.ascontiguousarray(state.detach().cpu().numpy() if hasattr(state,'detach') else state)
    import hashlib
    return digest({'dtype':str(a.dtype),'shape':list(a.shape),'bytes_sha256':hashlib.sha256(a.tobytes()).hexdigest()})


def catalog_states(rpent_root,suites):
    load_rpent(rpent_root)
    os.environ['LIBERO_TYPE']='pro'
    import rlinf.envs.sim.libero.libero_env  # install pro aliases and repair stale benchmark paths
    from rlinf.envs.sim.libero.utils import benchmark
    out={}
    for name in suites:
        suite=benchmark.get_benchmark(name)()
        n=getattr(suite,'n_tasks',None)
        if n is None: n=len(suite.tasks)
        out[name]={}
        for task in range(n):
            states=suite.get_task_init_states(task)
            out[name][str(task)]=[state_fingerprint(s) for s in states]
    return out


class CheckedEnv:
    """Interposes on EACH action. Never submit a full uninterruptible VLA chunk.

    This changes RPC overhead versus upstream chunk_step; both nominal and dynamic
    use this same wrapper. Benchmark physical time and wall time separately.
    """
    def __init__(self,env,owner):
        self.inner,self.owner=env,owner
        self.return_all_frames=True
        self.last_obs=None
    @property
    def terminated(self): return self.inner.terminated
    @property
    def truncated(self): return self.inner.truncated
    def reset(self):
        if self.last_obs is not None: raise ValidationError('same_episode_reset_forbidden')
        # Native BaseEnvClient resets once while connecting to the newly owned
        # environment. Reuse that initial observation instead of resetting twice.
        initial=getattr(self.inner,'last_obs',None)
        if isinstance(initial,dict):
            self.last_obs=initial
            return initial,{}
        obs,info=self.inner.reset(); self.last_obs=obs
        return obs,info
    def raw_obs(self): return self.inner.raw_obs()
    def get_camera_meta(self,*a,**kw): return self.inner.get_camera_meta(*a,**kw)
    def render_camera(self,*a,**kw): return self.inner.render_camera(*a,**kw)
    def get_task_language(self): return self.inner.get_task_language()
    def step(self,action):
        a=plain(action)
        self.owner.before(a)
        try:
            obs,reward,term,trunc,info=self.inner.step(action)
        except Exception as e:
            # A connection failure could occur AFTER simulation advanced.
            raise UncertainExecution('RPent step returned no authoritative receipt; no retry') from e
        self.last_obs=obs
        self.owner.steps+=1
        record=getattr(self.owner,'record_step',None)
        if record is not None: record(obs)
        self.owner.native_success=bool(self.inner.terminated)
        self.owner.native_truncated=bool(self.inner.truncated)
        self.owner.after(self.owner.observe(),a)
        return obs,reward,term,trunc,info
    def chunk_step(self,actions,*,return_all_frames=None):
        import numpy as np
        arr=np.asarray(actions)
        if arr.ndim!=2 or arr.shape[1]!=7 or not 1<=len(arr)<=1024:
            raise ValidationError(f'Unexpected policy action chunk shape: {arr.shape}')
        obs_list=[]; rewards=[]; terms=[]; truncs=[]; info={}
        for action in arr:
            obs,r,t,tr,info=self.step(action)
            obs_list.append(obs); rewards.append(r); terms.append(t); truncs.append(tr)
            if self.terminated or self.truncated: break
        return (obs_list if return_all_frames is not False else obs_list[-1],
                np.asarray(rewards),np.asarray(terms),np.asarray(truncs),info)


class MeteredPolicy:
    def __init__(self,inner,owner): self.inner,self.owner=inner,owner
    def predict(self,*args,**kwargs):
        self.owner.before_vla()
        if self.inner is None: raise Unavailable('Frozen policy service not enabled')
        return self.inner.predict(*args,**kwargs)


class RPentBackend:
    def __init__(self,case,output_dir,config):
        self.case,self.output_dir,self.config=case,Path(output_dir),config
        self.source=config.get('information_profile','sensor')
        if self.source not in ('sensor','privileged_sim'):
            raise ValidationError('Native information profile must be sensor or privileged_sim')
        if not config.get('allow_native'):
            raise Unavailable('Native simulator launch requires --allow-native')
        if config.get('control_hz',20)!=20:
            raise ValidationError('RPent adapter is qualified only for the declared 20 Hz contract')
        if not (3,10)<=sys.version_info[:2]<(3,13):
            raise Unavailable('Native RPent requires an isolated Python 3.10-3.12 environment')
        if config.get('enable_policy',True):
            h=config.get('checkpoint_sha256','')
            if len(h)!=64 or any(c not in '0123456789abcdef' for c in h):
                raise ValidationError('Record exact checkpoint file-manifest SHA256 before model evaluation')
            if not config.get('checkpoint_id') or config['checkpoint_id'].startswith('REPLACE'):
                raise ValidationError('Record exact checkpoint ID and revision')
        if config.get('mode')=='dynamic_k1':
            from ..geometry import load_k1
            load_k1(config.get('k1_root','external/k1'))
        self.root=load_rpent(config['rpent_root'])
        os.environ['LIBERO_TYPE']='pro'
        os.environ.setdefault('MUJOCO_GL','egl')
        os.environ.setdefault('PYOPENGL_PLATFORM','egl')
        from importlib.metadata import version
        if version('mujoco')!='3.3.0':
            raise ValidationError('This native profile pins mujoco==3.3.0; do not silently mix physics versions')
        self.steps=0; self.extra_targets={}; self.images=[]; self.cameras={}; self.capture_step=-1
        self.native_success=False; self.native_truncated=False; self.daemons=[]
        self.video_writer=None; self.video_frames=0; self.video_error=None
        self.before=lambda a: (_ for _ in ()).throw(Unavailable('No execution governor installed'))
        self.after=lambda o,a:None
        self.before_vla=lambda: (_ for _ in ()).throw(Unavailable('No VLA budget installed'))
        self._validate_case()
        from robots.libero.robot_spec import _init_runtime
        from rpent.dashboard.events import NullDashboardEventSink
        from robots.libero.tools import LiberoPrimitives
        args=argparse.Namespace(suite=case.suite,task=case.task_id,seed=case.state_index,
            max_episode_steps=config['max_steps'],libero_type='pro',
            cuda_device=config.get('cuda_device',0),env_endpoint=None,
            vla_endpoint=config.get('vla_endpoint'),sam3_endpoint=None,molmo_endpoint=None,
            planner='api',collect_flywheel_data=False,flywheel_root=None)
        components={'env','vla'} if config.get('enable_policy',True) else {'env'}
        self.daemons,kw=_init_runtime(args,self.output_dir,NullDashboardEventSink(),components)
        try:
            self.env=CheckedEnv(kw['env'],self)
            self.policy=MeteredPolicy(kw.get('model'),self)
            self.primitives=LiberoPrimitives(env=self.env,model=self.policy,sam3_client=None,
                                             check_cancelled=lambda:None)
            self.primitives.reset()
            self.task=self.env.get_task_language() or str(self.env.last_obs.get('task_descriptions',''))
            self.metadata={'backend':'rpent_libero','rpent_revision':RPENT_REV,
                'information_profile':self.source,'physics':'MuJoCo (native unqualified here)',
                'control_hz':config.get('control_hz',20),'state_sha256':case.state_sha256,
                'state_index':case.state_index,'env_seed_used':case.state_index,
                'policy_rng_control':'not_exposed_by_this_adapter',
                'policy_checkpoint':config.get('checkpoint_id','UNSPECIFIED'),
                'checkpoint_sha256':config.get('checkpoint_sha256','UNSPECIFIED'),
                'capabilities':'independent PRL compositions over RPent; not DynaHarness exact'}
            self.capture()
            if config.get('record_video',False):
                try:
                    import imageio.v2 as imageio
                    self.video_writer=imageio.get_writer(str(self.output_dir/'native_policy_view.mp4'),fps=20)
                except Exception as e:
                    self.video_error=type(e).__name__+': '+str(e)
        except BaseException:
            self.close(); raise

    def _validate_case(self):
        from rlinf.envs.sim.libero.utils import benchmark
        suite=benchmark.get_benchmark(self.case.suite)()
        states=suite.get_task_init_states(self.case.task_id)
        if not 0<=self.case.state_index<len(states):
            # Upstream seed % trials would silently alias. Reject instead.
            raise ValidationError('state_index_out_of_range: modulo resets forbidden')
        if state_fingerprint(states[self.case.state_index])!=self.case.state_sha256:
            raise ValidationError('initial_state_hash_mismatch')

    def set_hooks(self,before,after,before_vla):
        self.before,self.after,self.before_vla=before,after,before_vla

    def observe(self):
        import numpy as np
        obs=self.env.last_obs
        s=np.asarray(obs['states']).reshape(-1)
        if len(s)<8: raise ValidationError('Unqualified RPent state layout')
        targets=dict(self.extra_targets)
        if self.source=='privileged_sim':
            raw=self.env.raw_obs()
            for k,v in raw.items():
                if k.endswith('_pos') and 'robot0' not in k and 'to_robot' not in k:
                    a=np.asarray(v).reshape(-1)
                    if len(a)==3:
                        key=k[:-4]
                        targets[key]=Target(key,tuple(float(x) for x in a),'privileged_sim',
                            'simulator_object_origin',self.steps,uncertainty_m=0,
                            evidence_id=f'privileged:{self.steps}:{key}')
        return Observation(self.case.case_id,self.steps,self.steps,getattr(self,'task',''),
                           tuple(float(x) for x in s[:3]),float(abs(s[6])+abs(s[7])),
                           self.source,targets,list(self.images),{})

    def capture(self):
        import numpy as np
        from PIL import Image
        from ..geometry import rpent_camera
        if self.capture_step==self.steps: return self.observe()
        raw=self.env.raw_obs()
        images=[]; cameras={}
        for name,label in [('agentview','agentview'),('robot0_eye_in_hand','wrist')]:
            rgb,depth=raw.get(name+'_image'),raw.get(name+'_depth')
            if rgb is None or depth is None: continue
            h,w=np.asarray(rgb).shape[:2]
            meta=self.env.get_camera_meta(camera_name=name,height=int(h),width=int(w))
            if meta is None: raise Unavailable('Missing native camera calibration')
            cam=rpent_camera(rgb,depth,meta)
            base=self.output_dir/'observations'/f'{self.steps:06d}_{label}'
            base.parent.mkdir(parents=True,exist_ok=True)
            image=base.with_suffix('.png'); Image.fromarray(cam['rgb'].astype('uint8')).save(image)
            np.savez_compressed(base.with_suffix('.npz'),depth=cam['depth'],
                intrinsic_matrix=cam['intrinsic_matrix'],extrinsic_matrix=cam['extrinsic_matrix'])
            atomic_json(base.with_suffix('.json'),{'camera':label,'sim_step':self.steps,
                'observation_id':self.observe().observation_id,'source':'sensor',
                'coordinate_frame':'OpenCV optical camera-to-world',
                'pixel_mapping':'vertically flipped native RGB AND depth, matching RPent calibration',
                'image_sha256':file_digest(image),'depth_sha256':file_digest(base.with_suffix('.npz'))})
            images.append({'camera':label,'path':str(image.resolve()),'width':w,'height':h,
                           'observation_id':self.observe().observation_id,
                           'sha256':file_digest(image),'source':'sensor'})
            cameras[label]=cam
        self.images,self.cameras,self.capture_step=images,cameras,self.steps
        return self.observe()

    def query(self,name,args,registry):
        self.capture()
        if name=='observe': return self.observe().actor_view()
        if args['observation_id']!=self.observe().observation_id:
            raise Unavailable('stale_image')
        if args['camera'] not in self.cameras: raise Unavailable('camera_unavailable')
        from ..geometry import measure_pixel,fit_geometry
        if name=='measure_pixel':
            result=measure_pixel(self.cameras[args['camera']],args['pixel'],
                args.get('coordinate_space','pixels'),engine='k1' if registry.k1 else 'builtin')
        elif name=='fit_geometry':
            result=fit_geometry(self.cameras[args['camera']],args['roi'],args['kind'])
        else: raise Unavailable(f'query_not_supported:{name}')
        key=f'measurement_{len(self.extra_targets)}'
        self.extra_targets[key]=Target(key,tuple(result['xyz_world_m']),'sensor',
            result['kind'],self.steps,uncertainty_m=None,evidence_id=f'{self.observe().observation_id}:{key}')
        result.update(target_id=key,observation_id=self.observe().observation_id,
                      uncertainty='unquantified',source='sensor')
        return result

    def execute_stage(self,stage):
        if self.native_success or self.native_truncated:
            raise ValidationError('No steps permitted after native termination')
        op,args=stage.operation,dict(stage.arguments)
        try:
            if op in ('vla','vla_pick'):
                instruction=args['instruction']
                start=self.steps
                while self.steps-start<stage.max_steps:
                    self.primitives._vlm_chunk(instruction)
                return {'executed':True,'policy':self.metadata['policy_checkpoint']}
            if op not in ('move_to','move_pose','rotate_wrist','release','set_gripper'):
                raise Unavailable(f'unsupported_rpent_stage:{op}')
            if op!='set_gripper': args['max_steps']=stage.max_steps
            return plain(getattr(self.primitives,op)(**args))
        finally:
            # Interrupts happen inside env.step before upstream primitives.set_obs.
            # Synchronize the policy state before any later recovery or replan.
            if self.env.last_obs is not None: self.primitives.set_obs(self.env.last_obs)

    def verify_effect(self,name,args):
        # Native benchmark success is latched separately. No fragile gripper-gap
        # or TCP-arrival heuristic is represented as object-level task success.
        return None

    def record_step(self,obs):
        if self.video_writer is None:return
        try:
            import numpy as np
            frame=np.asarray(obs['main_images'])
            if frame.ndim!=3 or frame.shape[-1]!=3:
                raise ValidationError('Unqualified native video frame shape')
            self.video_writer.append_data(frame.astype('uint8'))
            self.video_frames+=1
        except Exception as e:
            self.video_error=type(e).__name__+': '+str(e)
            try:self.video_writer.close()
            except Exception:pass
            self.video_writer=None

    def close(self):
        if self.video_writer is not None:
            try:self.video_writer.close()
            except Exception as e:self.video_error=type(e).__name__+': '+str(e)
            self.video_writer=None
        if self.config.get('record_video',False):
            atomic_json(self.output_dir/'video_manifest.json',{'frames':self.video_frames,
                'native_steps':self.steps,'fps':20,
                'frame_convention':'RPent policy-oriented main_images, NOT depth/calibration pixels',
                'error':self.video_error,
                'complete':self.video_frames==self.steps and self.video_error is None})
        # Stop only daemons created by this backend. Never stop a shared VLA server.
        errors=[]
        for daemon in reversed(self.daemons):
            try: daemon.stop(timeout=10)
            except Exception as e: errors.append(str(e))
        self.daemons=[]
        if errors and self.output_dir.exists(): atomic_json(self.output_dir/'cleanup_errors.json',errors)
