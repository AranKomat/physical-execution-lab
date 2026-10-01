from __future__ import annotations
import json
import os
import signal
import subprocess
import time
from pathlib import Path
from .base import bind_response
from ..errors import Unavailable, ValidationError
from ..util import atomic_json, read_json, digest, canonical


class ReferencePlanner:
    identity='scripted_fixture_policy_NOT_LLM'
    def decide(self,context,output_dir):
        if context['observation']['information_profile']!='synthetic':
            raise ValidationError('Scripted fixture policy is forbidden for native benchmarks')
        answer={'capability':'pick_place','arguments':{'target':'block','destination':'destination'},
                'max_steps':min(180,context['budget']['remaining_native_steps']),
                'decision_summary':'Authored fixture action, not model inference.'}
        if len(context['recent_receipts'])>=2:
            answer={'capability':'finish','arguments':{},'max_steps':0,
                    'decision_summary':'End bounded synthetic contract test.'}
        atomic_json(Path(output_dir)/'response.json',answer)
        return bind_response(answer,context)


class CommandPlanner:
    """One JSON request on stdin, one JSON response on stdout. No shell execution.

    This is for a TRUSTED executable, not a security sandbox for arbitrary code.
    The planner receives no simulator connection or controller credentials here.
    """
    def __init__(self,command,timeout_s=120,decoder=bind_response):
        if not isinstance(command,list) or not command or any(not isinstance(s,str) for s in command):
            raise ValidationError('planner.command must be a nonempty argv list')
        self.command=command; self.timeout_s=timeout_s; self.decoder=decoder
        self.identity='command:'+digest(command)[:16]
    def decide(self,context,output_dir):
        out=Path(output_dir)
        env={k:v for k,v in os.environ.items() if not any(w in k.upper() for w in ('KEY','TOKEN','SECRET','PASSWORD'))}
        p=subprocess.Popen(self.command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,text=True,env=env,
                           start_new_session=(os.name=='posix'))
        try:
            stdout,stderr=p.communicate(canonical(context),timeout=self.timeout_s)
        except subprocess.TimeoutExpired as e:
            if os.name=='posix': os.killpg(p.pid,signal.SIGKILL)
            else: p.kill()
            p.communicate()
            raise Unavailable('planner_command_timeout_no_retry') from e
        (out/'stderr.txt').write_text(stderr[:1_000_000])
        (out/'stdout.txt').write_text(stdout[:1_000_000])
        if p.returncode or len(stdout)>1_000_000:
            raise Unavailable(f'planner_command_failed:{p.returncode}')
        try: answer=json.loads(stdout)
        except ValueError as e: raise ValidationError('planner_stdout_not_single_json') from e
        atomic_json(out/'response.json',answer)
        return self.decoder(answer,context)


class FilePlanner:
    """External Codex can answer request files without being embedded in our runtime.

    Write response.json atomically with {request_sha256, proposal:{...}}. Each
    request directory is unique and is never reused after an uncertain timeout.
    """
    identity='external_file_planner'
    def __init__(self,queue,timeout_s=300,decoder=bind_response):
        self.queue=Path(queue); self.timeout_s=timeout_s; self.decoder=decoder
    def decide(self,context,output_dir):
        key=context['proposal_id'].replace(':','_')
        # Same case IDs recur across paired conditions; isolate their requests
        # without changing the scientific planner configuration.
        key=digest(str(Path(output_dir).resolve()))[:16]+'__'+key
        d=self.queue/key; d.mkdir(parents=True,exist_ok=False)
        h=digest(context)
        atomic_json(d/'request.json',{'request_sha256':h,'context':context})
        atomic_json(Path(output_dir)/'queue.json',{'path':str(d.resolve()),'request_sha256':h})
        deadline=time.monotonic()+self.timeout_s
        while time.monotonic()<deadline:
            p=d/'response.json'
            if p.exists():
                answer=read_json(p)
                if answer.get('request_sha256')!=h: raise ValidationError('stale_file_response')
                atomic_json(Path(output_dir)/'response.json',answer)
                return self.decoder(answer['proposal'],context)
            time.sleep(.2)
        atomic_json(d/'EXPIRED.json',{'reason':'planner_timeout','request_sha256':h})
        raise Unavailable('external_file_planner_timeout_no_retry')
