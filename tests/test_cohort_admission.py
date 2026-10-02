import json
from types import SimpleNamespace

import numpy as np
import pytest

from k1lab.errors import ContractError
from semantic_lab.cohort_admission import check_reset


def reset_fixture(tmp_path):
    cases = [dict(case_id='task0', horizon=20), dict(case_id='task1', horizon=40)]
    resolved, bindings = [{'native': 0}, {'native': 1}], [{'layout': 0}, {'layout': 1}]
    (tmp_path / 'resolved-configs.json').write_text(json.dumps(resolved))
    (tmp_path / 'task-bindings.json').write_text(json.dumps(bindings))
    states = np.zeros((2, 14), np.float32)
    states[1] = 1
    np.savez(tmp_path / 'request-0000.npz', env_ids=np.array([0, 1]), states=states,
             prompts=np.array(['native0', 'native1']))
    observations = {i: SimpleNamespace(step=0, state=states[i].copy(), instruction=f'native{i}')
                    for i in range(2)}
    return cases, resolved, bindings, [20, 40], observations


def test_reset_binding_preserves_distinct_native_rows(tmp_path):
    report = check_reset(tmp_path, *reset_fixture(tmp_path))
    assert report['passed'] and len(report['rows']) == 2
    assert not report['rgb_bitwise_parity_required']


@pytest.mark.parametrize('field', ['state', 'instruction', 'horizon', 'config', 'layout'])
def test_reset_binding_rejects_mismatched_row(tmp_path, field):
    cases, configs, bindings, horizons, observations = reset_fixture(tmp_path)
    if field == 'state':
        observations[1].state = observations[0].state
    elif field == 'instruction':
        observations[1].instruction = observations[0].instruction
    elif field == 'horizon':
        horizons[1] += 1
    elif field == 'config':
        configs[1]['native'] = 0
    else:
        bindings[1]['layout'] = 0
    with pytest.raises(ContractError):
        check_reset(tmp_path, cases, configs, bindings, horizons, observations)
