import importlib.util
from pathlib import Path

import pytest


path = Path(__file__).resolve().parents[2] / 'scripts/multibench/export_inference_checkpoint.py'
spec = importlib.util.spec_from_file_location('inference_export', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_preserves_model_state_and_drops_training_state():
    state = {'weight': object()}
    source = {'model_state_dict': state, 'step': 7, 'optimizer_state_dict': object(),
              'ema_model_state_dict': object(), 'epoch': object()}
    result = module.inference_payload(source)
    assert result['model_state_dict'] is state
    assert result['step'] == 7
    assert 'optimizer_state_dict' not in result
    assert 'ema_model_state_dict' not in result
    assert 'epoch' not in result
    assert 'optimizer_state_dict' in source


def test_rejects_empty_state():
    with pytest.raises(ValueError):
        module.inference_payload({'model_state_dict': {}})
