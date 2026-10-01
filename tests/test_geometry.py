import sys,types
import numpy as np
import pytest
from prl.geometry import measure_pixel,image_pixel,validate_camera,rpent_camera,fit_geometry
from prl.errors import ValidationError,Unavailable

@pytest.fixture
def cam():return {'depth':np.full((20,30),.5),'intrinsic_matrix':[[100,0,15],[0,100,10],[0,0,1]],'extrinsic_matrix':np.eye(4)}

def test_projection(cam):assert measure_pixel(cam,[15,10])['xyz_world_m']==[0,0,.5]

def test_projection_translation(cam):
    cam['extrinsic_matrix'][0,3]=1
    assert measure_pixel(cam,[15,10])['xyz_world_m']==[1,0,.5]

@pytest.mark.parametrize('p,space', [([0,0],'normalized_01'),([1000,1000],'normalized_1000'),([29,19],'pixels')])
def test_coordinate_modes(cam,p,space):assert measure_pixel(cam,p,space)['kind']=='measured_surface'

@pytest.mark.parametrize('p,space',[([1.01,0],'normalized_01'),([30,0],'pixels'),([-1,0],'pixels'),([0,0],'auto')])
def test_bad_pixels(cam,p,space):
    with pytest.raises(ValidationError):measure_pixel(cam,p,space)

@pytest.mark.parametrize('depth',[float('nan'),0,-1,11])
def test_invalid_depth(cam,depth):
    cam['depth'][10,15]=depth
    with pytest.raises(Unavailable):measure_pixel(cam,[15,10])

def test_reflection_not_rigid_rotation(cam):
    cam['extrinsic_matrix'][0,0]=-1
    with pytest.raises(ValidationError):validate_camera(cam)

def test_k1_hook_invokes_expected_interface(cam,monkeypatch):
    package=types.ModuleType('robo_harness');module=types.ModuleType('robo_harness.geometry');calls=[]
    def unproject(c,p):calls.append(p);return {'xyz_world_m':[0,0,.5]}
    module.unproject=unproject
    monkeypatch.setitem(sys.modules,'robo_harness',package);monkeypatch.setitem(sys.modules,'robo_harness.geometry',module)
    assert measure_pixel(cam,[15,10],engine='k1')['engine']=='k1';assert calls==[[15,10]]

def test_missing_k1_fails_not_fallback(cam,monkeypatch):
    monkeypatch.setitem(sys.modules,'robo_harness.geometry',None)
    with pytest.raises(Unavailable):measure_pixel(cam,[15,10],engine='k1')

def test_rpent_optical_flip(cam):
    image=np.zeros((20,30,3),dtype=np.uint8);image[0,:,0]=255
    depth=np.zeros((20,30));depth[0]=1
    meta={'depth_near':.1,'depth_far':1,'intrinsic_K':cam['intrinsic_matrix'],'extrinsic_cam2world':cam['extrinsic_matrix']}
    out=rpent_camera(image,depth,meta)
    assert out['rgb'][-1,0,0]==255
    assert out['depth'][-1,0]==pytest.approx(1) and out['depth'][0,0]==pytest.approx(.1)

def test_rpent_encoding_not_guessed(cam):
    with pytest.raises(Unavailable):rpent_camera(np.zeros((20,30,3)),cam['depth'],{})
