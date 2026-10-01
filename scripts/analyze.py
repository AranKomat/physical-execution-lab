#!/usr/bin/env python3
import argparse,json,csv,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from k1lab.util import load_json,atomic_json
from k1lab.evaluation import compare,full_rows

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--left',default='k1_baseline')
    p.add_argument('--right',default='k1_sparse');p.add_argument('--partition',choices=['dev','test'],default='dev');a=p.parse_args()
    root=Path(a.run);outcomes=load_json(root/'outcomes.json')
    if (root/'manifest.json').exists():cases=[c for c in load_json(root/'manifest.json')['cases'] if c['partition']==a.partition]
    else:cases=load_json(root/'cases.json')
    result=compare(cases,outcomes[a.left],outcomes[a.right])
    atomic_json(root/f'comparison_{a.left}_vs_{a.right}.json',result)
    with (root/'outcomes.csv').open('w',newline='') as f:
        fields=['condition','case_id','task_key','native_success','native_steps','horizon','elapsed_seconds','llm_calls','policy_calls','termination']
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');writer.writeheader()
        for condition,rows in outcomes.items():
            for row in full_rows(cases,rows):writer.writerow({'condition':condition,**row})
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
