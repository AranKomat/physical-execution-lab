import importlib.util
from pathlib import Path

import pytest

from k1lab.errors import ContractError


path = Path(__file__).resolve().parents[2] / 'scripts/multibench/plan_matrix.py'
spec = importlib.util.spec_from_file_location('matrix_budget', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def config(mode='direct_dense', steps=5, requests=180, reviews=180):
    return {'mode': mode, 'max_decision_steps': steps, 'max_reviews': reviews,
            'model': {'max_requests': requests}}


def test_dense_budget_cannot_cover_native_horizon():
    row = module.direct_budget_feasibility({'horizon': 1100}, config())
    assert row['maximum_native_actions_from_call_budget'] == 900
    assert row['minimum_decisions_for_full_horizon'] == 220
    assert not row['full_horizon_possible_under_call_budget']


def test_sparse_and_request_cap_are_explicit():
    row = module.direct_budget_feasibility({'horizon': 1100},
                                          config('direct_sparse', 40, 75))
    assert row['maximum_decisions'] == 75
    assert row['minimum_decisions_for_full_horizon'] == 28
    assert row['full_horizon_possible_under_call_budget']
    assert module.direct_budget_feasibility({}, {'mode': 'motor_only'}) is None


@pytest.mark.parametrize('horizon', [None, 0, True, 1.5])
def test_missing_or_invalid_horizon_is_not_treated_as_feasible(horizon):
    with pytest.raises(ContractError):
        module.direct_budget_feasibility({'horizon': horizon}, config())
