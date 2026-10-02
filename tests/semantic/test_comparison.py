from copy import deepcopy
import pytest
from k1lab.errors import ContractError
from k1lab.multibench.manifest import seal
from semantic_lab.comparison import prepare, TASKS


def inputs():
    cases = [dict(case_id=f'{t}__standard__g0__l0', task=t, task_group=t, runtime_task=t,
        benchmark='robodojo', partition='dev' if i < 3 else 'test', variant='standard',
        horizon=1100, eval_seed=0, layout_id=0, layout_sha256=str(i), native_hz=25)
        for i, t in enumerate(TASKS)]
    provider = dict(identity=dict(name='pi05_robodojo', action_space='x5_joint14',
        prediction_horizon=50, execute_steps=15, stateful=False, checkpoint_sha256='checkpoint'))
    return seal(dict(cases=cases)), provider


def test_four_way_preparation_keeps_fixed_roster_and_explicit_missing_denominator():
    manifest, provider = inputs()
    original = deepcopy((manifest, provider))
    panel, configs, plan = prepare(manifest, provider)
    assert (manifest, provider) == original
    assert len(panel['cases']) == 10 and len(plan['slots']) == 40
    assert {row['status'] for row in plan['slots']} == {'missing'}
    assert not plan['executed'] and not plan['qualified']
    assert configs['numeric']['monitor']['max_unreviewed_steps'] == 105
    assert configs['semantic']['semantic_schedule']['review_interval_steps'] == 100
    assert not configs['semantic']['semantic_schedule']['allow_semantic_recovery']
    assert configs['direct']['max_correction_steps'] == 40
    assert 'model' not in configs['original_only']
    assert all(c['model']['service_tier'] == 'flex' for c in configs.values() if 'model' in c)


def test_preparation_refuses_roster_replacement_and_inexact_motor():
    manifest, provider = inputs()
    with pytest.raises(ContractError): prepare(seal(dict(cases=manifest['cases'][:-1])), provider)
    provider['identity']['execute_steps'] = 16
    with pytest.raises(ContractError): prepare(manifest, provider)


def test_authorized_tier_fallback_preserves_baseline_and_names_new_paid_conditions():
    manifest, provider = inputs()
    panel, configs, plan = prepare(manifest, provider)
    new_panel, new_configs, new_plan = prepare(manifest, provider, allow_standard_fallback=True)
    assert new_panel == panel and new_configs['original_only'] == configs['original_only']
    assert new_plan['tier_policy'] == 'flex_preferred_same_model_standard_capacity_fallback'
    for name in ('direct', 'numeric', 'semantic'):
        assert new_configs[name]['name'] != configs[name]['name']
        assert new_configs[name]['model']['model'] == configs[name]['model']['model']
        assert new_configs[name]['model']['reasoning_effort'] == 'medium'
        assert new_configs[name]['model']['tier_fallback'] == 'same_model_default_after_explicit_flex_capacity'
