"""Prepare a prompt-mode-only full-panel ablation; no robot/API actions."""
from copy import deepcopy
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from k1lab.util import atomic_json, digest, load_json
from k1lab.multibench.manifest import seal
from semantic_lab.protocol import freeze, verify_binding

source = ROOT / 'runs/pi05-approach-standard-fallback-preparation001'
destination = ROOT / 'runs/pi05-approach-semantic-subtask-preparation001'
prior = load_json(ROOT / 'runs/pi05-full-panel-screen-new-host-freeze004.json')
panel = load_json(source / 'cases.json')
configs = {label: load_json(source / (label + '.json'))
           for label in ('original_only', 'direct', 'numeric', 'semantic')}
original = deepcopy(configs['semantic'])
config = configs['semantic']
config['name'] += '_subtask_only001'
config['prompt_mode'] = 'subtask_only'
check = deepcopy(config)
check['name'] = original['name']
check['prompt_mode'] = original['prompt_mode']
assert check == original
assert config['semantic_schedule']['allow_semantic_recovery'] is False
plan = load_json(source / 'plan.json')
plan['configs']['semantic'] = digest(config)
for slot in plan['slots']:
    if slot['approach'] == 'semantic':
        slot['condition'] = config['name']
        slot['status'] = 'missing'
plan['prompt_mode_ablation'] = dict(parent_condition=original['name'],
    changed_behavior_fields=['prompt_mode'],
    cohort_name_only_changes_are_metadata=True, previous_trials_not_replaced=True,
    scope='full-ten descriptive rollout comparison, not same-state causal obedience test')
plan = seal(plan)
frozen = freeze(ROOT, panel, list(configs.values()),
                execution_sources=prior['execution_sources']['selectors'])
for c in configs.values():
    verify_binding(ROOT, frozen, panel, c, require_execution_sources=True)
destination.mkdir(exist_ok=False)
atomic_json(destination / 'cases.json', panel, exclusive=True)
atomic_json(destination / 'plan.json', plan, exclusive=True)
for label, c in configs.items():
    atomic_json(destination / (label + '.json'), c, exclusive=True)
atomic_json(destination / 'freeze.json', frozen, exclusive=True)
print(dict(preparation=str(destination), freeze_sha256=frozen['sha256'],
           semantic_config_sha256=digest(config), native_execution=False, paid_calls=0))
