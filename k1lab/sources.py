"""Pinned integration identities. No network on import."""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path
from .errors import ContractError,Unavailable

K1_REV='ee46363101fcf3ef87182fb2dbad99a92ce77fc0'
LIBERO_REV='eafdb809426b13153aa1e4c42d6601844217dfec'
RPENT_REV='d2595ff270c7d66dbb2effb803f5e6d4d8e08f82'


def checked_checkout(root,expected,required):
    root=Path(root).expanduser().resolve()
    if not (root/required).is_file():raise Unavailable(f'missing {root/required}; fetch pinned upstream')
    try:
        head=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
        dirty=subprocess.check_output(['git','-C',str(root),'status','--porcelain','--untracked-files=no'],text=True).strip()
    except (OSError,subprocess.CalledProcessError) as e:raise Unavailable('upstream must be a git checkout') from e
    if head!=expected or dirty:raise ContractError(f'upstream revision/cleanliness mismatch: {root} {head} dirty={bool(dirty)}')
    return root


def load_k1(root):
    root=checked_checkout(root,K1_REV,'src/robo_harness/runtime.py')
    src=root/'src'
    if str(src) not in sys.path:sys.path.insert(0,str(src))
    import robo_harness.runtime as runtime
    if Path(runtime.__file__).resolve()!=src/'robo_harness/runtime.py':raise ContractError('imported a different K1 install')
    import inspect
    if not {'registry_class','client_factory'}.issubset(inspect.signature(runtime.run_agent).parameters):
        raise ContractError('K1 extension seams changed')
    return runtime
