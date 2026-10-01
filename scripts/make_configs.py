"""Maintainer helper to create explicit templates, never run models."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from prl.util import atomic_json,digest
from prl.manifests import write_manifest

common={"backend":"synthetic","information_profile":"synthetic","max_steps":160,
        "max_decisions":8,"max_wall_s":60,"max_vla_calls":30,"control_hz":20,
        "max_infrastructure_errors":1,"planner":{"kind":"reference"},
        "governor":{"check_every_steps":10,"stall_checks":3,"stage_warmup_steps":20},
        "call_budget":{"max_calls":100,"max_reserved_tokens":1000000}}
for mode in ('frozen','nominal','dynamic'):
    atomic_json(ROOT/'configs'/f'synthetic_{mode}.json',{**common,"mode":mode})
cases=[]
for i,fixture in enumerate(('normal','blocked','normal','blocked')):
    cases.append(dict(case_id=f'fixture.t{i}',suite='synthetic_contract',task_id=i,
                      state_index=0,policy_seed=0,split='dev',fixture=fixture,
                      state_sha256=digest({'fixture':fixture,'index':i,'version':1})))
write_manifest(ROOT/'manifests/synthetic_dev.json','synthetic','dev',cases,
               'Software contract fixtures only, no physics or neural model. Not LIBERO.')
base={"backend":"rpent","information_profile":"sensor","rpent_root":"external/RPent",
      "max_steps":520,"max_decisions":40,"max_wall_s":1800,"max_vla_calls":100,
      "max_infrastructure_errors":1,"control_hz":20,"cuda_device":0,
      "enable_policy":True,"record_video":True,"vla_endpoint":"http://127.0.0.1:8911",
      "checkpoint_id":"REPLACE_WITH_EXACT_HF_ID_AND_REVISION",
      "checkpoint_sha256":"REPLACE_WITH_WEIGHT_MANIFEST_SHA256",
      "planner":{"kind":"api","max_output_tokens":2048,"input_token_reservation":60000,
                 "timeout_s":120,"extra_request":{"temperature":0}},
      "governor":{"check_every_steps":10,"stall_checks":4,"stage_warmup_steps":20,
                  "min_progress_m":0.001,"allow_substitution":True},
      "call_budget":{"max_calls":100,"max_reserved_tokens":6500000}}
for label,mode in [('e0','frozen'),('e1','nominal'),('e2','dynamic'),('e3','dynamic_k1')]:
    atomic_json(ROOT/'configs'/f'{label}_{mode}.template.json',{**base,"mode":mode})
file_mode={**base,'mode':'dynamic','planner':{'kind':'file','queue':'runs/queue-e2','timeout_s':300}}
atomic_json(ROOT/'configs/e2_file_planner.template.json',file_mode)
priv={**base,'mode':'dynamic','information_profile':'privileged_sim'}
atomic_json(ROOT/'configs/e2_privileged_diagnostic.template.json',priv)

pins=[
 ('RPent','RLinf/RPent','d2595ff270c7d66dbb2effb803f5e6d4d8e08f82','Apache-2.0','core'),
 ('RLinf','RLinf/RLinf','88f9867ff5b3004b482d6788a871081a43098620','upstream license','core'),
 ('openpi','RLinf/openpi','a560f4dd8205b8423ecd4c8a0fabb5f54140b8a0','upstream license','core'),
 ('LIBERO','RLinf/LIBERO','a8323074d93a09e32bd898630a70531b1f51bc77','upstream license','core'),
 ('LIBERO-PRO','RLinf/LIBERO-PRO','d1e11fb181b8544487d27742c0caa3a4d46452ad','upstream license','core'),
 ('k1','Robo-Harness/k1','ee46363101fcf3ef87182fb2dbad99a92ce77fc0','MIT','k1')]
atomic_json(ROOT/'upstream.lock.json',{'format':1,'checked_date':'2026-10-01',
    'note':'Pins checked through GitHub connector; no clones were downloaded in build environment. This is not a transitive Python lock.',
    'repositories':[dict(name=n,url='https://github.com/'+repo+'.git',revision=rev,
                         license=lic,group=grp) for n,repo,rev,lic,grp in pins]})
# Paper-reproduction configuration now lives in configs/dyna/. Do not overwrite
# the PDF-reviewed protocol by regenerating the legacy sensor-first experiments.
if not (ROOT/'configs/paper_protocol.json').exists():
    atomic_json(ROOT/'configs/paper_protocol.json', {
        'title':'Legacy runner pointer', 'status':'superseded_by_pdf_review',
        'use':'python paper_run.py audit',
        'exact_replication_requirements':{},
        'source_access':'Read references/2609.40306v1.pdf and configs/dyna/paper_spec.json.'})
