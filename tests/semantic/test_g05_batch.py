from types import SimpleNamespace
import numpy as np
import pytest
from k1lab.errors import ContractError
from semantic_lab.g05_batch import G05Batch, G05TokenGuard
from semantic_lab.motor_contract import motor_contract, validate_identity


class Tensor:
    def __init__(self, value): self.value = np.asarray(value)
    def detach(self): return self
    def cpu(self): return self
    def numpy(self): return self.value


def test_g05_guard_returns_exact_source_result_without_extra_encoding():
    result = (Tensor([[10, 11, 0], [20, 21, 0]]), Tensor([[1, 1, 0], [1, 1, 0]]))
    calls, records = [], []
    def encode(*args, **kwargs):
        calls.append((args, kwargs)); return result
    guard = G05TokenGuard(encode, lambda ids: 'Task: ' + ('pick red' if ids[0] == 10 else 'put blue'),
                          0, records.append)
    guard.prompts = ['pick red', 'put\nblue']
    assert guard(['samples'], mode='fm') is result
    assert len(calls) == guard.calls == 1
    assert all(row['entire_cleaned_prompt_present'] and row['active_tokens'] == 2 for row in records)


def test_g05_guard_rejects_truncation_without_repair():
    records = []
    guard = G05TokenGuard(lambda: (Tensor([[1]]), Tensor([[1]])), lambda ids: 'pick', 0, records.append)
    guard.prompts = ['pick the car']
    with pytest.raises(ContractError, match='not retained'):
        guard()
    assert not records[0]['entire_cleaned_prompt_present']
    assert guard.calls == 0


def fake_model(capacity=2, history=1):
    tokenizer = SimpleNamespace(decode=lambda ids: 'Task: ' + ('pick red' if ids[0] == 10 else 'put blue'),
                                pad_token_id=0)
    processor = SimpleNamespace(tokenizer=tokenizer,
        encode_inference=lambda: (Tensor([[10, 0], [20, 0]]), Tensor([[1, 0], [1, 0]])))
    model = SimpleNamespace(processor=SimpleNamespace(num_obs_steps=history), action_steps=16,
        inference_batch_size=capacity, policy=SimpleNamespace(processor=processor), resets=0, predictions=0)
    def reset(): model.resets += 1
    def update(rows): model.rows = rows
    def get():
        model.predictions += 1; processor.encode_inference()
        return [[{f'{arm}_arm_joint_state': np.full(6, row / 10)
                    for arm in ('left', 'right')} | {
                    f'{arm}_ee_joint_state': np.array([1.001]) for arm in ('left', 'right')}
                 for _ in range(16)] for row in range(capacity)]
    model.reset, model.update_obs_batch, model.get_action_batch = reset, update, get
    return model


def test_g05_fuses_distinct_rows_keeps_source_prefix_and_does_not_reset_on_prompt_change():
    model = fake_model(); records = []
    executor = G05Batch(model, dict(model_config=dict(inference_batch_size=2), gripper_clip=True), 2, records.append)
    raws = [dict(state=np.arange(14), prompt=prompt,
                 images={key: np.zeros((3, 2, 2), np.uint8)
                     for key in ('cam_high', 'cam_left_wrist', 'cam_right_wrist')})
            for prompt in ('pick red', 'put blue')]
    for _ in range(2): result = executor.infer(['group0/0', 'group1/0'], raws)
    assert model.resets == 1 and model.predictions == 2
    assert [row['env_idx'] for row in model.rows] == ['group0/0', 'group1/0']
    assert result['actions'].shape == result['raw_actions'].shape == (2, 16, 14)
    assert result['gripper_clips'] == [32, 32]
    assert result['actions'][0, 0, 6] == 1 and result['raw_actions'][0, 0, 6] > 1
    assert executor.calls == {'group0/0': 2, 'group1/0': 2}
    with pytest.raises(ContractError, match='unique episode'):
        executor.infer(['0', '0'], raws)


def test_g05_rejects_unqualified_history_or_singleton_batching():
    for capacity, history in ((1, 1), (2, 2)):
        with pytest.raises(ContractError, match='num_obs_steps'):
            G05Batch(fake_model(capacity, history), dict(model_config=dict(inference_batch_size=2)), 2, lambda row: None)


def test_motor_contract_distinguishes_underlying_and_exposed_g05_horizons():
    contract = motor_contract('g05')
    assert (contract['returned'], contract['execute'], contract['underlying_horizon']) == (16, 16, 32)
    identity = SimpleNamespace(name='g05_robodojo_fm', action_space='x5_joint14', execute_steps=16,
                               prediction_horizon=32, native_hz=25, stateful=True)
    assert validate_identity(identity, 'g05') == contract
    identity.execute_steps = 15
    with pytest.raises(ContractError): validate_identity(identity, 'g05')
