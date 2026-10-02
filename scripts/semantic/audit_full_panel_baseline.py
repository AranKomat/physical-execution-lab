#!/usr/bin/env python3
"""Check full-cohort motor ACKs against retained predictions; not native admission."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np
from k1lab.errors import ContractError
from semantic_lab.native_io import write_json


def audit(root):
    parent = json.loads((root / 'report.json').read_text())
    if parent['status'] != 'completed_full_original_only_cohort' or parent['paid_calls'] != 0:
        raise ContractError('requires a completed no-API original-only cohort')
    results, total_predictions, total_actions = [], 0, 0
    for group in sorted(root.glob('group[0-9]')):
        report = json.loads((group / 'report.json').read_text())
        if (not report['all_rows_native_terminal'] or report['contains_controller_or_contract_error']
                or report['unstable_envs']):
            raise ContractError('group contains censored, unstable or controller-invalid samples')
        actions = {int(idx): [] for idx in report['controller_results']}
        for line in (group / 'actions.jsonl').read_text().splitlines():
            row = json.loads(line)
            idx = row['env_idx']
            if idx not in actions or row['step'] != len(actions[idx]) + 1 or row['correction']:
                raise ContractError('noncontiguous, misrouted or corrected baseline ACK')
            actions[idx].append(row)
            proposal_index, offset = divmod(row['step'] - 1, 15)
            path = group / f'source-policy-proposals/{idx}/proposal_{proposal_index:06d}.npz'
            with np.load(path, allow_pickle=False) as data:
                expected = data['actions'][offset]
            if not np.array_equal(np.asarray(row['action'], np.float32), expected):
                raise ContractError('ACK differs from its source prediction/prefix')
        metadata_files = sorted(group.glob('prediction-*.json'))
        if len(metadata_files) != report['predictions']:
            raise ContractError('prediction coverage differs from native report')
        for path in metadata_files:
            number = int(path.stem.rsplit('-', 1)[1])
            metadata = json.loads(path.read_text())
            request = group / f'request-{number:04d}.npz'
            if hashlib.sha256(request.read_bytes()).hexdigest() != metadata['request_sha256']:
                raise ContractError('retained actor input hash mismatch')
            with np.load(request, allow_pickle=False) as inputs, np.load(path.with_suffix('.npz'), allow_pickle=False) as output:
                ids = inputs['env_ids'].tolist()
                if ids != output['env_ids'].tolist() or ids != metadata['env_ids']:
                    raise ContractError('prediction reply belongs to different task rows')
                if set(inputs.files) != {'env_ids', 'steps', 'states', 'prompts',
                                        'cam_high', 'cam_left_wrist', 'cam_right_wrist'}:
                    raise ContractError('unexpected actor input fields')
                if (output['actions'].shape != (len(ids), 50, 14)
                        or not np.isfinite(output['actions']).all()):
                    raise ContractError('invalid H50 joint14 output')
                for local, idx in enumerate(ids):
                    proposal_index = int(inputs['steps'][local]) // 15
                    with np.load(group / f'source-policy-proposals/{idx}/proposal_{proposal_index:06d}.npz', allow_pickle=False) as saved:
                        if not np.array_equal(saved['actions'], output['actions'][local]):
                            raise ContractError('episode proposal was rekeyed to another task')
        total_predictions += len(metadata_files)
        for idx, result in report['controller_results'].items():
            rows = actions[int(idx)]
            if (len(rows) != result['native_steps'] or not rows[-1]['ended']
                    or rows[-1]['success'] != result['success'] or result['error'] is not None):
                raise ContractError('native terminal result disagrees with its ACK stream')
            total_actions += len(rows)
            results.append({key: result[key] for key in ('case_id', 'task', 'partition', 'success',
                                                         'native_score', 'native_steps', 'status')})
    if len(results) != 10 or {row['case_id'] for row in results} != set(parent['cases']):
        raise ContractError('cohort did not cover exactly the ten fixed cases')
    batches = [json.loads(line) for line in (root / 'worker/batches.jsonl').read_text().splitlines()]
    if not batches or not any(row['active_rows'] == 10 for row in batches):
        raise ContractError('full-task B10 inference not observed')
    return dict(scope='retained baseline routing/prefix/ACK integrity only; not native-equivalence admission',
        integrity_passed=True, benchmark_qualified=False, native_admission_pending=True,
        distinct_cases=10, native_actions=total_actions, group_prediction_requests=total_predictions,
        fused_batches=len(batches), policy_calls=sum(g['controller_results'][idx]['metrics']['policy_calls']
            for g in parent['groups'] for idx in g['controller_results']),
        successes=sum(row['success'] for row in results), paid_calls=0,
        wall_including_startup_s=parent['wall_including_startup_s'],
        warm_b10_median_s=float(np.median([row['inference_s'] for row in batches[1:] if row['active_rows'] == 10])),
        rows=results)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    result = audit(args.run)
    write_json(args.output, result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
