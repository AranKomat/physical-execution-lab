"""Bounded simulator controller checks, not task solutions or safety certification."""
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from k1lab.errors import ContractError
from k1lab.util import atomic_json
from .types import Action
from .transport import encode_obs


def measured_target(obs):
    values=[]
    for arm in ('left','right'):
        pose=obs.eef[arm]
        q=np.asarray(pose['quaternion_xyzw'])
        values.extend([*pose['xyz'],*q[[3,0,1,2]],pose['gripper_opening_command']])
    return Action('x5_eef16_wxyz',values)


def pose_errors(obs,target):
    errors={}
    for arm,off in (('left',0),('right',8)):
        pose=obs.eef[arm]
        q=target.values[off+3:off+7][[1,2,3,0]]
        errors[arm]={'translation_m':float(np.linalg.norm(target.values[off:off+3]-pose['xyz'])),
            'rotation_rad':float((Rotation.from_quat(q)*Rotation.from_quat(pose['quaternion_xyzw']).inv()).magnitude()),
            'opening_command_error':abs(float(target.values[off+7])-pose['gripper_opening_command'])}
    return errors


def probe_eef(native,obs,output):
    """At most 80 ACKs: hold, separate 20 mm upward targets, then return."""
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    start=measured_target(obs);left=start.values.copy();left[2]+=.02
    both=left.copy();both[10]+=.02
    phases=[('hold',start,5),('left_up',Action(start.space,left),25),
            ('right_up',Action(start.space,both),25),('return',start,25)]
    report={'schema':'multibench.eef_probe.v1','episode':obs.episode,
        'scope':'development robot-only translation/hold check; not task success or contact qualification',
        'external_clearance':'unknown; simulator-only exploratory motion',
        'paid_calls':0,'max_actions':80,'phases':[],'passed':False}
    initial=obs.step
    try:
        for name,target,count in phases:
            atomic_json(out/(name+'-before.wire.json'),encode_obs(obs),exclusive=True)
            row={'name':name,'target':target.json(),'before':pose_errors(obs,target),'steps':0}
            report['phases'].append(row)
            for _ in range(count):
                result=native.step(target,correction=True);obs=result.observation
                row['steps']+=1
                if obs.step!=initial+sum(p['steps'] for p in report['phases']):
                    raise ContractError('calibration ACK counter mismatch')
                atomic_json(out/f'ack-{obs.step:06d}.json',
                    {'step':obs.step,'actor_state':obs.actor_state(),'target':target.json()},exclusive=True)
                if result.terminated or result.truncated:
                    raise ContractError('native episode ended during calibration')
            row['after']=pose_errors(obs,target)
            row['reached']=native.correction_reached(target)
            atomic_json(out/(name+'-after.wire.json'),encode_obs(obs),exclusive=True)
        report['passed']=all(p['reached'] for p in report['phases'])
    except Exception as exc:
        report['error']=type(exc).__name__+': '+str(exc)
        raise
    finally:
        report['actual_actions']=obs.step-initial
        atomic_json(out/'result.json',report,exclusive=True)
    return report
