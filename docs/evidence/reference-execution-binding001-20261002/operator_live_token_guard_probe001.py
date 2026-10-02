"""Bounded same-input/source-RNG guard comparison; no simulator or API."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import time

root = Path('/root/physical-execution-lab')
sys.path[:0] = [str(root), str(root / 'external/GPT-as-Policy')]
import jax
import numpy as np
from openpi.models.tokenizer import PaligemmaTokenizer
from openpi.policies.policy_config import create_trained_policy
from hybrid_rollout.robodojo.pi05_server.checkpoint import data_contract, checkpoint_identity
from semantic_lab.token_retention import PromptRetentionGuard
from semantic_lab.protocol import code_fingerprint

out = root / 'runs/live-token-guard-probe001'
out.mkdir(exist_ok=False)
provider = json.loads((root / 'configs/local/pi05-exact-bound-001/provider.json').read_text())
checkpoint = Path(provider['checkpoint_path'])
request = root / 'runs/reference-pi05-2-002/request-0000.npz'
with np.load(request, allow_pickle=False) as data:
    raw = {'state': data['states'][0].copy(), 'prompt': str(data['prompts'][0]),
        'images': {key: np.transpose(data[key][0], (2, 0, 1)).copy()
            for key in ('cam_high', 'cam_left_wrist', 'cam_right_wrist')}}
cfg, _ = data_contract(checkpoint)
policy = create_trained_policy(cfg, checkpoint)
identity = checkpoint_identity(checkpoint)
assert identity['checkpoint_sha256'] == provider['native_checkpoint_sha256']
transform = policy._input_transform
records = []
decoder = PaligemmaTokenizer(cfg.model.max_token_len)._tokenizer.decode
start = time.perf_counter()
policy._rng = jax.random.key(0)
original = np.asarray(policy.infer(copy.deepcopy(raw))['actions'])
original_rng = jax.random.key_data(policy._rng).tolist()
policy._input_transform = PromptRetentionGuard(transform, decoder, records.append)
policy._rng = jax.random.key(0)
guarded = np.asarray(policy.infer(copy.deepcopy(raw))['actions'])
guarded_rng = jax.random.key_data(policy._rng).tolist()
report = {'scope': 'two source inferences on one retained input; not native task performance',
    'source_sha256': code_fingerprint(root), 'checkpoint_identity': identity,
    'request_sha256': hashlib.sha256(request.read_bytes()).hexdigest(),
    'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'prediction_shape': list(original.shape), 'same_rng_after': original_rng == guarded_rng,
    'prediction_exactly_equal': bool(np.array_equal(original, guarded)),
    'max_absolute_difference': float(np.max(np.abs(original-guarded))),
    'guard_records': records, 'wall_s': time.perf_counter()-start,
    'simulator_actions': 0, 'paid_calls': 0, 'native_qualification': False}
(out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report), flush=True)
assert report['same_rng_after'] and report['prediction_exactly_equal']
