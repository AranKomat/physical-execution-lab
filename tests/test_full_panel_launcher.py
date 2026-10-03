"""Launcher orchestration fixtures, not native task-performance evidence."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from k1lab.errors import ContractError
from k1lab.util import digest
from scripts.semantic import run_full_panel_baseline as launcher


def setup_panel(tmp_path, monkeypatch, approach):
    monkeypatch.setattr(launcher, 'ROOT', tmp_path)
    (tmp_path / 'runs').mkdir()
    prepared = tmp_path / 'prepared'
    prepared.mkdir()
    panel = dict(sha256='panel', cases=[dict(task_group=name, case_id=name)
        for group in launcher.GROUPS for name in group])
    modes = dict(original_only='motor_only', direct='direct_sparse', numeric='sparse',
                 semantic='semantic_subtask_hierarchy')
    config = dict(mode=modes[approach], wall_limit_s=1, model=dict(api_key_env='TEST_RELAY_TOKEN'))
    plan = dict(manifest_sha256='panel', sha256='plan', configs={approach: digest(config)})
    for name, value in [('cases', panel), ('plan', plan), (approach, config),
                        ('freeze', dict(sha256='freeze'))]:
        (prepared / (name + '.json')).write_text(json.dumps(value))
    for name in ('semantic_lab/task_rows.py', 'semantic_lab/native_execution.py',
                 'semantic_lab/native_io.py', 'semantic_lab/pi05_batch.py',
                 'scripts/semantic/serve_pi05_batch.py', 'scripts/semantic/run_distinct_task_group.py',
                 'scripts/semantic/run_full_panel_baseline.py'):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('# fixture\n')
    monkeypatch.setattr(launcher.subprocess, 'check_output', lambda *a, **k: '0\n0\n')
    monkeypatch.setattr(launcher.shutil, 'disk_usage', lambda *a: SimpleNamespace(free=10 * 1024**3))
    monkeypatch.setattr(launcher, 'stop_child', lambda child: None)
    monkeypatch.setenv('TEST_RELAY_TOKEN', 'fixture-not-a-real-token')
    argv = ['runner', '--prepared', str(prepared), '--output', str(tmp_path / 'runs/out'),
            '--approach', approach]
    if approach != 'original_only':
        argv += ['--allow-api', '--freeze', str(prepared / 'freeze.json'),
                 '--baseline-run', str(tmp_path / 'baseline'),
                 '--native-reference-freeze', str(prepared / 'freeze.json'),
                 '--controller-run', str(tmp_path / 'controller')]
    monkeypatch.setattr('sys.argv', argv)
    return prepared, argv


@pytest.mark.parametrize('approach', ['original_only', 'direct', 'numeric', 'semantic'])
@pytest.mark.parametrize('preload', [False, True])
def test_full_method_cohort_routing(tmp_path, monkeypatch, approach, preload):
    _, argv = setup_panel(tmp_path, monkeypatch, approach)
    monkeypatch.delenv('LD_PRELOAD', raising=False)
    library = tmp_path / 'libstdc++.so.6'
    if preload:
        library.write_bytes(b'fixture library; never loaded')
        argv.extend(['--simulator-libstdcxx', str(library)])
    verifications, commands, environments = [], [], []
    monkeypatch.setattr(launcher, 'verify_binding', lambda *a, **k: verifications.append(k))
    monkeypatch.setattr(launcher, 'check_transfer', lambda *a: dict(transfer_checks_passed=True))

    def launch(command, **kwargs):
        commands.append(command)
        environments.append(kwargs['env'])
        if 'run_distinct_task_group.py' in command[2]:
            output = Path(command[command.index('--output') + 1])
            cases = json.loads(Path(command[command.index('--cases') + 1]).read_text())
            (output / 'report.json').write_text(json.dumps(dict(
                status='native_control_wave', paid_calls=0,
                controller_results={str(i): dict(status='native_completed', success=False)
                                    for i in range(len(cases))})))
            (output / 'pre-action-admission.json').write_text(json.dumps(dict(
                passed=True, initial_fk_checks={str(i): dict(passed=True) for i in range(len(cases))})))
        return SimpleNamespace(poll=lambda: 0)

    monkeypatch.setattr(launcher.subprocess, 'Popen', launch)
    launcher.main()
    report = json.loads((tmp_path / 'runs/out/report.json').read_text())
    groups = [c for c in commands if 'run_distinct_task_group.py' in c[2]]
    assert len(groups) == 3
    assert sum(len(json.loads(Path(c[c.index('--cases') + 1]).read_text())) for c in groups) == 10
    assert report['policy_runtimes'] == (0 if approach == 'direct' else 1)
    assert len(commands) == (3 if approach == 'direct' else 4)
    assert report['method'] == approach
    assert all(('--allow-api' in c) == (approach != 'original_only') for c in groups)
    assert bool(verifications) == (approach != 'original_only')
    for command, env in zip(commands, environments):
        expected = str(library) if preload and 'run_distinct_task_group.py' in command[2] else None
        assert env.get('LD_PRELOAD') == expected
    if preload:
        from k1lab.util import file_sha
        assert report['simulator_libstdcxx'] == dict(path=str(library), sha256=file_sha(library))
    else:
        assert 'simulator_libstdcxx' not in report


def test_paid_launch_requires_relay_before_startup(tmp_path, monkeypatch):
    setup_panel(tmp_path, monkeypatch, 'direct')
    monkeypatch.delenv('TEST_RELAY_TOKEN')
    with pytest.raises(ContractError, match='relay token'):
        launcher.main()
    assert not (tmp_path / 'runs/out').exists()


def test_paid_launch_rejects_unfrozen_sources(tmp_path, monkeypatch):
    setup_panel(tmp_path, monkeypatch, 'numeric')

    def reject(*args, **kwargs):
        raise ContractError('source changed')

    monkeypatch.setattr(launcher, 'verify_binding', reject)
    with pytest.raises(ContractError, match='source changed'):
        launcher.main()
    assert not (tmp_path / 'runs/out').exists()


def test_provider_interruption_is_not_ten_physical_failures():
    summary = launcher.summarize_cohort_results([dict(controller_results={
        str(i): dict(status='infrastructure_or_contract_error', success=False) for i in range(10)})])
    assert summary['native_task_failures'] == summary['native_terminal_cases'] == 0
    assert summary['censored_or_invalid_cases'] == 10
    assert not summary['all_rows_native_terminal']
