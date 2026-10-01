#!/usr/bin/env python3
"""Launch ONE pinned RoboDojo server and ONE controller; print-only unless --execute.

Readiness comes from the server's JSON stdout. Do not open a readiness socket:
upstream accepts only one controller connection. Only our own child processes
are terminated. No cluster, credentials, shared workers, or drivers are changed.
"""
from __future__ import annotations
import argparse,json,os,signal,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from k1lab.util import load_json,atomic_json,file_sha
from k1lab.errors import ContractError
from k1lab.multibench.manifest import check
from k1lab.multibench.adapters.robodojo import check_checkout,REV,RoboDojoRPC
from k1lab.multibench.transport import encode_obs
from k1lab.multibench.types import Action


def source_ready(log):
    if not Path(log).exists():return False
    for line in Path(log).read_text(errors='replace').splitlines():
        try:
            obj=json.loads(line)
            if isinstance(obj,dict) and obj.get('event')=='ready':return True
        except (ValueError,TypeError):pass
    return False


def stop_child(child):
    if child is None or child.poll() is not None:return
    try:os.killpg(child.pid,signal.SIGTERM)
    except ProcessLookupError:return
    try:child.wait(timeout=15)
    except subprocess.TimeoutExpired:
        try:os.killpg(child.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        child.wait(timeout=10)


def plan(a):
    root=Path(__file__).resolve().parents[2]
    manifest=check(load_json(a.manifest));case=next((c for c in manifest['cases'] if c['case_id']==a.case_id),None)
    if case is None or case['benchmark']!='robodojo':raise ContractError('not a selected RoboDojo case')
    cfg=load_json(a.config)
    if cfg['benchmark']!='robodojo':raise ContractError('wrong benchmark configuration')
    if a.capture_only and case['partition']!='dev':raise ContractError('capture-only is development, not held-out exploration')
    out=Path(a.output).resolve()
    if out.exists():raise FileExistsError('fresh output root required')
    donor=Path(a.gpt_as_policy_root or cfg['environment']['gpt_as_policy_root']).resolve()
    sim=Path(a.robodojo_root).resolve()
    server=[str(Path(a.sim_python).resolve()),'-u','-m','hybrid_rollout.robodojo.robodojo_server.server',
       '--task',case.get('runtime_task',case['task']),'--eval-seed',str(case['eval_seed']),
       '--port',str(a.sim_port),'--output',str(out/'native')]
    if case.get('layout_sha256'):
        if not a.source_panel or file_sha(a.source_panel)!=manifest['source_panel_sha256']:
            raise ContractError('exact source-panel file used during import is required')
        server+=['--eval-manifest',str(Path(a.source_panel).resolve()),'--case-file',str(out/'source_case.json')]
    controller=[str(Path(a.controller_python).resolve()),str(root/'run_bench.py'),'run-case',
        '--config',str(Path(a.config).resolve()),'--manifest',str(Path(a.manifest).resolve()),
        '--case-id',a.case_id,'--output',str(out/'controller'),'--allow-native']
    if a.development:controller+=['--development']
    else:
        if not a.capture_only and (not a.freeze or not a.qualification):raise ContractError('scored run needs freeze and native qualification')
        if a.freeze:controller+=['--freeze',str(Path(a.freeze).resolve())]
        if a.qualification:controller+=['--qualification',str(Path(a.qualification).resolve())]
    if a.allow_policy:controller+=['--allow-policy']
    if a.allow_api:controller+=['--allow-api']
    return {'server_argv':server,'controller_argv':controller,'server_cwd':str(sim),'controller_cwd':str(root),
        'donor_root':str(donor),'output':str(out),'case':case,'capture_only':a.capture_only,
        'locator_overrides':{'K1LAB_SIM_PORT':str(a.sim_port),'K1LAB_NATIVE_OUTCOME_PATH':str(out/'native/evaluation_outcome.json')},
        'network':'no paid model requests until controller explicitly starts with --allow-api'}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('config','manifest','case-id','output','sim-python','robodojo-root'):p.add_argument('--'+name,required=True)
    p.add_argument('--controller-python',default=sys.executable);p.add_argument('--gpt-as-policy-root')
    p.add_argument('--source-panel');p.add_argument('--sim-port',type=int,default=19113)
    p.add_argument('--startup-timeout',type=float,default=600)
    for name in ('development','allow-policy','allow-api','execute','capture-only','probe-one-step'):p.add_argument('--'+name,action='store_true')
    p.add_argument('--freeze');p.add_argument('--qualification');a=p.parse_args(argv)
    v=plan(a);print(json.dumps(v,indent=2),flush=True)
    if not a.execute:return
    donor=check_checkout(v['donor_root'],REV)
    if not Path(a.sim_python).is_file():raise ContractError('sim interpreter missing')
    out=Path(v['output']);out.mkdir(parents=True)
    atomic_json(out/'launch.json',v,exclusive=True)
    if v['case'].get('layout_sha256'):
        sys.path.insert(0,str(donor))
        from hybrid_rollout.robodojo.evaluation import read_panel,case_identity
        panel=read_panel(a.source_panel)
        source=next(c for c in panel['cases'] if c['case_id']==a.case_id)
        atomic_json(out/'source_case.json',{'case':source,'identity':case_identity(panel,source)},exclusive=True)
    env=dict(os.environ)
    # RoboDojo's donor server imports the pinned XPolicyLab RPC package
    # (`client_server`) even for capture-only episodes. Keep that checkout
    # explicit and discoverable when the standard bootstrap layout is used.
    source_paths=[str(donor),str(Path(a.robodojo_root).resolve())]
    xpolicy=Path(__file__).resolve().parents[2]/'external'/'XPolicyLab'
    if xpolicy.is_dir():source_paths.append(str(xpolicy))
    source_paths.append(env.get('PYTHONPATH',''))
    env['PYTHONPATH']=os.pathsep.join(source_paths)
    env.update(v['locator_overrides']);server=controller=None
    try:
        with (out/'server.log').open('w') as log:
            server=subprocess.Popen(v['server_argv'],cwd=v['server_cwd'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            end=time.monotonic()+a.startup_timeout
            while not source_ready(out/'server.log'):
                if server.poll() is not None:raise RuntimeError('sim server exited; inspect server.log')
                if time.monotonic()>end:raise TimeoutError('sim server not ready; no controller/API launched')
                time.sleep(.5)
            if a.capture_only:
                cfg=load_json(a.config)['environment']|{'gpt_as_policy_root':str(donor),'sim_port':a.sim_port,
                    'native_outcome_path':str(out/'native/evaluation_outcome.json')}
                native=RoboDojoRPC(cfg)
                try:
                    obs=native.reset(v['case']);atomic_json(out/'observation.wire.json',encode_obs(obs),exclusive=True)
                    if a.probe_one_step:
                        native.step(Action('x5_joint14',obs.state.copy()))
                        native.finish('one_step_native_probe')
                    else:
                        native.finish('capture_only_no_actions')
                finally:native.close()
            else:
                with (out/'controller.log').open('w') as control_log:
                    controller=subprocess.Popen(v['controller_argv'],cwd=v['controller_cwd'],env=env,
                        stdout=control_log,stderr=subprocess.STDOUT,start_new_session=True)
                    code=controller.wait()
                    if code:raise RuntimeError(f'controller exited {code}; results/logs retained, no retry')
            try:server.wait(timeout=30)
            except subprocess.TimeoutExpired:stop_child(server)
    finally:
        stop_child(controller);stop_child(server)

if __name__=='__main__':main()
