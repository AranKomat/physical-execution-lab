"""Offline source/layout admission inventory; never imports task execution."""
import ast
import hashlib
import json
from pathlib import Path
import sys

root = Path('/root/physical-execution-lab')
sys.path.insert(0, str(root))
from k1lab.multibench.manifest import check

manifest_path = root / 'configs/local/robodojo-cases.json'
manifest = json.loads(manifest_path.read_text())
check(manifest)
opened = {'classify_objects', 'build_tower', 'arrange_largest_number'}
groups = {row['task_group'] for row in manifest['cases']}
assert len(groups) == 10 and len(manifest['cases']) == 50
rows = []
for task in sorted({row['runtime_task'] for row in manifest['cases']}):
    selected = [row for row in manifest['cases'] if row['runtime_task'] == task]
    task_path = root / f'external/RoboDojo/task/RoboDojo/tasks/{task}.py'
    config_path = root / f'external/RoboDojo/task/RoboDojo/config/{task}.yml'
    tree = ast.parse(task_path.read_text())
    assert any(isinstance(node, ast.ClassDef) and node.name == task for node in tree.body)
    methods = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    horizon_assignments = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Attribute) and target.attr == 'step_lim' for target in node.targets):
            horizon_assignments.append({'line': node.lineno, 'expression': ast.unparse(node.value)})
    layout_rows = []
    for case in selected:
        layout = root / 'external/RoboDojo' / case['layout_path']
        actual = hashlib.sha256(layout.read_bytes()).hexdigest()
        assert actual == case['layout_sha256'], case['case_id']
        layout_rows.append({'case_id': case['case_id'], 'layout_sha256': actual,
                            'partition': case['partition'], 'horizon': case['horizon']})
    rows.append({'runtime_task': task, 'task_group': selected[0]['task_group'],
                 'historically_opened': selected[0]['task_group'] in opened,
                 'source_sha256': hashlib.sha256(task_path.read_bytes()).hexdigest(),
                 'config_sha256': hashlib.sha256(config_path.read_bytes()).hexdigest(),
                 'local_horizon_assignments': horizon_assignments,
                 'local_native_support_methods': sorted(methods & {'query_support_arm_traj', 'check_support_arm_stable'}),
                 'local_reward_registration': 'run_reward' in methods,
                 'cases': layout_rows, 'native_execution_admitted': False})
report = {'scope': 'static source/layout preparation only; inherited methods and runtime behavior are not proved',
          'manifest_file_sha256': hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
          'task_groups': len(groups), 'cases': len(manifest['cases']), 'runtime_variants': len(rows),
          'unopened_groups': sorted(groups - opened), 'paid_calls': 0, 'simulator_actions': 0,
          'native_admission_complete': False, 'rows': rows}
out = root / 'runs/reference-source-inventory001'
out.mkdir(exist_ok=False)
(out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({key: value for key, value in report.items() if key != 'rows'}))
