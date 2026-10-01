"""Direct LIBERO-PRO geometry/physics seam plus RPent's frozen-policy client.

Why a direct environment seam? RPent's standard RPC observation strips articulated
geometry and terminates immediately. The paper needs simulator geometry and an
independent predicate sampler/latch. We retain the pinned RPent/RLinf ecosystem
and VLA transport, but do not pass through the older sensor-only wrapper.

Native imports are lazy. This module was source-inspected and tested with doubles;
no native simulator or GPU executed on the build host.
"""
from pathlib import Path
import os
import sys
import math
import numpy as np
from scipy.spatial.transform import Rotation
from .scene import Scene,Entity,Articulation,v3
from ..errors import ValidationError,Unavailable,UncertainExecution
from ..util import atomic_json,file_digest,digest
from ..backends.rpent import load_rpent,state_fingerprint


def geom_vertices(sim,gid):
    """Physical geometry samples/bounds. Mesh vertices already carry mesh scale."""
    m,d=sim.model,sim.data
    typ=int(m.geom_type[gid]); size=np.asarray(m.geom_size[gid],float)
    if typ==7:
        mid=int(m.geom_dataid[gid]);start=int(m.mesh_vertadr[mid]);count=int(m.mesh_vertnum[mid])
        local=np.asarray(m.mesh_vert[start:start+count],float)
    else:
        if typ==2:ext=np.repeat(size[0],3)
        elif typ in (3,5):ext=np.array([size[0],size[0],size[1]+(size[0] if typ==3 else 0)])
        elif typ in (4,6):ext=size
        else:return np.empty((0,3))
        local=np.array([[x,y,z] for x in (-ext[0],ext[0]) for y in (-ext[1],ext[1]) for z in (-ext[2],ext[2])])
    return local @ np.asarray(d.geom_xmat[gid]).reshape(3,3).T + np.asarray(d.geom_xpos[gid])


def object_geometry(sim,obj,name,step,is_fixture):
    m,d=sim.model,sim.data
    root=m.body_name2id(obj.root_body)
    R=np.asarray(d.body_xmat[root]).reshape(3,3);center=np.asarray(d.body_xpos[root])
    gids=[];points=[]
    for gname in obj.contact_geoms:
        gid=m.geom_name2id(gname);gids.append(gid)
        p=geom_vertices(sim,gid)
        if len(p):points.append(p)
    if not points:raise Unavailable('no_physical_object_geometry:'+name)
    local=(np.concatenate(points)-center)@R
    lo,hi=local.min(0),local.max(0)
    e=Entity(name,tuple(center+R@((lo+hi)/2)),tuple((hi-lo)/2),
             tuple(Rotation.from_matrix(R).as_quat()),'fixture' if is_fixture else 'object',
             observed_step=step,attributes={'description':getattr(obj,'category_name',name),
                                           'geometry':'collision_geometry_bounds'})
    return e,gids,root


def scene_geometry(env,raw,episode_id,step,images=(),overrides=None):
    """Explicit simulator-state access. Never reads parsed goal or rewards."""
    core=env.env; sim=env.sim; m,d=sim.model,sim.data
    entities={};joints={};geoms={};roots={};warnings=[]
    for fixture,mapping in ((True,core.fixtures_dict),(False,core.objects_dict)):
        for name,obj in mapping.items():
            try:
                e,gids,root=object_geometry(sim,obj,name,step,fixture)
                entities[name]=e;geoms[name]=gids;roots[name]=root
            except (KeyError,ValueError,AttributeError,Unavailable) as e:
                warnings.append(f'{name}: {e}')
    for name,obj in core.object_sites_dict.items():
        try:
            sid=m.site_name2id(name)
            attrs={};kind='region';token=name.lower()
            if 'handle' in token or 'knob' in token:kind='handle'
            elif any(t in token for t in ('interior','inside','cavity','middle_region','top_region','bottom_region')):
                attrs['region_type']='cavity'
            elif any(t in token for t in ('receptacle','basket')):attrs['region_type']='receptacle'
            elif any(t in token for t in ('top_side','surface','table','cook_region','burner','hob')):
                attrs['region_type']='support'
            attrs['classification']='asset-site-name heuristic; explicit overrides permitted, not goal clauses'
            entities[name]=Entity(name,tuple(d.site_xpos[sid]),tuple(m.site_size[sid]),
                tuple(Rotation.from_matrix(np.asarray(d.site_xmat[sid]).reshape(3,3)).as_quat()),
                kind,getattr(obj,'parent_name',None),observed_step=step,attributes=attrs)
        except (KeyError,ValueError,AttributeError) as e:warnings.append(f'site {name}: {e}')
    # Fixed world tabletop may not be an entry in fixtures_dict. Its physical box
    # geometry is a valid scene affordance, not a benchmark goal-region oracle.
    for gid in range(int(m.ngeom)):
        name=m.geom_id2name(gid) or ''
        if name in ('table_collision','table_col'):
            pts=geom_vertices(sim,gid)
            if len(pts):
                lo,hi=pts.min(0),pts.max(0)
                entities['table_support']=Entity('table_support',tuple((lo+hi)/2),tuple((hi-lo)/2),
                    kind='fixture',observed_step=step,attributes={'region_type':'support'})
    def under(body,root):
        while body>0:
            if body==root:return True
            body=int(m.body_parentid[body])
        return body==root
    for jid in range(int(m.njnt)):
        typ=int(m.jnt_type[jid])
        if typ not in (2,3) or not m.jnt_limited[jid]:continue
        body=int(m.jnt_bodyid[jid]);parents=[n for n,r in roots.items() if under(body,r)]
        if len(parents)!=1:continue
        parent=parents[0]; name=m.joint_id2name(jid)
        handles=[e for e in entities.values() if e.kind=='handle' and (e.parent==parent or e.name.startswith(parent+'_'))]
        if not handles:continue
        pivot=np.asarray(d.xanchor[jid]);axis=np.asarray(d.xaxis[jid])
        # If several handles exist, do not silently bind the wrong drawer. Match
        # mechanism tokens first; unresolved mappings are refused downstream.
        jt=set(name.lower().split('_'))-set(parent.lower().split('_'))-{'joint'}
        matched=[e for e in handles if jt & set(e.name.lower().split('_'))]
        if len(matched)==1:handle=matched[0]
        elif len(handles)==1:handle=handles[0]
        else:
            warnings.append('ambiguous handle for '+name);continue
        lo,hi=map(float,m.jnt_range[jid]);q=float(d.qpos[int(m.jnt_qposadr[jid])])
        o=(overrides or {}).get('mechanisms',{}).get(name,{})
        # Endpoints are not always open/closed. This default must be physically
        # qualified; mechanism-specific configuration records its provenance.
        closed=o.get('closed_position',lo);opened=o.get('open_position',hi)
        joints[name]=Articulation(name,parent,handle.name,'slide' if typ==2 else 'hinge',
            tuple(pivot),tuple(axis),q,lo,hi,opened,closed,observed_step=step)
    # Optional physical asset annotations, frozen for all arms and hashes logged.
    # No task IDs, suite IDs, initial-state IDs or native goal text are accepted.
    from dataclasses import replace
    for name,attrs in (overrides or {}).get('entities',{}).items():
        if name in entities:entities[name]=replace(entities[name],attributes={**entities[name].attributes,**attrs})
    robot=core.robots[0];gripper=robot.gripper
    if isinstance(gripper,dict):
        if len(gripper)!=1:raise ValidationError('one_arm_gripper_required')
        gripper=next(iter(gripper.values()))
    important=gripper.important_geoms
    left=important.get('left_fingerpad',important.get('left_finger',[]))
    right=important.get('right_fingerpad',important.get('right_finger',[]))
    def ids(names):return {m.geom_name2id(n) for n in ([names] if isinstance(names,str) else names)}
    l,r=ids(left),ids(right);contact_pairs=[]
    for i in range(int(d.ncon)):
        c=d.contact[i];contact_pairs.append((int(c.geom1),int(c.geom2)))
    contacts={}
    for name,gids in geoms.items():
        gs=set(gids)
        hit=lambda finger:any((a in finger and b in gs) or (b in finger and a in gs) for a,b in contact_pairs)
        contacts[name]=(hit(l),hit(r))
    qvel=tuple(float(x) for x in np.asarray(d.qvel)[robot._ref_joint_vel_indexes])
    fingers=np.asarray(raw['robot0_gripper_qpos']).reshape(-1)
    scene=Scene(episode_id,step,env.language_instruction,entities,joints,
        tuple(raw['robot0_eef_pos']),tuple(raw['robot0_eef_quat']),float(np.abs(fingers).sum()),
        contacts,qvel,list(images),simulation_time=float(d.time))
    return scene,warnings


class NativeBackend:
    def __init__(self,case,out,config,settings):
        if not config.get('allow_native'):raise Unavailable('native_launch_needs_explicit_permission')
        if not (3,10)<=sys.version_info[:2]<(3,13):raise Unavailable('native_RPent_requires_Python_3.10_to_3.12')
        if config.get('information_profile')!='privileged_sim':
            raise ValidationError('paper_track_requires_disclosed_simulator_geometry')
        self.case=case;self.out=Path(out);self.config=config;self.settings=settings
        self.steps=0;self.images=[];self.env=None;self.policy=None;self.video=None
        self.guard=None;self._original_sim_step=None;self.capture_step=-1;self.substep_guard_calls=0
        self._scene_cache=None;self._scene_cache_step=-1
        self.source='native';self.overrides=config.get('geometry_overrides',{})
        forbidden=('suite','task_id','state_index','seed','goal_predicate')
        if any(k in str(self.overrides) for k in forbidden):raise ValidationError('task_keyed_geometry_overrides_forbidden')
        load_rpent(config['rpent_root'])
        os.environ['LIBERO_TYPE']='pro'
        os.environ.setdefault('MUJOCO_GL',config.get('mujoco_gl','egl'))
        os.environ.setdefault('PYOPENGL_PLATFORM',config.get('mujoco_gl','egl'))
        local_config=self.out/'libero-config';local_config.mkdir(parents=True,exist_ok=True)
        os.environ['LIBERO_CONFIG_PATH']=str(local_config.resolve())
        from importlib.metadata import version
        if version('mujoco')!='3.3.0':raise ValidationError('native_profile_requires_mujoco_3.3.0')
        # Import installs the upstream pro aliases. It is isolated to this process.
        import rlinf.envs.sim.libero.libero_env as routing
        import liberopro.liberopro as core
        from liberopro.liberopro.benchmark import get_benchmark
        from liberopro.liberopro.envs import OffScreenRenderEnv
        suite=get_benchmark(case.suite)();states=suite.get_task_init_states(case.task_id)
        if not 0<=case.state_index<len(states):raise ValidationError('no_modulo_initial_states')
        if state_fingerprint(states[case.state_index])!=case.state_sha256:
            raise ValidationError('initial_state_hash_mismatch')
        task=suite.get_task(case.task_id)
        bddl=Path(core.get_libero_path('bddl_files'))/task.problem_folder/task.bddl_file
        try:
            self.env=OffScreenRenderEnv(bddl_file_name=str(bddl),camera_heights=256,camera_widths=256,
                camera_depths=True,control_freq=settings.control_hz,horizon=10000,ignore_done=True,
                render_gpu_device_id=config.get('cuda_device',0),seed=case.state_index)
            self.env.seed(case.state_index)
            # The upstream wrapper retries randomization forever. Bound it here.
            from robosuite.utils.errors import RandomizationError
            for attempt in range(8):
                try:self.env.env.reset();break
                except RandomizationError:
                    if attempt==7:raise
            self.raw=self.env.set_init_state(np.asarray(states[case.state_index]))
            settle=config.get('settle_steps',10)
            for _ in range(settle):self.raw,_,_,_=self.env.step([0,0,0,0,0,0,-1])
            self.initial_sim_time=float(self.env.sim.data.time)
            self.post_reset_state_hash=state_fingerprint(self.env.get_sim_state())
            robot=self.env.robots[0]
            controllers=getattr(robot,'part_controllers',None)
            candidates=[c for c in (controllers or {}).values() if getattr(c,'control_dim',0)==6]
            self.controller=candidates[0] if len(candidates)==1 else getattr(robot,'controller',None)
            if self.controller is None or not hasattr(self.controller,'output_max'):
                raise Unavailable('unqualified_OSC_controller_mapping')
            self.output_max=np.broadcast_to(np.asarray(self.controller.output_max,float),(6,)).copy()
            self.output_min=np.broadcast_to(np.asarray(self.controller.output_min,float),(6,)).copy()
            if np.any(self.output_max<=0) or not np.allclose(self.output_min,-self.output_max):
                raise ValidationError('requires_symmetric_OSC_scaling')
            # Never convert a public-checkpoint label into proof of loaded weights.
            if settings.policy_enabled:
                att=Path(config['policy_attestation']);body=__import__('json').loads(att.read_text())
                if body.get('checkpoint_sha256')!=config.get('checkpoint_sha256'):
                    raise ValidationError('policy_attestation_hash_mismatch')
                if body.get('action_chunk')!=settings.policy_chunk_actions or body.get('config_name')!='pi05_libero':
                    raise ValidationError('policy_attestation_configuration_mismatch')
                from rpent.robots.components.pi05_vla_client import Pi05VLAClient
                from rpent.utils.rpc import make_rpc_client
                rpc=make_rpc_client(config['vla_endpoint'])
                live=rpc.call('vla.get_prl_attestation',timeout_s=30.0)
                if digest(live)!=digest(body):raise ValidationError('live_policy_service_attestation_mismatch')
                self.policy=Pi05VLAClient(rpc,embodiment='libero')
            self.metadata={'backend':'direct_LIBERO_PRO_plus_RPent_policy','information_profile':'privileged_sim',
                'geometry_access':'physical MuJoCo bodies/geoms/sites/joints/contacts; not goal clauses',
                'bddl_sha256':file_digest(bddl),'source_state_sha256':case.state_sha256,
                'post_reset_state_sha256':self.post_reset_state_hash,'settle_steps':settle,
                'settle_provenance':'reconstruction default; not specified in attached PDF',
                'mujoco_version':version('mujoco'),'robosuite_version':version('robosuite'),
                'OSC_output_max':self.output_max.tolist(),'override_hash':digest(self.overrides),
                'policy_checkpoint_sha256':config.get('checkpoint_sha256'),'policy_rng_control':'not_exposed',
                'policy_attestation':config.get('policy_attestation'),
                'policy_preset':body.get('preset') if settings.policy_enabled else None,
                'native_qualification':'required'}
            if config.get('record_video',False):
                import imageio.v2 as imageio
                self.video=imageio.get_writer(str(self.out/'native.mp4'),fps=settings.control_hz)
            self.capture()
        except BaseException:
            self.close();raise

    def scene(self):
        if self._scene_cache_step==self.steps and self._scene_cache is not None:
            self._scene_cache.images=list(self.images)
            return self._scene_cache
        scene,warnings=scene_geometry(self.env,self.raw,self.case.case_id,self.steps,self.images,self.overrides)
        self.geometry_warnings=warnings
        self._scene_cache,self._scene_cache_step=scene,self.steps
        return scene

    def safety_scene(self):
        # The physical watchdog needs current qdot/time, not expensive geometry
        # extraction at every substep. Geometry is refreshed at 20 Hz boundaries.
        from dataclasses import replace
        cached=self.scene()
        sim=self.env.sim;robot=self.env.robots[0]
        qdot=tuple(float(x) for x in np.asarray(sim.data.qvel)[robot._ref_joint_vel_indexes])
        return replace(cached,joint_velocity=qdot,simulation_time=float(sim.data.time))

    def capture(self):
        if self.capture_step==self.steps:return self.scene()
        from PIL import Image
        images=[]
        for key,name in (('agentview_image','agentview'),('robot0_eye_in_hand_image','wrist')):
            rgb=np.asarray(self.raw[key])[::-1].copy()
            p=self.out/'observations'/f'{self.steps:06d}_{name}.png';p.parent.mkdir(parents=True,exist_ok=True)
            Image.fromarray(rgb.astype('uint8')).save(p)
            images.append({'camera':name,'path':str(p.resolve()),'width':rgb.shape[1],'height':rgb.shape[0],
                'sha256':file_digest(p),'observation_id':f'{self.case.case_id}:0:0:{self.steps}'})
        self.images=images;self.capture_step=self.steps
        scene=self.scene()
        atomic_json(self.out/'geometry'/f'{self.steps:06d}.json',{'snapshot':scene,'warnings':self.geometry_warnings,
            'privileged_simulation_grounding':True})
        return scene

    def set_safety_check(self,guard,hz):
        self.guard=guard;self.next_guard=float(self.env.sim.data.time)
        sim=self.env.sim;self._original_sim_step=sim.step
        def wrapped_step(*args,**kwargs):
            now=float(sim.data.time)
            if now+1e-10>=self.next_guard:
                self.substep_guard_calls+=1
                guard(self.safety_scene());self.next_guard=now+1/hz
            return self._original_sim_step(*args,**kwargs)
        # If this simulator binding disallows interception, do not pretend a
        # per-action check implements the paper's 50 Hz physical envelope.
        try:sim.step=wrapped_step
        except Exception as e:raise Unavailable('cannot_install_physics_substep_safety_hook') from e

    def pose_action(self,xyz,quat,gripper):
        now=self.scene()
        trans=v3(xyz)-v3(now.eef_xyz)
        angle=(Rotation.from_quat(quat)*Rotation.from_quat(now.eef_quat).inv()).as_rotvec()
        # Limits are controller commands, not a certification of joint rates.
        if np.linalg.norm(angle)>0.09:angle*=0.09/np.linalg.norm(angle)
        normalized=np.r_[trans,angle]/self.output_max
        return np.r_[np.clip(normalized,-1,1),float(gripper)]

    def step(self,action):
        a=np.asarray(action,float)
        if a.shape!=(7,) or not np.isfinite(a).all() or np.any(abs(a)>1.00001):
            raise ValidationError('invalid_native_action')
        before_guards=self.substep_guard_calls
        try:self.raw,_,_,_=self.env.step(a)
        except Exception:
            # A safety stop may happen after some physics substeps. Native
            # qualification must inspect this; never reset/replay automatically.
            atomic_json(self.out/'PARTIAL_CONTROL_STEP.json',{'completed_actions':self.steps,
                'simulator_time':float(self.env.sim.data.time),'result':'interrupted_native_step'})
            raise UncertainExecution('partial_native_control_step_requires_reconciliation')
        self.steps+=1
        if self.guard and self.substep_guard_calls==before_guards:
            raise Unavailable('simulator_bypassed_physics_substep_safety_hook')
        if self.video is not None:self.video.append_data(np.asarray(self.raw['agentview_image'])[::-1])
        # This is the ONE native Boolean query. Scene extraction never calls it.
        verdict=bool(self.env.check_success())
        return self.scene(),verdict

    def policy_actions(self,instruction):
        if self.policy is None:raise Unavailable('frozen_policy_not_loaded')
        from rlinf.envs.sim.libero.utils import get_libero_image,get_libero_wrist_image,quat2axisangle
        obs={'main_images':get_libero_image(self.raw),'wrist_images':get_libero_wrist_image(self.raw),
             'extra_view_images':None,'states':np.r_[self.raw['robot0_eef_pos'],
              quat2axisangle(np.asarray(self.raw['robot0_eef_quat']).copy()),self.raw['robot0_gripper_qpos']],
             'task_descriptions':instruction}
        return self.policy.predict(obs,options={'mode':'eval'})

    def save_failure_state(self,path):
        p=Path(path);p.mkdir(parents=True,exist_ok=True)
        np.savez_compressed(p/'physics.npz',state=self.env.get_sim_state())
        atomic_json(p/'metadata.json',{'episode_id':self.case.case_id,'step':self.steps,
            'state_sha256':file_digest(p/'physics.npz'),
            'probe_only':True,'portable_resume':False,
            'missing':'controller integrators, action-chunk cursor, RNG and full governor state; do not advertise exact replay'})

    def close(self):
        if self.video is not None:self.video.close();self.video=None
        if self.env is not None:
            if self._original_sim_step is not None:self.env.sim.step=self._original_sim_step
            self.env.close();self.env=None
