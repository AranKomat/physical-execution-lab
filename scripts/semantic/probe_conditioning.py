#!/usr/bin/env python3
"""One recorded-observation prompt probe. No simulator motion or paid model call.

This is a development wiring check, NOT a robot success test. It uses a manually
supplied language goal and cannot be counted as the zero-shot planner condition.
Do not fake source ACKs; an unused proposal is cancelled explicitly.
"""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from k1lab.util import atomic_json, load_json
from k1lab.multibench.manifest import resolved_config
from k1lab.multibench.transport import decode_obs
from semantic_lab.cli import policy
from semantic_lab.protocol import require_live_base
from semantic_lab.contracts import SemanticContext


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--policy-config', required=True)
    p.add_argument('--observation', required=True)
    p.add_argument('--subtask', required=True)
    p.add_argument('--prompt-mode', choices=['original_only','task_plus_subtask','subtask_only'], required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--allow-policy', action='store_true')
    a = p.parse_args()
    root = Path(__file__).resolve().parents[2]
    require_live_base(root)
    obs = decode_obs(load_json(a.observation))
    if obs.step != 0:
        raise ValueError('use a reset observation, not a fabricated partial source history')
    config = resolved_config({'policy': load_json(a.policy_config)})['policy']
    pol = policy(config, a.allow_policy)
    try:
        pol.reset()
        pol.set_context(SemanticContext(obs.instruction, a.subtask, 0, a.prompt_mode))
        pol.observe(obs)
        proposal = pol.propose(obs)
        receipt = pol.finish_prefix(0, 'abort')
        atomic_json(a.output, {'observation_sha256': obs.stamp,
            'model_input_prompt': proposal.diagnostics['semantic'],
            'actions': [x.json() for x in proposal.actions], 'cancellation': receipt,
            'actual_native_actions': 0, 'not_proof_of_language_obedience': True,
            'tokenizer_truncation_audit_still_required': True}, exclusive=True)
    finally:
        pol.close()

if __name__ == '__main__': main()
