#!/usr/bin/env python3
"""Serve RPent pi05_libero with 10-action chunks and a byte-level attestation.

Requires the external GPU host. Does not fine-tune or select weights implicitly.
A hash proves which bytes were requested/loaded, not parity with the authors'
unpublished exact checkpoint revision or sampler configuration.
"""
import argparse
import os
import sys
import copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from prl.util import read_json,file_digest,atomic_json,digest
from prl.errors import ValidationError
from prl.backends.rpent import load_rpent


def verified_manifest(model_path,manifest_path):
    model=Path(model_path).resolve();manifest=read_json(manifest_path)
    body={k:v for k,v in manifest.items() if k!='sha256'}
    if digest(body)!=manifest.get('sha256'):raise ValidationError('checkpoint_manifest_tampered')
    if not manifest.get('files'):raise ValidationError('empty_checkpoint_manifest')
    for row in manifest['files']:
        p=(model/row['path']).resolve()
        if not p.is_relative_to(model):raise ValidationError('checkpoint_path_escape')
        if not p.is_file() or file_digest(p)!=row['sha256']:raise ValidationError('checkpoint_bytes_changed:'+row['path'])
    return manifest['sha256']


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rpent-root',default='external/RPent');p.add_argument('--model-path',required=True)
    p.add_argument('--checkpoint-manifest',required=True);p.add_argument('--checkpoint-id',required=True)
    p.add_argument('--attestation-out',required=True);p.add_argument('--cuda-device',default='0')
    p.add_argument('--port',type=int,default=8911)
    args=p.parse_args();os.environ['CUDA_VISIBLE_DEVICES']=args.cuda_device
    if 'libero130' in args.checkpoint_id.lower():raise ValidationError('RLinf_fullshot_is_not_the_paper_public_PI_checkpoint')
    h=verified_manifest(args.model_path,args.checkpoint_manifest);load_rpent(args.rpent_root)
    import rpent.robots.components.pi05_vla_server as upstream
    preset=copy.deepcopy(upstream.PI05_EMBODIMENTS['libero'])
    preset['num_action_chunks']=10;preset['openpi']['action_chunk']=10
    upstream.PI05_EMBODIMENTS['libero']=preset
    facade=upstream.Pi05VLAFacade(model_path=args.model_path,embodiment='libero')
    body={'status':'loaded','checkpoint_id':args.checkpoint_id,'checkpoint_sha256':h,
          'action_chunk':10,'config_name':'pi05_libero','loader':'RPent pinned Pi05VLAFacade',
          'preset':preset,'pid':os.getpid(),'paper_exact_checkpoint_parity':'not established'}
    facade._rpc['vla.get_prl_attestation']=lambda:body
    if hasattr(facade,'_readonly_methods'):facade._readonly_methods.add('vla.get_prl_attestation')
    atomic_json(Path(args.attestation_out),body)
    facade.serve(transport='http',host='127.0.0.1',port=args.port,parent_watch=False)

if __name__=='__main__':main()
