"""Observe native transformed prompts without replacing policy preprocessing."""
import hashlib
import numpy as np
from k1lab.errors import ContractError


class PromptRetentionGuard:
    def __init__(self, transform, decode, record):
        self.transform = transform
        self.decode = decode
        self.record = record

    def __call__(self, raw):
        prompt = raw.get('prompt')
        if not isinstance(prompt, str) or not prompt.strip():
            raise ContractError('nonempty native policy prompt required')
        transformed = self.transform(raw)
        ids = np.asarray(transformed['tokenized_prompt'])
        mask = np.asarray(transformed['tokenized_prompt_mask'])
        if ids.ndim != 1 or mask.shape != ids.shape or mask.dtype != np.bool_:
            raise ContractError('invalid native tokenized prompt shape/mask')
        decoded = self.decode(ids[mask].tolist())
        cleaned = prompt.strip().replace('_', ' ').replace('\n', ' ')
        retained = cleaned in decoded
        self.record({'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
            'active_tokens': int(mask.sum()), 'token_limit': int(ids.size),
            'entire_cleaned_prompt_present': retained})
        if not retained:
            raise ContractError('native policy prompt not retained after tokenization')
        return transformed
