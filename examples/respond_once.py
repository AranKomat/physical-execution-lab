"""Inspect a pending FilePlanner request, atomically submit a human-authored JSON.

Usage: python examples/respond_once.py queue/request_dir my_proposal.json
The external coding agent may write the same format itself. This is not a policy.
"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from prl.util import read_json,atomic_json
from prl.planners.base import bind_response
request_dir=Path(sys.argv[1]);request=read_json(request_dir/'request.json')
if (request_dir/'EXPIRED.json').exists():raise SystemExit('Request expired; do not retry it.')
proposal=read_json(sys.argv[2]);bind_response(proposal,request['context'])
if (request_dir/'response.json').exists():raise SystemExit('Response already exists')
atomic_json(request_dir/'response.json',{'request_sha256':request['request_sha256'],'proposal':proposal})
