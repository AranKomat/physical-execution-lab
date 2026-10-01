"""Causal geometry boundary. Full K1 is optional and never silently substituted.

The built-in projection is a conventional geometric implementation, not a claim
of reproducing the K1 perception stack (SAM3, TAPNext++, grasp hypotheses).
"""
from __future__ import annotations
from .errors import ValidationError, Unavailable


def validate_camera(camera):
    import numpy as np
    k=np.asarray(camera['intrinsic_matrix'],float)
    t=np.asarray(camera['extrinsic_matrix'],float)
    depth=np.asarray(camera['depth'],float).squeeze()
    if k.shape!=(3,3) or t.shape!=(4,4) or depth.ndim!=2:
        raise ValidationError('camera_shape')
    if not np.isfinite(k).all() or not np.isfinite(t).all():
        raise ValidationError('nonfinite_calibration')
    if min(k[0,0],k[1,1])<=1 or abs(np.linalg.det(k))<1e-9:
        raise ValidationError('invalid_intrinsics')
    if not np.allclose(t[3],[0,0,0,1],atol=1e-6) or not np.allclose(t[:3,:3].T@t[:3,:3],np.eye(3),atol=1e-4) or np.linalg.det(t[:3,:3])<0.999:
        raise ValidationError('extrinsics_must_be_rigid_camera_to_world_optical')
    return depth,k,t


def image_pixel(pixel,shape,space='pixels'):
    import numpy as np
    p=np.asarray(pixel,float)
    if p.shape!=(2,) or not np.isfinite(p).all(): raise ValidationError('pixel_shape')
    h,w=shape
    if space=='normalized_01':
        if np.any(p<0) or np.any(p>1): raise ValidationError('pixel_range')
        p=p*np.array([w-1,h-1])
    elif space=='normalized_1000':
        if np.any(p<0) or np.any(p>1000): raise ValidationError('pixel_range')
        p=p/1000*np.array([w-1,h-1])
    elif space!='pixels': raise ValidationError('unknown_pixel_coordinate_space')
    if np.any(p<0) or p[0]>=w or p[1]>=h: raise ValidationError('pixel_outside_original_image')
    return np.minimum(np.floor(p+0.5).astype(int),[w-1,h-1])


def measure_pixel(camera,pixel,coordinate_space='pixels', *, engine='builtin'):
    import numpy as np
    depth,k,t=validate_camera(camera)
    u,v=image_pixel(pixel,depth.shape,coordinate_space)
    z=float(depth[v,u])
    if not np.isfinite(z) or not 0<z<10: raise Unavailable('invalid_measured_depth')
    if engine=='k1':
        try: from robo_harness.geometry import unproject
        except ImportError as e: raise Unavailable('Install pinned K1; no silent geometry fallback') from e
        result=unproject(camera,[int(u),int(v)])
    elif engine=='builtin':
        p=t[:3,:3]@(np.linalg.solve(k,[u,v,1])*z)+t[:3,3]
        result={'pixel':[int(u),int(v)],'depth_m':z,'xyz_world_m':p.tolist()}
    else: raise ValidationError('unknown_geometry_engine')
    return {**result,'engine':engine,'kind':'measured_surface',
            'meaning':'Visible surface only; not object center, collision clearance or grasp assurance.'}


def fit_geometry(camera,roi,kind):
    validate_camera(camera)
    try: from robo_harness.perception import fit_geometry as fit
    except ImportError as e: raise Unavailable('Pinned K1 perception module unavailable') from e
    return {**fit(camera,roi,kind=kind),'engine':'k1'}


def rpent_camera(raw_image,raw_depth,meta):
    """Match RPent tools._save_observation_artifacts, without high-res side renders.

    RPent policy-oriented images are NOT these optical calibration-frame images.
    Wrist extrinsics must be refreshed for each capture, not cached across motion.
    """
    import numpy as np
    d=np.asarray(raw_depth,dtype=np.float64).squeeze()
    rgb=np.asarray(raw_image)
    if d.ndim!=2 or rgb.shape[:2]!=d.shape:
        raise ValidationError('rgb_depth_shape_mismatch')
    near,far=meta.get('depth_near'),meta.get('depth_far')
    if near is None or far is None or not 0<near<far:
        raise Unavailable('depth_encoding_unqualified: expected RPent normalized depth metadata')
    if not np.isfinite(d).all() or np.any(d<0) or np.any(d>1):
        raise ValidationError('normalized_depth_out_of_range')
    metric=near/(1.0-d*(1.0-near/far))
    cam={'rgb':np.ascontiguousarray(rgb[::-1]),'depth':np.ascontiguousarray(metric[::-1]),
         'intrinsic_matrix':meta['intrinsic_K'],
         'extrinsic_matrix':meta['extrinsic_cam2world']}
    validate_camera(cam)
    return cam


K1_REV = "ee46363101fcf3ef87182fb2dbad99a92ce77fc0"

def load_k1(root):
    """Use only the reviewed K1 source pin; imports do not load neural weights."""
    import subprocess
    import sys
    from pathlib import Path
    root=Path(root).expanduser().resolve()
    if not (root/'src/robo_harness/geometry.py').is_file():
        raise Unavailable('Pinned K1 checkout missing')
    rev=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
    dirty=subprocess.check_output(['git','-C',str(root),'status','--porcelain','--untracked-files=no'],text=True)
    if rev!=K1_REV or dirty.strip():
        raise ValidationError('K1 source differs from reviewed pin')
    sys.path.insert(0,str(root/'src'))
    from robo_harness import geometry as module
    if Path(module.__file__).resolve()!=root/'src/robo_harness/geometry.py':
        raise ValidationError('A different K1 package was imported earlier')
    return {'repository_revision':rev,'geometry_file':str(module.__file__)}
