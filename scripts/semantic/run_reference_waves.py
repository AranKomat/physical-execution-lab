#!/usr/bin/env python3
"""Own bounded concurrent source-bound reference waves and one shared motor runtime."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from k1lab.errors import ContractError
from k1lab.util import atomic_json, load_json, digest
from semantic_lab.protocol import verify_binding
from scripts.multibench.launch_robodojo_case import stop_child


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepared', type=Path, required=True)
    parser.add_argument('--freeze', type=Path, required=True)
    parser.add_argument('--case-ids', nargs='+', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--tag-base', type=int, required=True)
    parser.add_argument('--development-subset', action='store_true',
                        help='Historical subset utility; not the full-task comparison runner')
    args = parser.parse_args()
    if not args.development_subset:
        raise ContractError('subset runner is not the owner-requested full-task concurrent comparison; do not launch it as that campaign')
    panel = load_json(args.prepared/'cases.json')
    plan = load_json(args.prepared/'plan.json')
    config_path = args.prepared/'original_only.json'
    config = load_json(config_path)
    frozen = load_json(args.freeze)
    if len(args.case_ids) != len(set(args.case_ids)) or not 1 <= len(args.case_ids) <= 2:
        raise ContractError('initial wave pair requires one or two unique fixed cases')
    if config['mode'] != 'motor_only' or digest(config) != plan['configs']['original_only']:
        raise ContractError('initial reference waves are the prepared no-API baseline only')
    if panel['sha256'] != plan['manifest_sha256']:
        raise ContractError('comparison panel changed')
    cases = {row['case_id']: row for row in panel['cases']}
    selected = [cases[case_id] for case_id in args.case_ids]
    if any(c['task_group'] not in ('classify_objects', 'build_tower', 'arrange_largest_number') for c in selected):
        raise ContractError('unopened tasks require separate native admission')
    verify_binding(ROOT, frozen, panel, config, require_execution_sources=True)
    usage = subprocess.check_output(['nvidia-smi','--query-gpu=memory.used','--format=csv,noheader,nounits'], text=True)
    if not all(int(x) < 500 for x in usage.splitlines()):
        raise ContractError('preserve active GPU work')
    if __import__('shutil').disk_usage(ROOT).free < 2*1024**3:
        raise ContractError('less than 2GiB free before bounded two-case wave')
    args.output.mkdir(parents=True, exist_ok=False)
    broker = args.output/'shared-worker'
    broker.mkdir()
    children, streams = [], []
    report = dict(status='started', condition=config['name'], paid_calls=0,
        cases=args.case_ids, source_freeze_sha256=frozen['sha256'], comparison_plan_sha256=plan['sha256'],
        wave_outputs={}, policy_runtimes=1, simulator_processes=len(selected),
        native_qualification=False, no_case_replacement_or_automatic_retry=True)
    started = time.monotonic()
    try:
        log = (args.output/'shared-worker.log').open('x'); streams.append(log)
        service = subprocess.Popen([str(ROOT/'.venv-pi05/bin/python'), '-u',
            str(ROOT/'runs/operator_pi05_multifamily_worker001.py'),'--root',str(broker)],
            cwd=ROOT, env=dict(os.environ, CUDA_VISIBLE_DEVICES='1', XLA_PYTHON_CLIENT_PREALLOCATE='false',
                OMP_NUM_THREADS='4', MKL_NUM_THREADS='4'), stdout=log, stderr=subprocess.STDOUT,
            start_new_session=True)
        children.append(service)
        deadline = time.monotonic()+900
        while not (broker/'service-ready.json').exists():
            if service.poll() is not None: raise RuntimeError('shared model startup failed; no retry')
            if time.monotonic() > deadline: raise TimeoutError('shared model readiness')
            time.sleep(.2)
        waves = []
        for i, case in enumerate(selected):
            tag = str(args.tag_base+i)
            out = ROOT/f'runs/reference-pi05-1-{tag}'
            if out.exists(): raise FileExistsError(out)
            stream = (args.output/(case['task_group']+'.log')).open('x'); streams.append(stream)
            command = ['/root/miniconda3/envs/RoboDojo/bin/python3.11','-u',
                str(ROOT/'runs/operator_reference_rollout001.py'),'--policy','pi05','--num-envs','1',
                '--steps',str(case['horizon']),'--tag',tag,'--task',case['runtime_task'],
                '--case-manifest',str(args.prepared/'cases.json'),'--case-ids',case['case_id'],
                '--semantic-config',str(config_path),'--execution-freeze',str(args.freeze),
                '--shared-worker-root',str(broker)]
            child = subprocess.Popen(command,cwd=ROOT,env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',
                OMNI_KIT_ACCEPT_EULA='YES',OMP_NUM_THREADS='4',MKL_NUM_THREADS='4'),
                stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
            children.append(child); waves.append(child)
            report['wave_outputs'][case['case_id']] = str(out)
        atomic_json(args.output/'report.json',report)
        deadline = time.monotonic()+config['wall_limit_s']+180
        while any(child.poll() is None for child in waves):
            if service.poll() is not None: raise RuntimeError('shared worker exited; no retry')
            if any(child.poll() not in (None,0) for child in waves): raise RuntimeError('wave failed; partial evidence retained')
            if time.monotonic()>deadline: raise TimeoutError('reference waves wall limit')
            time.sleep(1)
        report['waves'] = {case: load_json(Path(path)/'report.json') for case,path in report['wave_outputs'].items()}
        report['status'] = 'completed_reference_waves'
    except BaseException as exc:
        report.update(status='error_stop_no_retry',error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        (broker/'stop-service').touch()
        for child in reversed(children): stop_child(child)
        for stream in streams: stream.close()
        report['wall_including_startup_s'] = time.monotonic()-started
        atomic_json(args.output/'report.json',report)
    print(json.dumps(report))


if __name__ == '__main__':
    main()
