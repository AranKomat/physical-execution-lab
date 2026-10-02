from __future__ import annotations
import argparse
from copy import deepcopy
import json
from pathlib import Path
import time
from k1lab.errors import ContractError
from k1lab.util import atomic_json, digest, load_json
from k1lab.multibench import manifest as mf
from .contracts import MODES, ScheduleConfig
from . import protocol

ROOT = Path(__file__).resolve().parents[1]


def configurations(source, max_calls=32):
    """Derive from a known working bound config, retaining model/provider identities."""
    if source['benchmark'] not in ('robodojo', 'robocasa365') or not source.get('policy'):
        raise ContractError('a working motor-only RoboDojo/RoboCasa config is required')
    # New conditions do not inherit the old horizon-reducing governor/correction contract.
    base = deepcopy(source)
    for key in ('monitor', 'max_decision_steps', 'max_correction_steps', 'max_reviews',
                'translation_limit_m', 'robot_preview'):
        base.pop(key, None)
    base['no_task_memory'] = base['no_task_demonstrations'] = True
    base['max_semantic_calls'] = max_calls
    base['semantic_schedule'] = dict(review_interval_steps=100, minimum_dwell_steps=30,
                                    event_cooldown_steps=30, allow_semantic_recovery=False)
    base['async_planner'] = False
    base['semantic_protocol'] = 'semantic-policy.v1'
    base['classification'] = 'benchmark_trained_policy_plus_language_hierarchy'
    model = base.setdefault('model', {})
    # Preserve authorized route and user-selected model. No capability claim from its name.
    defaults = {'model': 'gpt-6.1-sol', 'transport': 'responses', 'base_url': 'https://api.openai.com/v1',
                'api_key_env': 'OPENAI_API_KEY', 'service_tier': 'flex', 'reasoning_effort': 'medium',
                'history_rounds': 4, 'image_max_edge': 480, 'max_output_tokens': 2048, 'timeout_s': 900}
    for k, v in defaults.items():
        model.setdefault(k, v)
    model['max_requests'] = max_calls
    model['max_total_output_tokens'] = max_calls * model['max_output_tokens']
    variants = [('motor_only', 'original_only', 'motor'),
                ('semantic_shadow', 'original_only', 'shadow'),
                ('semantic_subtask_hierarchy', 'task_plus_subtask', 'task_plus_subtask'),
                ('semantic_subtask_hierarchy', 'subtask_only', 'subtask_only')]
    results = []
    for mode, prompt, label in variants:
        cfg = deepcopy(base)
        cfg['mode'], cfg['prompt_mode'] = mode, prompt
        cfg['name'] = f'{source["benchmark"]}_{source["policy"]["identity"]["name"]}_semantic_v5_{label}'
        results.append(cfg)
    return results


def policy(config, allow_policy):
    if config['backend'] == 'remote':
        from .transport import SemanticRemotePolicy
        return SemanticRemotePolicy(config, allow_policy=allow_policy)
    from k1lab.multibench.factory import policy as construct
    from .policy import InstructionPolicy
    return InstructionPolicy(construct(config, allow_policy), kind=config['backend'])


def main(argv=None):
    p = argparse.ArgumentParser(description='Semantic hierarchy: language changes, native motor cadence does not')
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('doctor')
    q = sub.add_parser('synthetic'); q.add_argument('--output', required=True)
    q = sub.add_parser('prepare'); q.add_argument('--from-config', required=True); q.add_argument('--output', required=True); q.add_argument('--max-calls', type=int, default=32)
    q = sub.add_parser('serve-policy'); q.add_argument('--config', required=True); q.add_argument('--port', type=int, default=19600); q.add_argument('--allow-policy', action='store_true')
    q = sub.add_parser('freeze'); q.add_argument('--manifest', required=True); q.add_argument('--configs', nargs='+', required=True); q.add_argument('--output', required=True)
    q = sub.add_parser('qualification-template'); q.add_argument('--config', required=True); q.add_argument('--output', required=True)
    q = sub.add_parser('run-case')
    for name in ('config', 'manifest', 'case-id', 'output'):
        q.add_argument('--' + name, required=True)
    for name in ('development', 'allow-native', 'allow-policy', 'allow-api'):
        q.add_argument('--' + name, action='store_true')
    q.add_argument('--freeze'); q.add_argument('--qualification')
    q = sub.add_parser('report')
    for name in ('manifest', 'runs', 'output'):
        q.add_argument('--' + name, required=True)
    q.add_argument('--conditions', nargs='+', required=True)
    q.add_argument('--partition', choices=['dev', 'test', 'all'], default='test')
    q.add_argument('--baseline'); q.add_argument('--candidate')
    q = sub.add_parser('audit'); q.add_argument('--episode', required=True)
    a = p.parse_args(argv)
    if a.cmd == 'doctor':
        print(json.dumps({'version': '0.5.0', 'native_results_from_this_build': 0,
                          'architecture': 'semantic goals -> unchanged natural VLA execution prefixes',
                          'native_base': protocol.compatibility(ROOT),
                          'async_native_runner': False, 'new_training': False,
                          'model_or_tier_fallback': False}, indent=2)); return
    if a.cmd == 'synthetic':
        from .synthetic import run
        print(json.dumps(run(a.output), indent=2)); return
    if a.cmd == 'prepare':
        if not 1 <= a.max_calls <= 10000:
            raise ContractError('invalid semantic request budget')
        c = mf.resolved_config(load_json(a.from_config))
        out = Path(a.output); out.mkdir(parents=True, exist_ok=False)
        for cfg in configurations(c, a.max_calls):
            atomic_json(out / (cfg['name'] + '.json'), cfg, exclusive=True)
        print(out); return
    if a.cmd == 'freeze':
        m = mf.check(load_json(a.manifest))
        cs = [mf.resolved_config(load_json(path)) for path in a.configs]
        atomic_json(a.output, protocol.freeze(ROOT, m, cs), exclusive=True); return
    if a.cmd == 'qualification-template':
        c = mf.resolved_config(load_json(a.config))
        atomic_json(a.output, {'schema': 'semantic.qualification.v1',
            'config_sha256': digest(c), 'source_sha256': protocol.code_fingerprint(ROOT),
            'checks': {k: False for k in ('native_motor_only_parity', 'effective_prompt_seen_at_model_boundary',
                'continue_preserves_cadence', 'context_switch_preserves_ack_history',
                'native_terminal_scoring_separate', 'source_bound_model_identity', 'tokenizer_subtask_not_truncated')}, 'evidence': []}, exclusive=True); return
    if a.cmd == 'serve-policy':
        protocol.require_live_base(ROOT)
        c = mf.resolved_config({'policy': load_json(a.config)})['policy']
        if c['backend'] == 'remote':
            raise ContractError('serve-policy requires an in-process provider config')
        from .transport import serve
        t = time.perf_counter(); pol = policy(c, a.allow_policy)
        serve(pol, a.port, time.perf_counter() - t); return
    if a.cmd == 'run-case':
        protocol.require_live_base(ROOT)
        c = mf.resolved_config(load_json(a.config)); m = mf.check(load_json(a.manifest))
        case = next((v for v in m['cases'] if v['case_id'] == a.case_id), None)
        if not case or c['benchmark'] != case['benchmark'] or c['mode'] not in MODES:
            raise ContractError('case/config mismatch')
        if a.development:
            if case['partition'] != 'dev':
                raise ContractError('development cannot use held-out cases')
        else:
            if not a.freeze or not a.qualification:
                raise ContractError('scored semantic runs need new freeze and qualification')
            protocol.verify(ROOT, load_json(a.freeze), m, c, load_json(a.qualification))
        if not a.allow_native or not a.allow_policy:
            raise ContractError('explicit --allow-native and --allow-policy required')
        if c['mode'] != 'motor_only' and c['model']['transport'] in ('responses', 'chat') and not a.allow_api:
            raise ContractError('paid route requires --allow-api')
        if c['mode'] != 'motor_only' and c['model'].get('service_tier') != 'flex':
            raise ContractError('this project branch is Flex-only; tier changes require a separate reviewed experiment')
        out = Path(a.output)
        if out.exists(): raise FileExistsError(out)
        env = pol = planner = None
        try:
            from .planner import SemanticPlanner
            from k1lab.multibench.factory import environment
            from .runner import run_episode
            if c['mode'] != 'motor_only':
                planner = SemanticPlanner(c['model'], out / 'model', allow_api=a.allow_api)
            pol = policy(c['policy'], a.allow_policy)
            env = environment(c['environment'], a.allow_native)
            result = run_episode(env, pol, planner, case, c, out)
        except Exception:
            for obj in (env, pol, planner):
                if obj:
                    try: obj.close()
                    except Exception: pass
            raise
        print(json.dumps(result, indent=2))
        if result['status'] != 'native_completed': raise SystemExit(2)
        return
    if a.cmd == 'report':
        from .report import write_report
        m = mf.check(load_json(a.manifest))
        cases = [c for c in m['cases'] if a.partition == 'all' or c['partition'] == a.partition]
        ids = {c['case_id'] for c in cases}
        rr = [load_json(f) for f in Path(a.runs).rglob('result.json')]
        rr = [r for r in rr if r.get('schema') == 'semantic.result.v1' and r['case_id'] in ids]
        print(json.dumps(write_report(cases, rr, a.output, a.conditions, a.baseline, a.candidate), indent=2)); return
    if a.cmd == 'audit':
        from .audit import audit
        print(json.dumps(audit(a.episode), indent=2)); return

if __name__ == '__main__':
    main()
