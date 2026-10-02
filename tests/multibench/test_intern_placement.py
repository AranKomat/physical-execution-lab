from dataclasses import dataclass
from types import SimpleNamespace
import pytest
from k1lab.errors import ContractError
from k1lab.multibench.adapters.intern_placement import validate, place_runtime


def settings():
    return {'encoder_device':'cuda:0','main_device':'cuda:1',
            'disable_causal_conv1d_fast_path':True}


@pytest.mark.parametrize('patch',[{'main_device':'cuda:0'}, {'encoder_device':'cpu'},
    {'main_device':'cuda'}, {'disable_causal_conv1d_fast_path':1}, {'unknown':True}])
def test_placement_rejects_ambiguous_or_unqualified_settings(patch):
    with pytest.raises(ContractError):
        validate({'device':'cuda:1','mixed_precision':'bf16'}, settings() | patch)


def test_placement_requires_explicit_matching_device_and_precision():
    assert validate({'device':'cuda:1','mixed_precision':'bf16'},settings())==('cuda:0','cuda:1')
    for cfg in ({'device':'cuda','mixed_precision':'bf16'}, {'device':'cuda:1','mixed_precision':'fp16'}):
        with pytest.raises(ContractError):validate(cfg,settings())


class Module:
    def __init__(self):self._modules={};self.moves=[];self.pre=[];self.post=[]
    def __setattr__(self,k,v):
        object.__setattr__(self,k,v)
        if isinstance(v,Module):self._modules[k]=v
    def to(self,device):self.moves.append(device);return self
    def eval(self):return self
    def register_forward_pre_hook(self,hook,**kwargs):self.pre.append(hook)
    def register_forward_hook(self,hook):self.post.append(hook)


@dataclass(frozen=True)
class Runtime:
    model: object
    device: str


def test_frozen_runtime_replaced_and_encoder_boundaries_preserved():
    m=Module();m.text_encoder=Module();m.understanding=Module();m.understanding.vlm=Module()
    m.vae=SimpleNamespace(set_runtime_context=lambda **kw: None);m.torch_dtype='bf16'
    old=Runtime(m,'cpu');torch=SimpleNamespace(device=str,is_tensor=lambda v:False)
    new=place_runtime(old,settings(),torch)
    assert old.device=='cpu' and new.device=='cuda:1' and new.model is m
    assert m.moves==['cuda:1'] and m.text_encoder.moves==['cuda:0']
    assert m.understanding.vlm.moves==['cuda:0'] and m.understanding.vlm.device=='cuda:0'
    assert len(m.text_encoder.pre)==len(m.text_encoder.post)==len(m.understanding.vlm.post)==1
    assert m.text_encoder.pre[0](None,('prompt',),{'mask':'mask'})==(('prompt',),{'mask':'mask'})
    assert m.understanding.vlm.post[0](None,(),('features','mask'))==('features','mask')
