"""Synchronous semantic boundaries, uninterrupted native motor prefixes.

This runner deliberately has no motor-action correction or 'shorten' decision.
The simulator pauses during planner calls; that is disclosed in every result.
"""
from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
import time
import numpy as np
from PIL import Image
from k1lab.errors import ContractError
from k1lab.journal import Journal
from k1lab.util import atomic_json, digest
from k1lab.multibench.runner import usage_summary
from .contracts import MODES, ScheduleConfig
from .state import SemanticState


def run_episode(env, policy, planner, case, config, output, *, clock=time.monotonic):
    mode = config['mode']
    if mode not in MODES or policy is None:
        raise ContractError('semantic experiments require a motor policy and a recognized mode')
    if (planner is None) != (mode == 'motor_only'):
        raise ContractError('only motor_only omits the semantic planner')
    if config.get('async_planner', False):
        raise ContractError('v5 native runner is synchronous; mailbox is an isolated future seam')
    root = Path(output)
    root.mkdir(parents=True, exist_ok=True)
    if any((root / p).exists() for p in ('events.jsonl', 'run.json', 'result.json')):
        raise FileExistsError('episode output already exists')
    journal = Journal(root / 'events.jsonl')
    timing = dict(setup_s=0., policy_s=0., ack_s=0., review_s=0., env_s=0., evidence_io_s=0.)
    metrics = dict(policy_calls=0, policy_requests=0, semantic_calls=0, semantic_changes=0, motor_prompt_changes=0,
                   semantic_recoveries=0, shadow_planner_failures=0, controller_faults=0, native_steps=0,
                   predicted_policy_actions=0, natural_suffix_discards=0, abort_prefix_discards=0,
                   unresolved_policy_actions=0, natural_prefixes=0, completed_prefixes=0,
                   gpt_induced_motor_resamples=0, gpt_induced_policy_resets=0,
                   gpt_induced_prefix_shortening=0, corrections=0)
    before = clock()
    max_reviews = config.get('max_semantic_calls', 32)
    wall_limit = config.get('wall_limit_s', 3600.)
    if type(max_reviews) is not int or max_reviews < 0 or not np.isfinite(wall_limit) or wall_limit <= 0:
        raise ContractError('invalid experiment budgets')
    schedule = ScheduleConfig(**config.get('semantic_schedule', {}))
    prompt_mode = config.get('prompt_mode', 'original_only')
    if mode in ('motor_only', 'semantic_shadow') and prompt_mode != 'original_only':
        raise ContractError('motor/shadow controls must preserve the original motor prompt')
    obs = None
    initial_stamp = None
    state = None
    prefix = None
    receipt = None
    result_status = 'incomplete'
    termination = 'unstarted'
    native_success = False
    native_terminal_observed = False
    native_success_observed = False
    native_score = None
    error = None
    receipts = []
    exposures = []
    captured = set()
    shadow_planner_disabled = False

    def log(name, data):
        journal.append(name, data)

    def capture(observation):
        if observation.step in captured:
            return
        t = clock()
        path = root / 'observations' / f'{observation.step:06d}'
        path.mkdir(parents=True, exist_ok=False)
        atomic_json(path / 'state.json', observation.actor_state())
        np.savez_compressed(path / 'sensors.npz', state=observation.state, **observation.rgb)
        for key, arr in observation.rgb.items():
            if not key.replace('_', '').replace('.', '').isalnum():
                raise ContractError('unsafe camera filename')
            Image.fromarray(arr).save(path / f'{key}.jpg', quality=90)
        captured.add(observation.step)
        timing['evidence_io_s'] += clock() - t

    try:
        t = clock()
        obs = env.reset(case)
        state = SemanticState(obs.instruction, prompt_mode, schedule)
        state.observe(obs)
        initial_stamp = obs.stamp
        policy.reset()
        policy.set_context(state.context)
        policy.observe(obs)
        timing['setup_s'] += clock() - t
        if planner is not None:
            planner.reset()
        capture(obs)
        run_info = {'schema': 'semantic.run.v1', 'case': case, 'config': config,
                    'policy': asdict(policy.identity), 'environment': env.describe(),
                    'initial_observation_sha256': initial_stamp,
                    'original_task': obs.instruction,
                    'simulation_advances_during_model_wait': False,
                    'new_training': False, 'cross_episode_solution_memory': False}
        atomic_json(root / 'run.json', run_info)
        log('episode_begin', run_info)
        while obs.step < env.horizon:
            if clock() - before > wall_limit:
                result_status, termination = 'resource_limited', 'wall_limit_at_boundary'
                break
            if obs.signals.get('controller_fault') is True:
                metrics['controller_faults'] += 1
                result_status, termination = 'controller_fault', 'native_controller_fault'
                break
            reasons = state.due(obs) if planner is not None and not shadow_planner_disabled else []
            if reasons:
                if metrics['semantic_calls'] >= max_reviews:
                    result_status, termination = 'resource_limited', 'semantic_call_budget'
                    break
                capture(obs)
                t = clock()
                metrics['semantic_calls'] += 1  # Attempts count even if response fails.
                old = state.context
                shadow = mode == 'semantic_shadow'
                effect = {}
                try:
                    decision = planner.decide(obs, state, reasons, receipt)
                    # Shadow progress remains private to the planner, not the motor.
                    effect = state.apply(decision, obs, shadow=False)
                except Exception as exc:
                    if not shadow:
                        raise
                    shadow_planner_disabled = True
                    metrics['shadow_planner_failures'] += 1
                    log('shadow_planner_error', {'step': obs.step,
                        'type': type(exc).__name__, 'detail': str(exc)[:1000],
                        'automatic_retry': False, 'further_planner_calls_disabled': True,
                        'motor_prompt_and_cadence_unchanged': True})
                finally:
                    timing['review_s'] += clock() - t
                effect['shadow_only'] = shadow
                if not shadow_planner_disabled:
                    log('semantic_decision', {'step': obs.step, 'reasons': reasons,
                        'decision': decision.wire(), 'effect': effect,
                        'native_evaluator_information_supplied': False})
                if effect.get('changed'):
                    metrics['semantic_changes'] += 1
                    if decision.operation == 'recover':
                        metrics['semantic_recoveries'] += 1
                    if not shadow:
                        reply = policy.set_context(state.context)
                        if reply.get('physical_steps') != 0 or reply.get('policy_resampled') or reply.get('history_reset'):
                            raise ContractError('semantic update changed motor execution state')
                        metrics['motor_prompt_changes'] += int(old.effective_prompt != state.context.effective_prompt)
                if effect.get('stop') and not shadow:
                    result_status, termination = 'planner_stop_incomplete', 'semantic_abstention_not_native_success'
                    break
            if clock() - before > wall_limit:
                result_status, termination = 'resource_limited', 'wall_limit_after_semantic_call'
                break
            t = clock()
            metrics['policy_requests'] += 1
            try:
                prefix = policy.propose(obs)
            finally:
                timing['policy_s'] += clock() - t
            prefix.validate(obs, policy.identity)
            n = policy.identity.execute_steps
            if len(prefix.actions) < n:
                raise ContractError('source prefix shorter than native execution horizon')
            metrics['policy_calls'] += 1
            metrics['natural_prefixes'] += 1
            metrics['predicted_policy_actions'] += len(prefix.actions)
            contract = prefix.diagnostics.get('semantic', {})
            expected_prompt = obs.instruction if mode in ('motor_only', 'semantic_shadow') else state.context.effective_prompt
            if contract.get('effective_prompt') != expected_prompt:
                raise ContractError('policy did not attest exact effective prompt')
            if contract.get('original_observation_sha256') != obs.stamp:
                raise ContractError('policy prompt bound to different physical evidence')
            exposures.append({'step': obs.step, **contract})
            log('policy_proposal', {'step': obs.step, 'actions': [a.json() for a in prefix.actions],
                                   'diagnostics': prefix.diagnostics, 'natural_prefix_length': n})
            start_step = obs.step
            executed = 0
            end_reason = 'natural_boundary'
            for action in prefix.actions[:n]:
                if obs.step >= env.horizon or clock() - before > wall_limit:
                    end_reason = 'resource_limit'
                    break
                prior = obs
                t = clock()
                stepped = env.step(action, correction=False)
                timing['env_s'] += clock() - t
                obs = stepped.observation
                if obs.episode != prior.episode or obs.step != prior.step + 1:
                    raise ContractError('non-contiguous physical ACK')
                if obs.instruction != state.context.original_task:
                    raise ContractError('original instruction mutated by environment or adapter')
                # Preserve a known physical ACK even if model-side acknowledgement fails.
                executed += 1
                metrics['native_steps'] += 1
                state.observe(obs)
                log('control_ack', {'step': obs.step, 'action': action.json(), 'eef': obs.eef,
                    'terminated': stepped.terminated, 'truncated': stepped.truncated,
                    'observation_sha256': obs.stamp})
                if stepped.terminated or stepped.truncated:
                    native_terminal_observed = True
                    native_success_observed = stepped.success
                    native_score = stepped.score
                t = clock()
                try:
                    policy.observe(obs)
                finally:
                    timing['ack_s'] += clock() - t
                # Evaluation signal can stop/score, never select a semantic subtask.
                if stepped.terminated or stepped.truncated:
                    native_success, native_score = stepped.success, stepped.score
                    result_status, termination = 'native_completed', 'native_terminal'
                    end_reason = 'native_terminal'
                    break
                if obs.signals.get('controller_fault') is True:
                    metrics['controller_faults'] += 1
                    result_status, termination = 'controller_fault', 'native_controller_fault'
                    end_reason = 'controller_fault'
                    break
                # Soft tracking/gripper/stagnation events do NOT truncate this prefix.
            completion = policy.finish_prefix(executed, end_reason)
            metrics['natural_suffix_discards'] += completion['natural_unexecuted_prediction_suffix']
            metrics['abort_prefix_discards'] += completion['unexecuted_prefix']
            metrics['completed_prefixes'] += int(executed == n)
            receipt = {'start_step': start_step, 'end_step': obs.step, 'executed_steps': executed,
                       'stop_reason': end_reason, 'semantic_epoch': state.context.epoch,
                       'original_task_unchanged': True,
                       'object_effect': 'not_certified_by_robot_motion', 'source_prefix_receipt': completion}
            receipts.append(receipt)
            log('motor_prefix_receipt', receipt)
            prefix = None
            if result_status in ('native_completed', 'controller_fault'):
                break
            if end_reason == 'resource_limit':
                result_status, termination = 'resource_limited', 'native_or_wall_budget'
                break
        if result_status == 'incomplete':
            result_status, termination = 'resource_limited', 'native_step_budget_without_terminal_ack'
        final = env.finish(termination)
        if result_status == 'native_completed':
            if final.get('success') is True and not native_success:
                raise ContractError('finish and terminal ACK disagree')
            if final.get('score') is not None:
                native_score = final['score']
        capture(obs)
    except Exception as exc:
        result_status = 'infrastructure_or_contract_error'
        termination = type(exc).__name__
        error = str(exc)[:1000]
        log('error', {'error_type': termination, 'detail': error, 'automatic_retry': False})
        try:
            env.finish('error:' + termination)
        except Exception:
            pass
    finally:
        # Missing ACKs remain unresolved; never pretend a failed request did not move.
        metrics['unresolved_policy_actions'] = max(0, metrics['predicted_policy_actions'] - metrics['native_steps']
            - metrics['natural_suffix_discards'] - metrics['abort_prefix_discards'])
        for item in (env, policy, planner):
            if item is not None:
                try:
                    item.close()
                except Exception as exc:
                    log('cleanup_error', {'type': type(exc).__name__, 'detail': str(exc)[:300]})
    result = {'schema': 'semantic.result.v1', 'case_id': case['case_id'], 'task': case['task'],
              'benchmark': case['benchmark'], 'partition': case.get('partition', 'dev'),
              'task_group': case.get('task_group', case['task']), 'condition': config['name'], 'mode': mode,
              'success': bool(native_success and result_status == 'native_completed'),
              'native_score': native_score, 'native_terminal_observed': native_terminal_observed,
              'native_success_observed': native_success_observed, 'status': result_status, 'termination': termination, 'error': error,
              'native_steps': metrics['native_steps'], 'elapsed_s': clock() - before, 'timing': timing,
              'simulated_seconds': metrics['native_steps'] / obs.control_hz if obs else 0.,
              'metrics': metrics, 'usage': usage_summary(planner),
              'shadow_planner_disabled_after_failure': shadow_planner_disabled,
              'config_sha256': digest(config), 'case_sha256': digest(case),
              'policy_identity': policy.identity.identity,
              'initial_observation_sha256': initial_stamp,
              'environment_contract_sha256': digest(env.describe()) if obs else None,
              'planner_config': config.get('model') if planner else None,
              'evidence_kind': getattr(env, 'evidence_kind', 'native_unqualified'),
              'simulation_advances_during_model_wait': False,
              'task_solution_memory': False, 'weight_updates': False}
    atomic_json(root / 'result.json', result)
    atomic_json(root / 'receipts.json', receipts)
    atomic_json(root / 'prompt_exposures.json', exposures)
    log('episode_end', result)
    journal.close()
    return result
