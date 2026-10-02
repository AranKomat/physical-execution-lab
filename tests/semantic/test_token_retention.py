import numpy as np
import pytest
from k1lab.errors import ContractError
from semantic_lab.token_retention import PromptRetentionGuard


def test_guard_observes_once_and_returns_identical_native_object():
    transformed = {'tokenized_prompt': np.array([10, 11, 0]),
                   'tokenized_prompt_mask': np.array([True, True, False]), 'images': object()}
    calls = []; records = []
    def transform(raw):
        calls.append(raw)
        return transformed
    guard = PromptRetentionGuard(transform, lambda ids: 'Task: Pick up red ball, State: 1', records.append)
    raw = {'prompt': 'Pick_up\nred ball'}
    assert guard(raw) is transformed
    assert calls == [raw] and records[0]['active_tokens'] == 2
    assert records[0]['entire_cleaned_prompt_present'] is True


def test_truncation_is_recorded_then_rejected_without_prompt_repair():
    records = []
    guard = PromptRetentionGuard(lambda raw: {'tokenized_prompt': np.array([10]),
        'tokenized_prompt_mask': np.array([True])}, lambda ids: 'Task: Pick up', records.append)
    raw = {'prompt': 'Pick up the ball'}
    with pytest.raises(ContractError, match='not retained'):
        guard(raw)
    assert raw == {'prompt': 'Pick up the ball'}
    assert records[0]['entire_cleaned_prompt_present'] is False


@pytest.mark.parametrize('mask', [np.array([1]), np.array([[True]]), np.array([True, False])])
def test_guard_refuses_malformed_native_mask(mask):
    guard = PromptRetentionGuard(lambda raw: {'tokenized_prompt': np.array([10]),
        'tokenized_prompt_mask': mask}, lambda ids: 'Task: hello', lambda row: None)
    with pytest.raises(ContractError, match='shape/mask'):
        guard({'prompt': 'hello'})
