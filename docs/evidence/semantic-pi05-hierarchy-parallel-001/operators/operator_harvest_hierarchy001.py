import json
import argparse
from pathlib import Path
import sys
import numpy as np

root = Path('/root/physical-execution-lab')
sys.path.insert(0, str(root))
from k1lab.util import load_json, atomic_json
from semantic_lab.audit import audit
from semantic_lab.contracts import SemanticContext

p = argparse.ArgumentParser()
p.add_argument('--condition', choices=('motor_only', 'task_plus_subtask', 'subtask_only'), default='task_plus_subtask')
p.add_argument('--case-id', default='build_tower__standard__g0__l0')
p.add_argument('--cohort', choices=('semantic-pi05-hierarchy-001', 'semantic-pi05-hierarchy-parallel-001'), default='semantic-pi05-hierarchy-001')
a = p.parse_args()
condition = a.condition
out = root / 'runs' / a.cohort / condition / a.case_id
controller = out / 'episode/controller'
result = load_json(controller / 'result.json')
report = audit(controller)
rows = [json.loads(s) for s in (controller / 'events.jsonl').read_text().splitlines()]
proposals = [r['data'] for r in rows if r['event'] == 'policy_proposal']
sessions = list((out / 'source-policy-proposals').glob('session-*'))
assert len(sessions) == 1
assert [p['diagnostics']['inference_index'] for p in proposals] == list(range(len(proposals)))
for i, p in enumerate(proposals):
    assert p['natural_prefix_length'] == 15 and len(p['actions']) == 50
    with np.load(sessions[0] / f'proposal_{i:06d}.npz', allow_pickle=False) as data:
        assert np.array_equal(data['actions'], np.asarray([a['values'] for a in p['actions']]))
    sem = p['diagnostics']['semantic']
    assert sem['context']['prompt_mode'] == ('original_only' if condition == 'motor_only' else condition)
    assert sem['history_reset'] is False
    assert sem['effective_prompt'] == SemanticContext(**sem['context']).effective_prompt
source = load_json(out / 'source-identity.json')
provider = load_json(out / 'provider.json')
assert source['checkpoint_sha256'] == provider['native_checkpoint_sha256']
assert result['metrics']['unresolved_policy_actions'] == 0
complete = result['status'] == 'native_completed'
if complete:
    outcome = load_json(out / 'episode/native/evaluation_outcome.json')
    assert outcome['complete'] is True
    assert result['success'] == outcome['native_success']
    assert result['native_score'] == outcome['native_score']
    assert result['native_steps'] == outcome['native_control_steps']
    native = load_json(out / 'episode/native/native_evaluation.json')
    assert native['registered'] is True
    assert any(n > 0 for key in ('check_list', 'final_check_list')
        for n in native['condition_group_counts'].get(key, []))
if condition == 'motor_only':
    assert result['metrics']['semantic_calls'] == 0
    original = load_json(controller / 'run.json')['original_task']
    assert all(p['diagnostics']['semantic']['effective_prompt'] == original for p in proposals)
report.update(source_npz_proposals_match_journal=True, fresh_inference_indices=True,
    checkpoint_identity_verified=True, controller_evaluator_agree=True if complete else None,
    terminal_status=result['status'], source_proposals=len(proposals),
    no_history_reset=True, prediction_horizon=50, native_prefix=15,
    native_completion_nonvacuous=True if complete else None)
atomic_json(out / 'offline-audit.json', report, exclusive=True)
print(json.dumps(report), flush=True)
