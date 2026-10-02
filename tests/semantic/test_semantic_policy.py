from dataclasses import replace
import numpy as np
import pytest
from k1lab.errors import ContractError
from k1lab.multibench.types import Proposal, Action
from k1lab.multibench.adapters.pi05 import Pi05Policy
from k1lab.multibench.adapters.xpolicylab import XPolicyModel
from k1lab.multibench.adapters.robocasa import XiaomiRoboCasaPolicy
from semantic_lab.policy import InstructionPolicy
from semantic_lab.contracts import SemanticContext
from semantic_lab.synthetic import ToyEnvironment, ToyPolicy


def begin(base=None, kind='test'):
    env = ToyEnvironment(); obs = env.obs()
    base = base or ToyPolicy(); wrapper = InstructionPolicy(base, kind=kind)
    wrapper.reset(); wrapper.set_context(SemanticContext(obs.instruction, prompt_mode='task_plus_subtask')); wrapper.observe(obs)
    return env, wrapper, base


def drain(env, wrapper, proposal):
    for a in proposal.actions[:wrapper.identity.execute_steps]:
        step = env.step(a); wrapper.observe(step.observation)
    return wrapper.finish_prefix(wrapper.identity.execute_steps)


def test_context_switch_no_extra_ack_no_reset():
    env, w, b = begin(); obs = env.obs()
    w.set_context(SemanticContext(obs.instruction, 'Pick object.', 1, 'task_plus_subtask'))
    p = w.propose(obs)
    assert b.acks == [0] and b.rebindings == 1
    assert 'Current subtask:\nPick object.' in b.prompts[-1]
    assert p.observation_sha256 == obs.stamp
    assert p.diagnostics['semantic']['conditioned_observation_sha256'] != obs.stamp
    receipt = drain(env, w, p)
    assert receipt['natural_unexecuted_prediction_suffix'] == 2
    assert b.acks == [0, 1, 2, 3] and not b.invalidations
    w.set_context(SemanticContext(obs.instruction, 'Place object.', 2, 'task_plus_subtask'))
    p = w.propose(env.obs()); assert b.acks == [0, 1, 2, 3]
    drain(env, w, p); assert not b.invalidations


def test_cannot_resample_or_set_context_mid_prefix():
    env, w, _ = begin(); w.propose(env.obs())
    with pytest.raises(ContractError): w.propose(env.obs())
    with pytest.raises(ContractError): w.set_context(SemanticContext(env.task))
    with pytest.raises(ContractError): w.reset()
    with pytest.raises(ContractError): w.finish_prefix(0)


def test_abort_does_not_fake_actions():
    env, w, b = begin(); p = w.propose(env.obs())
    w.observe(env.step(p.actions[0]).observation)
    receipt = w.finish_prefix(1, 'resource_limit')
    assert b.acks == [0, 1] and receipt['unexecuted_prefix'] == 2
    assert b.invalidations == ['resource_limit']


def test_no_skipped_or_unexpected_acks():
    env, w, _ = begin(); env.step_id = 1
    with pytest.raises(ContractError): w.observe(env.obs())
    env.step_id = 0; w.propose(env.obs()); env.step_id = 2
    with pytest.raises(ContractError): w.observe(env.obs())


def test_original_context_immutable_and_epochs_monotonic():
    env, w, _ = begin()
    with pytest.raises(ContractError): w.set_context(SemanticContext('Other task'))
    with pytest.raises(ContractError): w.set_context(SemanticContext(env.task, 'Goal', 3, 'task_plus_subtask'))
    with pytest.raises(ContractError): w.set_context(SemanticContext(env.task, prompt_mode='subtask_only'))


class XplSource:
    def __init__(self): self.reset()
    def reset(self):
        self.session = self
        self.pending_model_actions = []
        self.current = None
        self.ack_history = []
        self.prompts = []
    def update_obs(self, obs):
        self.current = obs
        if self.pending_model_actions:
            self.pending_model_actions.pop(0)
            self.ack_history.append(obs['state']['left_ee_pose'][0])
    def get_action(self):
        assert not self.pending_model_actions
        self.prompts.append(self.current['instruction'])
        self.pending_model_actions = [0, 0, 0]
        return [dict(left_arm_joint_state=np.zeros(6), right_arm_joint_state=np.zeros(6),
                     left_ee_joint_state=np.array([.5]), right_ee_joint_state=np.array([.5])) for _ in range(3)]


def test_real_xpolicy_wrapper_refresh_no_phantom_wam_ack():
    from dataclasses import asdict
    identity = asdict(ToyPolicy(horizon=3, execute=3).identity)
    source = XplSource()
    base = XPolicyModel({'policy': 'internw0_delta', 'identity': identity, 'model_config': {}}, model=source)
    env = ToyEnvironment()
    # XPL needs three views; preserve explicit distinct named arrays in the fixture.
    oldobs = env.obs
    def obs3():
        obs = oldobs(); obs.rgb.update(cam_left_wrist=obs.rgb['cam_high'].copy(), cam_right_wrist=obs.rgb['cam_high'].copy()); return obs
    env.obs = obs3
    w = InstructionPolicy(base, kind='xpolicylab'); w.reset()
    w.set_context(SemanticContext(env.task, prompt_mode='task_plus_subtask')); w.observe(env.obs())
    w.set_context(SemanticContext(env.task, 'First goal.', 1, 'task_plus_subtask'))
    p = w.propose(env.obs()); assert source.ack_history == []
    drain(env, w, p); assert len(source.ack_history) == 3
    w.set_context(SemanticContext(env.task, 'Second goal.', 2, 'task_plus_subtask'))
    p = w.propose(env.obs())
    assert len(source.ack_history) == 3 and 'Second goal.' in source.prompts[-1]
    drain(env, w, p); assert len(source.ack_history) == 6


def test_real_pi05_wrapper_prompt_gets_to_native_client(tmp_path):
    from dataclasses import asdict
    class Client:
        metadata = {}
        def infer(self, raw, path):
            self.raw = raw
            arr = np.zeros((5, 14), np.float32); arr[:, [6, 13]] = .5
            return arr, {}
        def close(self): pass
    client = Client()
    base = Pi05Policy({'identity': asdict(ToyPolicy().identity), 'artifact_dir': str(tmp_path)}, client=client)
    env, w, _ = begin(base, 'pi05')
    w.set_context(SemanticContext(env.task, 'New goal.', 1, 'task_plus_subtask'))
    w.propose(env.obs())
    assert client.raw['instruction'].endswith('New goal.')
    assert env.obs().instruction == env.task


def test_real_xr1_wrapper_keeps_history_on_prompt_change():
    from dataclasses import asdict
    class Helper:
        CAMERA_KEYS = ('cam_high',)
        @staticmethod
        def sample_history(q, length, interval): return np.stack(list(q))
    class Client:
        def infer(self, states, images, instruction):
            self.length = len(states); self.instruction = instruction
            return np.zeros((3, 12))
        def close(self): pass
    identity = asdict(ToyPolicy(horizon=3, execute=3).identity); identity['action_space'] = 'robocasa12'
    client = Client()
    base = XiaomiRoboCasaPolicy({'identity': identity}, client=client, evaluator=Helper())
    env, w, _ = begin(base, 'xiaomi_robocasa')
    w.set_context(SemanticContext(env.task, 'First goal.', 1, 'task_plus_subtask'))
    p = w.propose(env.obs()); assert len(base.states) == 1
    drain(env, w, p)
    length = len(base.states)
    w.set_context(SemanticContext(env.task, 'Second goal.', 2, 'task_plus_subtask'))
    w.propose(env.obs())
    assert len(base.states) == length and client.instruction.endswith('Second goal.')
