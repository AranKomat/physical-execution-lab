from types import SimpleNamespace
import numpy as np
import pytest
from k1lab.errors import ContractError
from semantic_lab.robot_view import SingleEnvironmentRobotManager


def manager():
    calls = []
    def query(*args, env_idx_list=None, **kwargs):
        calls.append((env_idx_list, kwargs))
        return {idx: np.array([idx, 10+idx]) if idx in env_idx_list else None for idx in range(3)}
    limits = np.arange(12).reshape(3, 2, 2)
    return SimpleNamespace(num_envs=3, robot_list=['robot'],
        robot_key=[SimpleNamespace(data=SimpleNamespace(soft_joint_pos_limits=limits))],
        get_joint=query, get_link_pose=query, get_real_endpose=query, calls=calls)


def test_source_zero_index_queries_and_limits_bind_the_selected_native_environment():
    native = manager(); view = SingleEnvironmentRobotManager(native, 2)
    for query in (view.get_joint, view.get_link_pose, view.get_real_endpose):
        assert query('robot', is_relative=True)[0].tolist() == [2, 12]
    assert all(ids == [2] for ids, kwargs in native.calls)
    assert np.array_equal(view.robot_key[0].data.soft_joint_pos_limits,
                          native.robot_key[0].data.soft_joint_pos_limits[2:3])
    assert native.num_envs == 3 and view.num_envs == 1
    assert not hasattr(view, 'scene')  # No generic forwarding to scene/object state.


@pytest.mark.parametrize('idx', [-1, 3, True])
def test_robot_view_refuses_invalid_global_indices(idx):
    with pytest.raises(ContractError): SingleEnvironmentRobotManager(manager(), idx)


def test_robot_view_cannot_query_another_local_environment():
    view = SingleEnvironmentRobotManager(manager(), 1)
    with pytest.raises(ContractError): view.get_joint('robot', env_idx_list=[1])


def test_native_missing_pose_is_not_replaced_with_environment_zero():
    native = manager(); native.get_joint = lambda *a, **kw: {0: np.zeros(2), 1: None}
    view = SingleEnvironmentRobotManager(native, 1)
    with pytest.raises(ContractError): view.get_joint('robot')
