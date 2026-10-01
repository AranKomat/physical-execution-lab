"""Preserve the source RoboDojo OpenPI/JAX config, image order and identity checks."""
from __future__ import annotations
from pathlib import Path
import sys
import numpy as np
from k1lab.errors import ContractError
from ..types import Action,Proposal,PolicyIdentity
from .robodojo import check_checkout,REV

class Pi05Policy:
    def __init__(self,config,client=None):
        self.config=config;self.identity=PolicyIdentity(**config['identity'])
        if self.identity.action_space!='x5_joint14':raise ContractError('pi05 RoboDojo is joint14')
        self.output=Path(config['artifact_dir']).resolve();self.output.mkdir(parents=True,exist_ok=True)
        if client is None:
            root=check_checkout(config['gpt_as_policy_root'],REV);sys.path.insert(0,str(root))
            from hybrid_rollout.robodojo.pi05_server.client import Pi05Client
            client=Pi05Client(int(config['port']),config['checkpoint_path'])
        self.client=client;self.n=0
        # The native server hash has a different scope than our complete file-manifest
        # hash; bind both rather than claiming they are identical.
        expected=config.get('native_checkpoint_sha256')
        if expected is not None and client.metadata.get('checkpoint_sha256')!=expected:
            raise ContractError('source-server checkpoint hash differs')
    def reset(self):pass # stateless action generation; server index persists by contract
    def observe(self,obs):pass
    def invalidate(self,reason):pass # suffix held by caller only, never by source client
    def propose(self,obs):
        path=self.output/f'proposal_{self.n:06d}.npz';self.n+=1
        if path.exists():raise FileExistsError(path)
        raw={**obs.rgb,'states':obs.state,'instruction':obs.instruction}
        actions,meta=self.client.infer(raw,path)
        return Proposal(obs.stamp,obs.step,self.identity.identity,[Action('x5_joint14',a) for a in actions],meta)
    def synchronize(self):pass # blocking socket returns CPU action arrays
    def memory(self):return {'scope':'JAX server memory not collected by client'}
    def close(self):self.client.close()
