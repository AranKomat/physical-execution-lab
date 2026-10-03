#!/usr/bin/env python3
"""Own one full ten-distinct-task condition, with fused inference when applicable."""
import argparse
from collections import Counter
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
from semantic_lab.protocol import verify_binding
from semantic_lab.cohort_admission import check_transfer

# Native global physics and support-robot configuration determine groups, not
# task outcomes. All ten cases still share one condition and one inference batch.
GROUPS = (
    ('arrange_largest_number', 'build_tower', 'classify_objects_by_language', 'fold_clothes'),
    ('imitate_sorting_sequence', 'make_kong'),
    ('classify_objects', 'organize_table', 'pack_objects_into_box', 'put_bottles_into_dustbin'),
)


def summarize_cohort_results(groups):
    rows = [row for group in groups for row in group['controller_results'].values()]
    counts = Counter(row['status'] for row in rows)
    terminal = sum(row['status'] == 'native_completed' for row in rows)
    return dict(controller_status_counts=dict(counts), results_present=len(rows),
        native_terminal_cases=terminal, all_rows_native_terminal=terminal == 10 and len(rows) == 10,
        successes=sum(row['success'] and row['status'] == 'native_completed' for row in rows),
        native_task_failures=sum(not row['success'] and row['status'] == 'native_completed' for row in rows),
        censored_or_invalid_cases=len(rows)-terminal,
        paid_calls_count_scope='client HTTP attempts, including local relay rejections; not provider reservations or charges')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--prepared', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--approach', choices=('original_only', 'direct', 'numeric', 'semantic'),
                   default='original_only')
    p.add_argument('--freeze', type=Path)
    p.add_argument('--allow-api', action='store_true')
    p.add_argument('--baseline-run', type=Path)
    p.add_argument('--native-reference-freeze', type=Path)
    p.add_argument('--controller-run', type=Path)
    p.add_argument('--allow-standard-fallback', action='store_true')
    p.add_argument('--simulator-libstdcxx', type=Path,
                   help='Explicit host C++ runtime preload for native simulator processes only')
    args = p.parse_args()
    simulator_env = dict(os.environ)
    if args.simulator_libstdcxx is not None:
        library = args.simulator_libstdcxx.resolve(strict=True)
        if not library.is_file():
            raise ContractError('simulator C++ runtime must be a file')
        simulator_env['LD_PRELOAD'] = str(library)
    panel = load_json(args.prepared / 'cases.json')
    plan = load_json(args.prepared / 'plan.json')
    config_path = (args.prepared / (args.approach + '.json')).resolve()
    treatment = load_json(config_path)
    mode = {'original_only': 'motor_only', 'direct': 'direct_sparse',
            'numeric': 'sparse', 'semantic': 'semantic_subtask_hierarchy'}[args.approach]
    if (len(panel['cases']) != 10 or panel['sha256'] != plan['manifest_sha256']
            or treatment['mode'] != mode or digest(treatment) != plan['configs'][args.approach]):
        raise ContractError('full cohort does not match the fixed comparison preparation')
    if args.allow_api != (args.approach != 'original_only'):
        raise ContractError('paid conditions require explicit API enablement; original-only forbids it')
    if args.allow_api and not os.environ.get(treatment['model']['api_key_env']):
        raise ContractError('budget relay token must be configured before simulator startup')
    if args.allow_standard_fallback != (treatment.get('model', {}).get('tier_fallback') ==
                                       'same_model_default_after_explicit_flex_capacity'):
        raise ContractError('tier fallback must match the explicitly prepared condition')
    if args.approach != 'original_only' and args.freeze is None:
        raise ContractError('paid full-panel conditions require a fresh execution-source freeze')
    frozen = load_json(args.freeze) if args.freeze else None
    if frozen:
        verify_binding(ROOT, frozen, panel, treatment, require_execution_sources=True)
    admission = None
    if args.allow_api:
        if args.baseline_run is None or args.native_reference_freeze is None or args.controller_run is None:
            raise ContractError('paid matched panel requires retained baseline/native reference admission')
        admission = check_transfer(ROOT, args.baseline_run,
                                   load_json(args.native_reference_freeze), panel, args.controller_run)
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
    if admission:
        atomic_json(out / 'native-transfer.json', admission)
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
    direct = args.approach == 'direct'
    report = dict(status='starting', method=args.approach, paid_calls=0, policy_runtimes=0 if direct else 1,
                  simulator_processes=3, distinct_tasks=10, source_hashes=source_hashes,
                  simulator_gpu_affinity=[0, 1, 0], policy_gpu=None if direct else 1, jax_memory_fraction=.5,
                  source_freeze_sha256=frozen['sha256'] if frozen else None,
                  tier_policy=plan.get('tier_policy', 'flex_only'),
                  comparison_plan_sha256=plan['sha256'], cases=[case['case_id'] for case in panel['cases']],
                  native_equivalence_admission_pending=True, automatic_retry=False)
    if args.simulator_libstdcxx is not None:
        from k1lab.util import file_sha
        report['simulator_libstdcxx'] = dict(path=str(library), sha256=file_sha(library))
    children, streams = [], []
    started = time.monotonic()
    try:
        # Start model loading and scene construction concurrently.
        service = None
        if not direct:
            stream = (out / 'worker.log').open('x'); streams.append(stream)
            service = subprocess.Popen([str(ROOT / '.venv-pi05/bin/python'), '-u',
                str(ROOT / 'scripts/semantic/serve_pi05_batch.py'), '--cohort', str(out / 'cohort.json'),
                '--output', str(out / 'worker'), '--capacity', '10'], cwd=ROOT,
                env=dict(os.environ, CUDA_VISIBLE_DEVICES='1', XLA_PYTHON_CLIENT_PREALLOCATE='false',
                         XLA_PYTHON_CLIENT_MEM_FRACTION='.5',
                         OMP_NUM_THREADS='4', MKL_NUM_THREADS='4'), stdout=stream, stderr=subprocess.STDOUT,
                start_new_session=True)
            children.append(service)
        simulators = []
        for idx, wave in enumerate(waves):
            gpu = 1 if idx == 1 else 0
            stream = (out / f'group{idx}.log').open('x'); streams.append(stream)
            command = ['/root/miniconda3/envs/RoboDojo/bin/python3.11', '-u',
                str(ROOT / 'scripts/semantic/run_distinct_task_group.py'),
                '--cases', str(out / f'group{idx}-cases.json'), '--config', str(config_path),
                '--output', str(wave),
                '--kit_args', f'--/renderer/activeGpu={gpu} --/renderer/multiGpu/enabled=false']
            if args.allow_api:
                command.append('--allow-api')
                command.extend(['--baseline-group', str((args.baseline_run / f'group{idx}').resolve())])
            if args.freeze:
                command.extend(['--freeze', str(args.freeze.resolve()),
                                '--panel', str((args.prepared / 'cases.json').resolve())])
            child = subprocess.Popen(command, cwd=ROOT,
                env=dict(simulator_env, CUDA_VISIBLE_DEVICES=str(gpu), OMNI_KIT_ACCEPT_EULA='YES',
                         OMP_NUM_THREADS='4', MKL_NUM_THREADS='4'),
                stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
            children.append(child); simulators.append(child)
        atomic_json(out / 'report.json', report)
        deadline = time.monotonic() + treatment['wall_limit_s'] + 900
        log_offsets = [0] * len(waves)
        log_tails = [''] * len(waves)
        admitted = not args.allow_api

        def admit_ready_groups():
            nonlocal admitted
            if admitted or not all((wave / 'pre-action-admission.json').exists() for wave in waves):
                return
            bindings = [load_json(wave / 'pre-action-admission.json') for wave in waves]
            if any(not binding.get('passed') for binding in bindings):
                raise ContractError('a native reset admission failed')
            if args.approach in ('direct', 'numeric') and any(
                    len(binding.get('initial_fk_checks', {})) != len(GROUPS[idx])
                    or any(not check.get('passed') for check in binding['initial_fk_checks'].values())
                    for idx, binding in enumerate(bindings)):
                raise ContractError('native robot-only FK admission incomplete')
            for wave in waves:
                atomic_json(wave / 'cohort-admitted.json', dict(
                    scope='matched screened simulator runtime, not full benchmark or real hardware',
                    source_freeze_sha256=frozen['sha256'], all_ten_reset_bindings_passed=True))
            admitted = True

        while any(child.poll() is None for child in simulators):
            if service is not None and service.poll() not in (None, 0):
                raise RuntimeError('fused model worker failed; no retry')
            if any(child.poll() not in (None, 0) for child in simulators):
                raise RuntimeError('distinct-task group failed; retain partial cohort evidence')
            for wave in waves:
                path = wave / 'report.json'
                if path.exists() and load_json(path)['status'] == 'error_stop_no_retry':
                    raise RuntimeError('native group reported failure, regardless of process exit code')
            for idx in range(len(waves)):
                with (out / f'group{idx}.log').open(errors='replace') as stream:
                    stream.seek(log_offsets[idx])
                    recent = log_tails[idx] + stream.read()
                    log_offsets[idx] = stream.tell()
                log_tails[idx] = recent[-512:]
                if any(marker in recent for marker in ('Scene state is corrupted',
                    'Simulation cannot continue', 'aborting simulation')):
                    raise RuntimeError(f'native PhysX fatal error in group{idx}; cohort censored')
            if time.monotonic() > deadline:
                raise TimeoutError('full cohort wall limit')
            if shutil.disk_usage(ROOT).free < 1024**3:
                raise ContractError('retention disk reserve reached; do not delete unique evidence')
            for path, expected in source_hashes.items():
                if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected:
                    raise ContractError('executor source changed during cohort execution')
            if frozen:
                verify_binding(ROOT, frozen, panel, treatment, require_execution_sources=True)
            admit_ready_groups()
            time.sleep(1)
        admit_ready_groups()
        if not admitted:
            raise ContractError('cohort terminated before all-ten native admission; no completed comparison')
        results = [load_json(wave / 'report.json') for wave in waves]
        if any(row['status'] in ('starting', 'native_ready', 'error_stop_no_retry') for row in results):
            raise RuntimeError('simulator exit is not proof of completed episodes')
        summary = summarize_cohort_results(results)
        report.update(status=('completed_full_original_only_cohort' if args.approach == 'original_only'
                              else 'completed_full_approach_cohort' if summary['all_rows_native_terminal']
                              else 'incomplete_full_approach_cohort'), groups=results,
                      paid_calls=sum(row['paid_calls'] for row in results))
        report.update(summary)
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
