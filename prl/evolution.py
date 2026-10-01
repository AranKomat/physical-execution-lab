"""Offline attribution and admission checks; no live self-modification.

Attributions are diagnostic hypotheses, not causal proof. The labels are our
explicit taxonomy, not a claimed transcription of DynaHarness's 13 layers.
"""
from __future__ import annotations
from .errors import ValidationError
from .evaluation import read_run,compare_runs
from .util import digest


def attribute(result):
    reason=result['reason']
    if result['status'] in ('infrastructure_error','uncertain_execution'):
        layer='infrastructure_or_execution_receipt'
    elif 'stale' in reason or 'future' in reason:layer='evidence_freshness'
    elif any(s in reason for s in ('unresolved','uncertain_target','depth','camera')):layer='grounding'
    elif any(s in reason for s in ('argument','unknown_capability','validation','workspace')):layer='command_contract'
    elif any(s in reason for s in ('stagnation','target_not_reached')):layer='local_control_or_geometry'
    elif 'finish' in reason:layer='termination_or_verification'
    elif result.get('native_success') is False:layer='capability_or_planning_unresolved'
    else:layer='none'
    return {'case_id':result['case']['case_id'],'candidate_layer':layer,
            'reason':reason,'causal_status':'hypothesis_only',
            'next_evidence':'Inspect current observations, native action trace and receipts before editing.'}


def regression_gate(baseline,candidate,policy_reference=None):
    ib,mb,cb,rb=read_run(baseline); ic,mc,cc,rc=read_run(candidate)
    if ib['split']!='dev' or ic['split']!='dev':
        raise ValidationError('Capability promotion may use development results only')
    comparison=compare_runs(baseline,candidate,contrast='evolution')
    reasons=[]
    if not comparison['complete']: reasons.append('incomplete_paired_development_evaluation')
    if comparison['wins_b_only']<comparison['wins_a_only']: reasons.append('total_success_regression')
    # Deliberately conservative software admission rule, stricter than only totals.
    for cid,r in rb.items():
        if r['status']=='completed' and r['native_success'] and (
            cid not in rc or rc[cid]['status']!='completed' or not rc[cid]['native_success']):
            reasons.append(f'previous_success_lost:{cid}')
    faults=lambda rs:sum(r['status']!='completed' for r in rs.values())
    if faults(rc)>faults(rb):reasons.append('more_infrastructure_or_protocol_faults')
    if policy_reference:
        ip,mp,cp,rp=read_run(policy_reference)
        if mp['sha256']!=mb['sha256'] or ip['source']!=ib['source']:
            raise ValidationError('policy_reference_manifest_or_source_mismatch')
        for cid,r in rp.items():
            if r['status']=='completed' and r['native_success'] and (
                cid not in rc or rc[cid]['status']!='completed' or not rc[cid]['native_success']):
                reasons.append(f'policy_reference_win_lost:{cid}')
    artifact={'decision':'reject' if reasons else 'eligible_for_broader_regression',
              'reasons':reasons,'baseline_code':ib['code_sha256'],'candidate_code':ic['code_sha256'],
              'manifest':mb['sha256'],'source':ib['source'],
              'note':'Does not deploy code, change models, claim hardware safety or unlock test-set tuning.'}
    artifact['sha256']=digest(artifact)
    return artifact
