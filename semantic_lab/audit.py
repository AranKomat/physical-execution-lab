"""Check actual trace invariants, not just zero-valued metric fields."""
import json
from pathlib import Path
from k1lab.journal import verify
from k1lab.errors import ContractError
from k1lab.util import digest, load_json


def audit(root):
    root = Path(root)
    chain = verify(root / 'events.jsonl')
    events = [json.loads(s) for s in (root / 'events.jsonl').read_text().splitlines()]
    result = load_json(root / 'result.json')
    prefix = None
    ack_step = 0
    natural_prefixes = 0
    context_epochs = []
    prompts = []
    for e in events:
        kind, d = e['event'], e['data']
        if kind == 'semantic_decision' and prefix is not None:
            raise ContractError('semantic review occurred inside motor prefix')
        if kind == 'policy_proposal':
            if prefix is not None or d['step'] != ack_step:
                raise ContractError('proposal/resampling interrupted unresolved prefix')
            sem = d['diagnostics']['semantic']
            if sem['effective_prompt_sha256'] != digest(sem['effective_prompt']):
                raise ContractError('effective prompt hash mismatch')
            prefix = {'actions': d['actions'], 'native': d['natural_prefix_length'], 'executed': 0}
            context_epochs.append(sem['context']['epoch']); prompts.append(sem['effective_prompt'])
            natural_prefixes += 1
        if kind == 'control_ack':
            if prefix is None or d['step'] != ack_step + 1:
                raise ContractError('noncontiguous/unproposed action')
            if d['action'] != prefix['actions'][prefix['executed']]:
                raise ContractError('executed action differs from proposed prefix')
            prefix['executed'] += 1; ack_step += 1
        if kind == 'motor_prefix_receipt':
            if prefix is None or d['executed_steps'] != prefix['executed']:
                raise ContractError('receipt/ACK mismatch')
            if d['stop_reason'] == 'natural_boundary' and prefix['executed'] != prefix['native']:
                raise ContractError('shortened natural prefix')
            prefix = None
    if ack_step != result['native_steps']:
        raise ContractError('result action counter differs from journal')
    if result['status'] == 'native_completed' and prefix is not None:
        raise ContractError('terminal run has unresolved prefix')
    return {'journal': chain, 'actual_control_acks': ack_step, 'policy_proposals': natural_prefixes,
            'semantic_epochs_seen_by_motor': sorted(set(context_epochs)),
            'distinct_effective_prompts': len(set(prompts)), 'prefix_cadence_verified': True,
            'complete_native_result': result['status'] == 'native_completed',
            'evidence_kind': result['evidence_kind'], 'robot_competence_claim': False}
