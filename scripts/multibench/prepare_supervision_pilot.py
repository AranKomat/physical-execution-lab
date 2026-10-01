#!/usr/bin/env python3
"""Prepare fresh development conditions using one explicit loopback paid route."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from k1lab.util import atomic_json,load_json


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bound-root',required=True);p.add_argument('--output',required=True)
    p.add_argument('--benchmark',choices=('robodojo','robocasa365'),default='robodojo')
    a=p.parse_args();source=Path(a.bound_root);out=Path(a.output)
    out.mkdir(parents=True,exist_ok=False)
    prefix='robodojo_g05' if a.benchmark=='robodojo' else 'robocasa365_xiaomi'
    for name in ('motor_only','review_every_chunk','sparse'):
        cfg=load_json(source/f'{prefix}_{name}.json')
        if cfg['benchmark']!=a.benchmark:raise ValueError('bound benchmark mismatch')
        if a.benchmark=='robodojo':
            cfg['environment']['gpt_as_policy_root']=str(Path(__file__).resolve().parents[2]/'external/GPT-as-Policy')
        cfg['model'].update(base_url='http://127.0.0.1:19861',api_key_env='K1_RELAY_TOKEN',
            max_requests=75,max_total_output_tokens=153600)
        cfg['max_reviews']=75;cfg['wall_limit_s']=2400
        cfg['paid_route']={'model':'openai/gpt-6.1-sol','provider':'openai/flex',
            'service_tier':'flex','local_cap_usd':'3','shared_ceiling_usd':'85',
            'retry':False,'credentials_location':'operator Mac, never GPU host',
            'request_normalization':{'remove':['parallel_tool_calls'],
                'reason':'not advertised by selected route; local actor requires exactly one function call'}}
        atomic_json(out/f'{prefix}_{name}.json',cfg,exclusive=True)


if __name__=='__main__':main()
