#!/usr/bin/env python3
import argparse,json
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--transport',choices=['file','responses','chat'],default='file')
    p.add_argument('--model',default=None);p.add_argument('--output',default='configs')
    p.add_argument('--policy-spec');p.add_argument('--service-tier',default=None);a=p.parse_args()
    root=Path(a.output);root.mkdir(parents=True,exist_ok=True)
    base={'model':a.model,'memory_scope':'current_episode_only','max_model_calls':100,'resolution':384,'delta_axis':.03,
          'native':{'k1_root':'external/k1','libero_root':'external/LIBERO-PRO','libero_config':'configs/libero.local',
                    'trust_local_state_archives':True},
          'registry_options':{'history_rounds':8,'history_image_rounds':1,'region_tools':True,
                              'interaction_feedback':True,'completion_feedback':False,'tracking_backend':'lk','tracking_device':'cpu'},
          'limits':{},'planner':{'transport':a.transport,'timeout_s':180,'max_requests':100,
                               'max_output_tokens':2048,'max_total_output_tokens':204800}}
    if a.transport in ('responses','chat'):
        base['planner'].update(base_url='https://api.openai.com/v1',api_key_env='OPENAI_API_KEY',reasoning_effort='medium')
        if a.service_tier:base['planner']['service_tier']=a.service_tier
    modes=['k1_baseline','k1_stepwise','k1_sparse']
    if a.policy_spec:modes+=['hybrid_stepwise','hybrid_sparse','policy_only']
    for mode in modes:
        c=json.loads(json.dumps(base));c['condition']=mode
        if mode.startswith('hybrid') or mode=='policy_only':
            c['policy']={'endpoint':'http://127.0.0.1:8811','spec':json.loads(Path(a.policy_spec).read_text())}
        path=root/(mode+'.json')
        if path.exists():raise SystemExit('refusing to overwrite '+str(path))
        path.write_text(json.dumps(c,indent=2)+'\n')
if __name__=='__main__':main()
