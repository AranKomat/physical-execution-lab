"""K1 tracked sensor points, never scene-state contacts or object IDs.

A rigid co-motion test supports a hypothesis. It is NOT a grasp certificate.
"""
from __future__ import annotations
from collections import deque
import numpy as np
from scipy.spatial.transform import Rotation
from .util import vector


def point_at(points,point_id,frame):
    for p in points:
        if p.get('id')==point_id and p.get('frame_id')==frame and p.get('status') in ('initialized','tracked_estimate'):
            try: return vector(p['xyz_world_m'],3)
            except (KeyError,ValueError): return None
    return None


class CoMotion:
    def __init__(self,point_id,obs,points,arm,minimum_m=0.008,tolerance_m=0.006,min_samples=3):
        self.point_id=point_id; self.arm=arm; self.minimum=minimum_m; self.tolerance=tolerance_m
        self.min_samples=min_samples; self.samples=deque(maxlen=32)
        self.p0=point_at(points,point_id,obs['frame_id'])
        state=obs['arms'][arm]; self.t0=vector(state['xyz_world_m'],3)
        self.r0=Rotation.from_quat(state['quaternion_xyzw'])
        self.last_frame=obs['frame_id']; self.reason='insufficient_movement'
    def update(self,obs,points):
        frame=obs['frame_id']
        if frame<=self.last_frame: return
        self.last_frame=frame
        p=point_at(points,self.point_id,frame)
        if self.p0 is None or p is None:
            self.samples.clear(); self.reason='correspondence_or_depth_unavailable'; return
        state=obs['arms'][self.arm]; t=vector(state['xyz_world_m'],3); r=Rotation.from_quat(state['quaternion_xyzw'])
        predicted=t+(r*self.r0.inv()).apply(self.p0-self.t0)
        travel=float(np.linalg.norm(predicted-self.p0))
        residual=float(np.linalg.norm(p-predicted))
        displacement=float(np.linalg.norm(p-self.p0))
        self.samples.append({'frame_id':frame,'expected_feature_displacement_m':travel,
                             'measured_feature_displacement_m':displacement,'rigid_residual_m':residual})
        self.reason='insufficient_movement' if travel<self.minimum else 'measured'
    def result(self):
        eligible=[s for s in self.samples if s['expected_feature_displacement_m']>=self.minimum]
        status='unknown'; reason=self.reason
        recent=eligible[-self.min_samples:]
        if len(recent)>=self.min_samples:
            if all(s['rigid_residual_m']<=self.tolerance and s['measured_feature_displacement_m']>=self.minimum/2 for s in recent):
                status='supported'; reason='tracked_feature_follows_rigid_hand_motion'
            elif all(s['rigid_residual_m']>2*self.tolerance for s in recent):
                status='contradicted'; reason='tracked_feature_does_not_follow_hand'
        return {'status':status,'reason':reason,'point_id':self.point_id,'samples':list(self.samples),
                'identity_verified':False,'attachment_verified':False,
                'meaning':'Sensor correspondence supports/challenges co-motion, not identity, attachment, force safety or task success.'}
