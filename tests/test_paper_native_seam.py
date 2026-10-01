"""CPU contract tests of native adapter math. These never instantiate LIBERO."""
from types import SimpleNamespace as NS
from dataclasses import replace
from pathlib import Path
import importlib.util
import numpy as np
import pytest
from scipy.spatial.transform import Rotation
from prl.dyna.native import geom_vertices, object_geometry, NativeBackend
from prl.dyna.fixture import FixtureBackend, FixturePlanner
from prl.dyna.engine import Engine, CommandFailure
from prl.dyna.planner import Advisory, context_for, decode_plan
from prl.dyna.capabilities import PaperLibrary
from prl.dyna.scene import ExecutionMemory
from prl.journal import Journal
from prl.errors import ValidationError
from prl.util import atomic_json, digest, file_digest


def geom_sim(typ=6, size=(.1,.2,.3), rot=None):
    r=np.eye(3) if rot is None else rot
    return NS(model=NS(geom_type=[typ],geom_size=np.array([size]),geom_dataid=[0],
        mesh_vertadr=[0],mesh_vertnum=[2],mesh_vert=np.array([[0,0,0],[.2,.3,.4]])),
        data=NS(geom_xmat=[r.ravel()],geom_xpos=[[1,2,3]]))

@pytest.mark.parametrize('typ,expected',[(2,[.1,.1,.1]),(3,[.1,.1,.3]),(4,[.1,.2,.3]),(5,[.1,.1,.2]),(6,[.1,.2,.3])])
def test_geom_extent_type(typ,expected):
    p=geom_vertices(geom_sim(typ),0)
    assert np.allclose((p.max(0)-p.min(0))/2,expected)

def test_mesh_vertices_transformed():
    p=geom_vertices(geom_sim(7),0)
    assert np.allclose(p,[[1,2,3],[1.2,2.3,3.4]])

def test_geometry_rotation_changes_world_bounds():
    p=geom_vertices(geom_sim(rot=Rotation.from_euler('z',90,degrees=True).as_matrix()),0)
    assert np.allclose((p.max(0)-p.min(0))/2,[.2,.1,.3])

def test_unsupported_geom_not_fabricated():
    assert geom_vertices(geom_sim(0),0).shape==(0,3)

def test_object_bounds_use_collision_geometry():
    sim=geom_sim();sim.model.body_name2id=lambda name:0;sim.model.geom_name2id=lambda name:0
    sim.data.body_xmat=[np.eye(3).ravel()];sim.data.body_xpos=[[1,2,3]]
    entity,gids,root=object_geometry(sim,NS(root_body='root',contact_geoms=['physical'],category_name='box'),'box',10,False)
    assert entity.observed_step==10 and entity.source=='privileged_sim'
    assert np.allclose(entity.half_size,[.1,.2,.3]) and gids==[0] and root==0

def test_pose_action_uses_controller_scaling():
    b=NativeBackend.__new__(NativeBackend);scene=FixtureBackend().scene();b.scene=lambda:scene
    b.output_max=np.array([.05,.05,.05,.5,.5,.5])
    action=b.pose_action(np.array(scene.eef_xyz)+[.01,0,0],scene.eef_quat,-1)
    assert action[0]==pytest.approx(.2) and action[6]==-1

def test_pose_action_clips_large_commands():
    b=NativeBackend.__new__(NativeBackend);scene=FixtureBackend().scene();b.scene=lambda:scene
    b.output_max=np.array([.05,.05,.05,.5,.5,.5])
    action=b.pose_action(np.array(scene.eef_xyz)+[5,0,0],scene.eef_quat,1)
    assert abs(action).max()<=1

def test_watchdog_wraps_actual_substeps():
    b=NativeBackend.__new__(NativeBackend);sim=NS(data=NS(time=0.))
    def rawstep():sim.data.time+=.002
    sim.step=rawstep;b.env=NS(sim=sim);b.substep_guard_calls=0
    scene=FixtureBackend().scene();b.safety_scene=lambda:replace(scene,simulation_time=sim.data.time)
    seen=[];b.set_safety_check(lambda s:seen.append(s.simulation_time),50)
    for _ in range(100):sim.step()
    assert len(seen)==10 and len(set(seen))==10
    assert np.diff(seen)==pytest.approx([.02]*9)

def test_missing_entity_is_recorded_refusal(tmp_path):
    b=FixtureBackend();j=Journal(tmp_path/'events.jsonl');e=Engine(b,FixturePlanner(),j,out=tmp_path)
    r=e.execute(Advisory('pick_and_place',{'object':'not_present','destination':'tray'}),'1');j.close()
    assert r['status']=='refused' and r['refusal_kind']=='grounding'
    assert b.steps==0 and e.refusals==1

@pytest.mark.parametrize('args',[{'object':'x','state':'maybe'}, {'object':'x','state':'OPEN'}])
def test_semantic_schema_repair_rejects_invalid_state(args):
    c=context_for(FixtureBackend().scene(),PaperLibrary(),ExecutionMemory(),300,'req')
    with pytest.raises(ValidationError):decode_plan({'capability':'slide_drawer','arguments':args},c)


def manifest_loader():
    path=Path(__file__).resolve().parents[1]/'scripts/serve_paper_policy.py'
    spec=importlib.util.spec_from_file_location('serve_paper_test',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.verified_manifest

def make_model(tmp_path):
    model=tmp_path/'model';model.mkdir();weight=model/'weights.bin';weight.write_bytes(b'not_real_weights')
    body={'format':1,'files':[{'path':'weights.bin','size':len(weight.read_bytes()),'sha256':file_digest(weight)}]}
    body['sha256']=digest(body);path=tmp_path/'weights.json';atomic_json(path,body)
    return model,weight,path,body

def test_policy_byte_manifest(tmp_path):
    model,weight,path,body=make_model(tmp_path)
    assert manifest_loader()(model,path)==body['sha256']

def test_policy_changed_bytes_rejected(tmp_path):
    model,weight,path,body=make_model(tmp_path);weight.write_bytes(b'changed')
    with pytest.raises(ValidationError,match='bytes_changed'):manifest_loader()(model,path)

def test_policy_manifest_tamper_rejected(tmp_path):
    model,weight,path,body=make_model(tmp_path);body['format']=999;atomic_json(path,body)
    with pytest.raises(ValidationError,match='tampered'):manifest_loader()(model,path)

def test_policy_manifest_path_escape(tmp_path):
    model,weight,path,body=make_model(tmp_path);body['files'][0]['path']='../other'
    body['sha256']=digest({k:v for k,v in body.items() if k!='sha256'});atomic_json(path,body)
    with pytest.raises(ValidationError,match='path_escape'):manifest_loader()(model,path)
