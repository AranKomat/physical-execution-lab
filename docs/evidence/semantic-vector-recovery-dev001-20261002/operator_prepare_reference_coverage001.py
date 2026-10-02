"""Plan task coverage from official case identities, without loading outcomes."""
import json
import hashlib
from pathlib import Path

root = Path('/root/physical-execution-lab')
source = root / 'configs/local/robodojo-cases.json'
manifest = json.loads(source.read_text())
groups = {}
for case in manifest['cases']:
    groups.setdefault(case['task_group'], []).append(case)
assert len(groups) == 10 and all(len(rows) == 5 for rows in groups.values())
fields = ('case_id', 'task', 'runtime_task', 'task_group', 'partition', 'variant',
    'eval_seed', 'layout_id', 'horizon', 'native_hz', 'layout_sha256', 'layout_path')
rows = []
for task, cases in sorted(groups.items()):
    selected = sorted(cases, key=lambda c: (c['variant'] != 'standard', c['layout_id'], c['case_id']))
    rows.append({'task_group': task,
        'initial_screen_case': {key: selected[0][key] for key in fields if key in selected[0]},
        'full_reference_cases': [{key: case[key] for key in fields if key in case} for case in selected],
        'untouched_heldout_eligible': selected[0]['partition'] == 'test' and task != 'arrange_largest_number',
        'vector_execution_admitted': task in ('classify_objects', 'build_tower')})
plan = {'scope': 'reference-aligned coverage preparation, not native execution or a qualified freeze',
    'manifest_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'initial_screen_tasks': 10, 'initial_screen_cases': 10, 'full_reference_cases': 50,
    'selection': 'all task groups; standard then numerical layout order; no outcome selection',
    'score': 'native [0,1]; multiply by100 for reference Score display',
    'no_baseline_rerun_for_scale_conversion': True,
    'reuse_rule': 'exact task/layout/model/cadence/sensors/runtime cohort only; do not pool historical serial runs',
    'missing_baselines_require_fresh_execution': True,
    'preserve_grouped_split': True, 'no_prompt_tuning_on_untouched_tasks': True,
    'admission_requirements': ['source-faithful task variant and layout reset',
        'native support-arm behavior if required', 'native horizon and nonvacuous completion registration',
        'actual ACK/source/RNG audits and actor/evaluator isolation'],
    'tasks': rows}
target = root / 'runs/reference-aligned-coverage001'
target.mkdir(exist_ok=False)
(target / 'plan.json').write_text(json.dumps(plan, indent=2) + '\n')
print(json.dumps({'tasks': 10, 'screen_cases': 10, 'full_cases': 50, 'output': str(target)}))
