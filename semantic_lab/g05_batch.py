"""Source fused G05 inference, scoped to the released one-observation checkpoint."""
import hashlib
import numpy as np
from k1lab.errors import ContractError
from k1lab.multibench.adapters.xpolicylab import decode_xpl


class G05TokenGuard:
    def __init__(self, encode, decode, pad_token_id, record):
        self.encode, self.decode = encode, decode
        self.pad_token_id, self.record = pad_token_id, record
        self.prompts = []
        self.calls = 0

    def __call__(self, *args, **kwargs):
        result = self.encode(*args, **kwargs)
        ids, mask = result
        ids = ids.detach().cpu().numpy()
        mask = mask.detach().cpu().numpy()
        if ids.ndim != 2 or mask.shape != ids.shape or len(ids) != len(self.prompts):
            raise ContractError('G05 actual token rows do not match the fused request')
        for prompt, row in zip(self.prompts, ids):
            cleaned = ' '.join(prompt.split())
            decoded = ' '.join(self.decode(row.tolist()).split())
            retained = bool(cleaned) and cleaned in decoded
            self.record(dict(prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
                active_tokens=int(np.count_nonzero(row != self.pad_token_id)),
                token_limit=int(row.size), entire_cleaned_prompt_present=retained,
                boundary='source policy.processor.encode_inference output'))
            if not retained:
                raise ContractError('G05 native policy prompt not retained after tokenization')
        self.calls += 1
        return result


class G05Batch:
    def __init__(self, model, provider, capacity, record):
        processors = getattr(model.processor, 'processors', None)
        resolved = model.processor
        if processors is not None:
            if set(processors) != {'robodojo'}:
                raise ContractError('G05 fused path requires one bound RoboDojo processor')
            resolved = processors['robodojo']
        # The inspected source history function defaults to one observation for
        # a registry. Also inspect its actual subprocessor, not only that default.
        if (getattr(model.processor, 'num_obs_steps', 1) != 1
                or getattr(resolved, 'num_obs_steps', None) != 1
                or model.action_steps != 16 or model.inference_batch_size != capacity
                or provider['model_config']['inference_batch_size'] != capacity):
            raise ContractError('G05 fused path requires bound B-capacity and num_obs_steps=1/H16')
        self.model, self.provider, self.capacity = model, provider, capacity
        self.calls = {}
        processor = model.policy.processor
        self.guard = G05TokenGuard(processor.encode_inference, processor.tokenizer.decode,
                                   processor.tokenizer.pad_token_id, record)
        processor.encode_inference = self.guard
        model.reset()

    def infer(self, episode_ids, raws):
        if len(raws) != self.capacity or len(set(episode_ids)) != len(raws):
            raise ContractError('G05 requires the fixed fused capacity and unique episode keys')
        observations = []
        for ident, raw in zip(episode_ids, raws):
            state = np.asarray(raw['state'])
            if state.shape != (14,):
                raise ContractError('G05 requires dual X5 joint14 state')
            observations.append(dict(env_idx=ident, instruction=raw['prompt'],
                state={key: state[offset+begin:offset+end].copy()
                    for arm, offset in (('left', 0), ('right', 7))
                    for key, begin, end in ((f'{arm}_arm_joint_state', 0, 6),
                                           (f'{arm}_ee_joint_state', 6, 7))},
                vision={name: {'color': np.transpose(raw['images'][name], (1, 2, 0)).copy()}
                    for name in ('cam_high', 'cam_left_wrist', 'cam_right_wrist')}))
        self.guard.prompts = [raw['prompt'] for raw in raws]
        before = self.guard.calls
        self.model.update_obs_batch(observations)
        chunks = self.model.get_action_batch()
        if self.guard.calls != before + 1 or len(chunks) != self.capacity:
            raise ContractError('G05 did not perform one fused tokenization/inference batch')
        actions, raw_actions, clips = [], [], []
        for ident, chunk in zip(episode_ids, chunks):
            converted, clipped = decode_xpl(chunk, 'x5_joint14', self.provider['gripper_clip'])
            if len(converted) != 16:
                raise ContractError('G05 source exposed action horizon changed')
            raw_actions.append(np.stack([np.concatenate([np.asarray(command[key]).reshape(-1)
                for arm in ('left', 'right')
                for key in (f'{arm}_arm_joint_state', f'{arm}_ee_joint_state')]) for command in chunk]))
            actions.append(np.stack([action.values for action in converted]))
            clips.append(clipped)
            self.calls[ident] = self.calls.get(ident, 0) + 1
        return dict(actions=np.stack(actions), raw_actions=np.stack(raw_actions), gripper_clips=clips)
