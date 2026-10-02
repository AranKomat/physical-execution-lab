#!/usr/bin/env python3
"""Own a full ten-distinct-task original-policy cohort with one fused worker."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from k1lab.errors import ContractError
from k1lab.util import atomic_json, digest, load_json
from scripts.multibench.launch_robodojo_case import stop_child

# Native global physics and support-robot configuration determine groups, not
# task outcomes. All ten cases still share one condition and one inference batch.
GROUPS = (
    ('arrange_largest_number', 'build_tower', 'classify_objects_by_language', 'fold_clothes'),
    ('imitate_sorting_sequence', 'make_kong'),
    ('classify_objects', 'organize_table', 'pack_objects_into_box', 'put_bottles_into_dustbin'),
)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--prepared', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    panel = load_json(args.prepared / 'cases.json')
    plan = load_json(args.prepared / 'plan.json')
    config_path = (args.prepared / 'original_only.json').resolve()
    treatment = load_json(config_path)
    if (len(panel['cases']) != 10 or panel['sha256'] != plan['manifest_sha256']
            or treatment['mode'] != 'motor_only' or digest(treatment) != plan['configs']['original_only']):
        raise ContractError('full cohort does not match the fixed original-only comparison preparation')
    cases = {case['task_group']: case for case in panel['cases']}
    if set(cases) != {name for group in GROUPS for name in group}:
        raise ContractError('full cohort must include the fixed ten distinct tasks without replacement')
    usage = subprocess.check_output(['nvidia-smi', '--query-gpu=memory.used',
                                     '--format=csv,noheader,nounits'], text=True)
    if len(usage.splitlines()) != 2 or any(int(value) >= 500 for value in usage.splitlines()):
        raise ContractError('preserve active GPU work; this full cohort requires two idle GPUs')
    if shutil.disk_usage(ROOT).free < 3 * 1024**3:
        raise ContractError('full cohort requires at least 3GiB free for retained inputs/actions')
    out = args.output.resolve()
    if not out.is_relative_to(ROOT / 'runs'):
        raise ContractError('cohort output must be inside runs')
    out.mkdir(exist_ok=False)
    waves = []
    for idx, names in enumerate(GROUPS):
        wave = out / f'group{idx}'
        wave.mkdir()
        atomic_json(out / f'group{idx}-cases.json', [cases[name] for name in names])
        waves.append(wave)
    atomic_json(out / 'cohort.json', [str(wave) for wave in waves])
    source_paths = ['semantic_lab/task_rows.py', 'semantic_lab/native_execution.py',
                    'semantic_lab/native_io.py', 'semantic_lab/pi05_batch.py',
                    'scripts/semantic/serve_pi05_batch.py',
                    'scripts/semantic/run_distinct_task_group.py',
                    'scripts/semantic/run_full_panel_baseline.py']
    import hashlib
    source_hashes = {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in source_paths}
    report = dict(status='starting', method='original_only', paid_calls=0, policy_runtimes=1,
                  simulator_processes=3, distinct_tasks=10, source_hashes=source_hashes,
                  comparison_plan_sha256=plan['sha256'], cases=[case['case_id'] for case in panel['cases']],
                  native_equivalence_admission_pending=True, automatic_retry=False)
    children, streams = [], []
    started = time.monotonic()
    try:
        # Start model loading and scene construction concurrently.
        stream = (out / 'worker.log').open('x'); streams.append(stream)
        service = subprocess.Popen([str(ROOT / '.venv-pi05/bin/python'), '-u',
            str(ROOT / 'scripts/semantic/serve_pi05_batch.py'), '--cohort', str(out / 'cohort.json'),
            '--output', str(out / 'worker'), '--capacity', '10'], cwd=ROOT,
            env=dict(os.environ, CUDA_VISIBLE_DEVICES='1', XLA_PYTHON_CLIENT_PREALLOCATE='false',
                     OMP_NUM_THREADS='4', MKL_NUM_THREADS='4'), stdout=stream, stderr=subprocess.STDOUT,
            start_new_session=True)
        children.append(service)
        simulators = []
        for idx, wave in enumerate(waves):
            stream = (out / f'group{idx}.log').open('x'); streams.append(stream)
            child = subprocess.Popen(['/root/miniconda3/envs/RoboDojo/bin/python3.11', '-u',
                str(ROOT / 'scripts/semantic/run_distinct_task_group.py'),
                '--cases', str(out / f'group{idx}-cases.json'), '--config', str(config_path),
                '--output', str(wave)], cwd=ROOT,
                env=dict(os.environ, CUDA_VISIBLE_DEVICES='0', OMNI_KIT_ACCEPT_EULA='YES',
                         OMP_NUM_THREADS='4', MKL_NUM_THREADS='4'),
                stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
            children.append(child); simulators.append(child)
        atomic_json(out / 'report.json', report)
        deadline = time.monotonic() + treatment['wall_limit_s'] + 900
        while any(child.poll() is None for child in simulators):
            if service.poll() not in (None, 0):
                raise RuntimeError('fused model worker failed; no retry')
            if any(child.poll() not in (None, 0) for child in simulators):
                raise RuntimeError('distinct-task group failed; retain partial cohort evidence')
            for wave in waves:
                path = wave / 'report.json'
                if path.exists() and load_json(path)['status'] == 'error_stop_no_retry':
                    raise RuntimeError('native group reported failure, regardless of process exit code')
            if time.monotonic() > deadline:
                raise TimeoutError('full cohort wall limit')
            if shutil.disk_usage(ROOT).free < 1024**3:
                raise ContractError('retention disk reserve reached; do not delete unique evidence')
            for path, expected in source_hashes.items():
                if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected:
                    raise ContractError('executor source changed during cohort execution')
            time.sleep(1)
        results = [load_json(wave / 'report.json') for wave in waves]
        if any(row['status'] in ('starting', 'native_ready', 'error_stop_no_retry') for row in results):
            raise RuntimeError('simulator exit is not proof of completed episodes')
        report.update(status='completed_full_original_only_cohort', groups=results)
    except BaseException as exc:
        report.update(status='error_stop_no_retry', error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        for wave in waves:
            (wave / 'stop-worker').touch()
        for child in reversed(children):
            stop_child(child)
        for stream in streams:
            stream.close()
        report['wall_including_startup_s'] = time.monotonic() - started
        atomic_json(out / 'report.json', report)
    print(json.dumps(report))


if __name__ == '__main__':
    main()
