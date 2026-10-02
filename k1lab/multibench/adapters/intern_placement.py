"""Explicit Intern component placement; no upstream edits or precision changes."""
from dataclasses import replace
import importlib
import os
from k1lab.errors import ContractError


def validate(config, placement):
    if not isinstance(placement, dict) or set(placement) != {'encoder_device', 'main_device', 'disable_causal_conv1d_fast_path'}:
        raise ContractError('explicit Intern component placement fields required')
    devices = (placement['encoder_device'], placement['main_device'])
    if any(not isinstance(d, str) for d in devices) or set(devices) != {'cuda:0', 'cuda:1'}:
        raise ContractError('Intern placement requires two distinct explicit CUDA devices')
    if config.get('device') != placement['main_device'] or config.get('mixed_precision') != 'bf16':
        raise ContractError('Intern placement must match the BF16 main device')
    if type(placement['disable_causal_conv1d_fast_path']) is not bool:
        raise ContractError('Intern fallback setting must be boolean')
    return devices


def place_runtime(shared, placement, torch):
    encoder, main = placement['encoder_device'], placement['main_device']
    model = shared.model
    text = model._modules.pop('text_encoder')
    vlm = model.understanding._modules.pop('vlm')
    try:
        model.to(main)
        model.device = torch.device(main)
        if hasattr(model.vae, 'set_runtime_context'):
            model.vae.set_runtime_context(device=model.device, dtype=model.torch_dtype)
        else:
            for name in ('mean', 'std'):
                value = getattr(model.vae, name, None)
                if torch.is_tensor(value):
                    setattr(model.vae, name, value.to(main))
            if hasattr(model.vae, 'mean') and hasattr(model.vae, 'std'):
                model.vae.scale = [model.vae.mean, 1.0 / model.vae.std]
        text.to(encoder)
        vlm.to(encoder)
        vlm.device = torch.device(encoder)
    finally:
        model.text_encoder = text
        model.understanding.vlm = vlm

    def move(value, device):
        if torch.is_tensor(value):
            return value.to(device)
        if isinstance(value, tuple):
            return tuple(move(v, device) for v in value)
        if isinstance(value, list):
            return [move(v, device) for v in value]
        if isinstance(value, dict):
            return {k: move(v, device) for k, v in value.items()}
        return value

    text.register_forward_pre_hook(lambda module, args, kw:
        (move(args, encoder), move(kw, encoder)), with_kwargs=True)
    text.register_forward_hook(lambda module, args, value: move(value, main))
    vlm.register_forward_hook(lambda module, args, value: move(value, main))
    model.eval()
    return replace(shared, device=main)


def load_model(source, config, placement):
    import torch
    validate(config, placement)
    if torch.cuda.device_count() < 2:
        raise ContractError('Intern split placement requires two visible GPUs')
    activate = source._activate_runtime
    patched = []
    key = 'WAM_DISABLE_CAUSAL_CONV1D_FAST_PATH'
    previous = os.environ.get(key)

    def split_activate(path):
        activate(path)
        runtime = importlib.import_module('wam.runtime.robodojo_policy')
        build = runtime.build_robotwin_shared_runtime
        patched.append((runtime, build))

        def split_build(**kwargs):
            kwargs['device'] = 'cpu'
            return place_runtime(build(**kwargs), placement, torch)
        runtime.build_robotwin_shared_runtime = split_build

    source._activate_runtime = split_activate
    os.environ[key] = '1' if placement['disable_causal_conv1d_fast_path'] else '0'
    try:
        return source.Model(config)
    finally:
        source._activate_runtime = activate
        for runtime, build in patched:
            runtime.build_robotwin_shared_runtime = build
        if previous is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = previous
