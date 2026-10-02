"""Replay retained source inputs through the installed transforms, CPU only."""
import hashlib
import inspect
import json
from pathlib import Path
import sys

import numpy as np

root = Path('/root/physical-execution-lab')
sys.path[:0] = [str(root), str(root / 'external/GPT-as-Policy')]
from hybrid_rollout.robodojo.pi05_server.checkpoint import data_contract
from openpi import transforms
from openpi.models.tokenizer import PaligemmaTokenizer
from openpi.policies import policy_config

out = root / 'runs/reference-pi05-2-002'
assert (out / 'report.json').exists(), 'only replay a terminal trial'
provider = json.loads((root / 'configs/local/pi05-exact-bound-001/provider.json').read_text())
cfg, dc = data_contract(Path(provider['checkpoint_path']))
# Same input sequence as create_trained_policy; no model/params are loaded.
transform = transforms.compose([
    transforms.InjectDefaultPrompt(None), *dc.data_transforms.inputs,
    transforms.Normalize(dc.norm_stats, use_quantiles=dc.use_quantile_norm),
    *dc.model_transforms.inputs,
])
tokenizer = PaligemmaTokenizer(cfg.model.max_token_len)._tokenizer
rows = []
for path in sorted(out.glob('request-*.npz')):
    with np.load(path, allow_pickle=False) as data:
        for i, env in enumerate(data['env_ids'].tolist()):
            prompt = str(data['prompts'][i])
            raw = {'state': data['states'][i].copy(), 'prompt': prompt,
                   'images': {key: np.transpose(data[key][i], (2, 0, 1)).copy()
                              for key in ('cam_high', 'cam_left_wrist', 'cam_right_wrist')}}
            transformed = transform(raw)
            ids = np.asarray(transformed['tokenized_prompt'])
            mask = np.asarray(transformed['tokenized_prompt_mask'])
            decoded = tokenizer.decode(ids[mask].tolist())
            cleaned = prompt.strip().replace('_', ' ').replace('\n', ' ')
            rows.append({'request': path.name, 'request_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                         'env_idx': env, 'step': int(data['steps'][i]),
                         'effective_prompt': prompt, 'decoded_active_tokens': decoded,
                         'active_tokens': int(mask.sum()), 'max_token_len': cfg.model.max_token_len,
                         'entire_cleaned_prompt_present': cleaned in decoded})
result = {'scope': 'offline exact input-transform replay of retained requests; not live token capture or obedience',
          'model_weights_loaded': False, 'simulator_actions': 0, 'paid_calls': 0,
          'policy_factory_source_sha256': hashlib.sha256(inspect.getsource(policy_config.create_trained_policy).encode()).hexdigest(),
          'all_delivered_prompts_retained': all(row['entire_cleaned_prompt_present'] for row in rows),
          'rows': rows}
with (out / 'tokenizer-replay.json').open('x') as stream:
    json.dump(result, stream, indent=2)
    stream.write('\n')
print(json.dumps({key: value for key, value in result.items() if key != 'rows'}))
