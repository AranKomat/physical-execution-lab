"""Prepare the fixed pi0.5-first four-way screen without reading outcomes."""
from copy import deepcopy
from k1lab.errors import ContractError
from k1lab.multibench.manifest import check, seal
from k1lab.util import digest

TASKS = ('arrange_largest_number', 'build_tower', 'classify_objects',
         'classify_objects_by_language', 'fold_clothes', 'imitate_sorting_sequence',
         'make_kong', 'organize_table', 'pack_objects_into_box', 'put_bottles_into_dustbin')


def prepare(manifest, provider, *, allow_standard_fallback=False):
    check(manifest)
    identity = provider['identity']
    if (identity['name'] != 'pi05_robodojo' or identity['action_space'] != 'x5_joint14'
            or identity['prediction_horizon'] != 50 or identity['execute_steps'] != 15
            or identity['stateful'] or not identity['checkpoint_sha256']):
        raise ContractError('comparison requires the exact bound stateless pi0.5 H50/15 identity')
    by_id = {row['case_id']: row for row in manifest['cases']}
    ids = [f'{task}__standard__g0__l0' for task in TASKS]
    if any(case_id not in by_id for case_id in ids):
        raise ContractError('fixed comparison roster is incomplete; no replacement allowed')
    cases = [deepcopy(by_id[case_id]) for case_id in ids]
    for task, row in zip(TASKS, cases):
        if (row['benchmark'] != 'robodojo' or row['runtime_task'] != task
                or row['task_group'] != task or row['variant'] != 'standard'
                or row['eval_seed'] != 0 or row['layout_id'] != 0
                or not row.get('layout_sha256') or row['native_hz'] != 25):
            raise ContractError('fixed reference case contract differs')
    model = dict(api_key_env='K1_RELAY_TOKEN', base_url='http://127.0.0.1:19861',
                 history_rounds=4, image_max_edge=480, max_output_tokens=2048,
                 max_requests=180, max_total_output_tokens=368640, model='gpt-6.1-sol',
                 reasoning_effort='medium', service_tier='flex', timeout_s=900, transport='responses')
    if allow_standard_fallback:
        model['tier_fallback'] = 'same_model_default_after_explicit_flex_capacity'
    common = dict(wall_limit_s=3600, no_task_memory=True, no_task_demonstrations=True,
                  controller_probe=False, comparison_scope='ten distinct tasks, one layout each; not full RoboDojo SR')
    configs = {}
    for label, mode in [('original_only', 'motor_only'), ('direct', 'direct_sparse'),
                        ('numeric', 'sparse'), ('semantic', 'semantic_subtask_hierarchy')]:
        config = dict(common, name='pi05_approach_screen001_'+label, mode=mode)
        if allow_standard_fallback and label != 'original_only':
            config['name'] += '_standard_fallback001'
        if label != 'original_only':
            config['model'] = deepcopy(model)
        if label in ('direct', 'numeric'):
            config.update(max_reviews=180, max_decision_steps=40 if label == 'direct' else 15,
                          max_correction_steps=40 if label == 'direct' else 5,
                          translation_limit_m=.05, robot_preview=label == 'numeric')
        if label == 'numeric':
            # The governor caps leases at this value; 105 preserves H15 natural boundaries.
            config['monitor'] = dict(max_unreviewed_steps=105, max_unreviewed_chunks=7)
        if label == 'semantic':
            config.update(prompt_mode='task_plus_subtask', max_semantic_calls=180,
                          async_planner=False, semantic_schedule=dict(review_interval_steps=100,
                          minimum_dwell_steps=30, event_cooldown_steps=30, allow_semantic_recovery=False))
        configs[label] = config
    panel = seal(dict(schema='multibench.manifest.v1', formal=False, cases=cases,
                      parent_manifest_sha256=manifest['sha256'], task_set='pi05_approach_screen001'))
    plan = seal(dict(schema='semantic.approach_screen.v1', manifest_sha256=panel['sha256'],
        parent_manifest_sha256=manifest['sha256'], provider_sha256=digest(provider), motor_identity=identity,
        configs={label: digest(config) for label, config in configs.items()},
        slots=[dict(condition=configs[label]['name'], approach=label, case_id=case_id, status='missing')
               for label in configs for case_id in ids],
        executed=False, qualified=False, source_freeze_pending=True,
        budget=('existing shared $85 reservation ledger; unresolved holds retained; '
                'only authorized same-model standard fallback after explicit Flex capacity'
                if allow_standard_fallback else
                'existing shared $85 reservation ledger; unresolved holds retained; no retry/fallback'),
        tier_policy='flex_preferred_same_model_standard_capacity_fallback' if allow_standard_fallback else 'flex_only',
        direct_has_motor_policy=False, numeric_is_adapted_not_paper_reproduction=True,
        initial_case_order_fixed_before_new_outcomes=True,
        censoring='budget/wall/contract/resource stops remain separate from physical horizon failures',
        cadence='numeric periodic lease105; semantic target100 at next H15 boundary; event reviews differ explicitly'))
    return panel, configs, plan
