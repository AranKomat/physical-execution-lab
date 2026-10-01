import numpy as np
from scipy.spatial.transform import Rotation
from k1lab.evidence import CoMotion,point_at
from k1lab.fixture import FixturePort

def test_duplicate_frames_not_new_evidence():
    p=FixturePort();m=CoMotion('P1',p.observe(),p.points(),'arm')
    for _ in range(10):m.update(p.observe(),p.points())
    assert m.result()['status']=='unknown' and not m.samples

def test_lost_correspondence_invalidates():
    p=FixturePort(lost_at=1);m=CoMotion('P1',p.observe(),p.points(),'arm')
    p.servo('arm',[0,0,.52],p.q,0);m.update(p.observe(),p.points())
    assert m.result()['status']=='unknown' and m.result()['reason']=='correspondence_or_depth_unavailable'

def test_rotation_compensated():
    p=FixturePort();p.gripper=0;p.feature=np.array([.03,0,.5]);m=CoMotion('P1',p.observe(),p.points(),'arm')
    for degrees in (30,45,60,90):
        p.servo('arm',p.xyz,Rotation.from_euler('z',degrees,degrees=True).as_quat(),0)
        m.update(p.observe(),p.points())
    assert m.result()['status']=='supported'

def test_motion_not_enough_for_identity():
    p=FixturePort();p.gripper=0;m=CoMotion('P1',p.observe(),p.points(),'arm')
    for x in (.01,.02,.03):p.servo('arm',[x,0,.5],p.q,0);m.update(p.observe(),p.points())
    assert m.result()['status']=='supported' and not m.result()['identity_verified']

def test_historical_coordinate_never_used():
    assert point_at([{'id':'P1','frame_id':3,'status':'lost_remeasure','historical_xyz_world_m_not_current':[1,2,3]}],'P1',3) is None
