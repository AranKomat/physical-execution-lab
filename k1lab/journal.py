"""Local append-only hash chain. Integrity, not adversarial authenticity."""
from __future__ import annotations
import json
import time
from pathlib import Path
from .util import digest, plain
from .errors import ContractError


class Journal:
    def __init__(self,path,clock=time.monotonic):
        self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
        if self.path.exists(): raise FileExistsError(self.path)
        self.stream=self.path.open('x'); self.clock=clock; self.start=clock()
        self.index=0; self.head='0'*64
    def append(self,event,data):
        row={'seq':self.index,'elapsed_s':self.clock()-self.start,'event':event,
             'data':plain(data),'previous_sha256':self.head}
        row['sha256']=digest(row)
        self.stream.write(json.dumps(row,allow_nan=False)+'\n'); self.stream.flush()
        self.index+=1; self.head=row['sha256']; return row
    def close(self): self.stream.close()
    def __enter__(self): return self
    def __exit__(self,*_): self.close()


def verify(path):
    head='0'*64; n=0
    with open(path) as f:
        for line in f:
            row=json.loads(line); h=row.pop('sha256',None)
            if row.get('seq')!=n or row.get('previous_sha256')!=head or digest(row)!=h:
                raise ContractError(f'journal mismatch at row {n}')
            head=h; n+=1
    return {'events':n,'head_sha256':head}
