import os
os.environ.update(CUDA_VISIBLE_DEVICES='0,1', WAM_DISABLE_CAUSAL_CONV1D_FAST_PATH='1',
                  OMP_NUM_THREADS='4', MKL_NUM_THREADS='4', HF_HUB_OFFLINE='1',
                  TRANSFORMERS_OFFLINE='1')
import gc
import importlib
import json
from pathlib import Path
import sys
import time
import traceback
from dataclasses import replace
import torch

root = Path('/root/physical-execution-lab')
sys.path.insert(0, str(root))
from k1lab.util import load_json, atomic_json, file_sha
from k1lab.multibench.adapters.xpolicylab import XPolicyModel, REV
from k1lab.multibench.adapters.robodojo import check_checkout
from k1lab.multibench.transport import decode_obs

out = root / 'runs/intern-two-gpu-probe-002'
out.mkdir(exist_ok=False)
cfg = load_json(root / 'configs/local/intern-seed0-bound/provider.json')
cfg['model_config']['device'] = 'cuda:1'
check_checkout(cfg['xpolicylab_root'], REV)
sys.path.insert(0, str(Path(cfg['xpolicylab_root']).parent))
source = importlib.import_module('XPolicyLab.policy.InternW0_delta.model')
activate = source._activate_runtime
placement = {}

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

def split_activate(path):
    activate(path)
    runtime = importlib.import_module('wam.runtime.robodojo_policy')
    build = runtime.build_robotwin_shared_runtime
    def split_build(**kwargs):
        kwargs['device'] = 'cpu'
        shared = build(**kwargs)
        m = shared.model
        text = m._modules.pop('text_encoder')
        vlm = m.understanding._modules.pop('vlm')
        placement.update(text_parameter_bytes=sum(p.numel()*p.element_size() for p in text.parameters()),
                         vlm_parameter_bytes=sum(p.numel()*p.element_size() for p in vlm.parameters()),
                         main_parameter_bytes=sum(p.numel()*p.element_size() for p in m.parameters()))
        m.to('cuda:1')
        m.device = torch.device('cuda:1')
        shared = replace(shared, device='cuda:1')
        if hasattr(m.vae, 'set_runtime_context'):
            m.vae.set_runtime_context(device=m.device, dtype=m.torch_dtype)
        else:
            for name in ('mean', 'std'):
                if torch.is_tensor(getattr(m.vae, name, None)):
                    setattr(m.vae, name, getattr(m.vae, name).to(m.device))
            if hasattr(m.vae, 'mean') and hasattr(m.vae, 'std'):
                m.vae.scale = [m.vae.mean, 1.0 / m.vae.std]
        text.to('cuda:0')
        vlm.to('cuda:0')
        vlm.device = torch.device('cuda:0')
        m.text_encoder = text
        m.understanding.vlm = vlm
        text.register_forward_pre_hook(lambda module, args, kw:
            (move(args, 'cuda:0'), move(kw, 'cuda:0')), with_kwargs=True)
        text.register_forward_hook(lambda module, args, value: move(value, 'cuda:1'))
        vlm.register_forward_hook(lambda module, args, value: move(value, 'cuda:1'))
        shared.model.eval()
        gc.collect()
        print(json.dumps({'event':'split_loaded', 'placement':placement}), flush=True)
        return shared
    runtime.build_robotwin_shared_runtime = split_build
source._activate_runtime = split_activate

def sync():
    for i in (0, 1):
        torch.cuda.synchronize(i)

def memory():
    return {str(i): {'peak_allocated_bytes':torch.cuda.max_memory_allocated(i),
                     'peak_reserved_bytes':torch.cuda.max_memory_reserved(i),
                     'allocated_bytes':torch.cuda.memory_allocated(i)} for i in (0, 1)}

report = {'schema':'multibench.intern_two_gpu_probe.v1', 'placement_variant':True,
          'model_config':cfg['model_config'], 'source_revision':REV,
          'probe_sha256':file_sha(Path(__file__)), 'paid_calls':0,
          'native_actions_executed':0, 'temporal_mode':'reset per independent saved observation',
          'qualification':'load/inference probe only; no native competence or steady-state timing claim'}
stage = 'construction'
try:
    start = time.perf_counter()
    policy = XPolicyModel(cfg)
    sync()
    report['load_seconds'] = time.perf_counter() - start
    report['loaded_memory'] = memory()
    report['placement'] = placement
    observation = decode_obs(load_json(root / 'runs/capture-005/observation.wire.json'))
    report['observation_stamp'] = observation.stamp
    timings = []
    lengths = []
    stage = 'inference'
    for i in range(4):
        policy.reset()
        sync()
        start = time.perf_counter()
        with torch.inference_mode():
            proposal = policy.propose(observation)
        sync()
        elapsed = time.perf_counter() - start
        timings.append(elapsed)
        lengths.append(len(proposal.actions))
        print(json.dumps({'event':'inference_completed','index':i,'seconds':elapsed,
                          'actions':lengths[-1],'memory':memory()}), flush=True)
    report.update(status='passed', cold_inference_seconds=timings[0],
                  warm_inference_seconds=timings[1:], action_lengths=lengths,
                  peak_memory=memory(), last_proposal=proposal.json())
except Exception as exc:
    report.update(status='failed', stage=stage, error_type=type(exc).__name__,
                  error=str(exc), traceback=traceback.format_exc(),
                  placement=placement, peak_memory=memory())
    print(json.dumps({'event':'failed','stage':stage,'error':str(exc)}), flush=True)
    raise
finally:
    atomic_json(out / 'result.json', report, exclusive=True)
