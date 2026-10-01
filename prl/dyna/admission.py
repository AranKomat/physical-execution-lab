"""Equation (5), p5: cell-level admission plus mandatory broader regression.

This is NOT v1's stricter 'retain every successful episode' rule. The paper protects
success COUNTS in policy-winning cells, not every individual stochastic seed.
No candidate is promoted from a targeted test alone. Attribution is a diagnostic
hypothesis; this module does not claim the PDF enumerates its exact 13 checks.
"""
from collections import defaultdict
from ..errors import ValidationError
from ..util import digest


def cell_key(row):return (row['case']['suite'],row['case']['task_id'])


def paired_gate(incumbent,candidate,policy,*,split='dev'):
    if split!='dev':raise ValidationError('no_test_set_admission')
    if not incumbent or not candidate or not policy:raise ValidationError('three_nonempty_paired_arms_required')
    groups=[]
    for rows in (incumbent,candidate,policy):
        m={r['identity']:r for r in rows}
        if len(m)!=len(rows):raise ValidationError('duplicate_gate_identity')
        groups.append(m)
    old,new,pi=groups
    if set(old)!=set(new) or set(old)!=set(pi):raise ValidationError('gate_pairing_mismatch')
    def success(r):return r['status']=='completed' and r.get('native_success') is True
    counts=[];harness=[];contamination=[];reasons=[]
    for label,rows in zip(('incumbent','candidate','policy'),groups):
        c=defaultdict(int);u=defaultdict(int);flags=0
        for r in rows.values():
            key=cell_key(r);c[key]+=int(success(r))
            flags+=int(bool(r.get('contamination_flags')) or r['status']!='completed')
            if not success(r) and label!='policy':
                a=r.get('attribution')
                if not isinstance(a,dict) or not isinstance(a.get('harness_attributed'),bool):
                    reasons.append('unresolved_attribution:'+label+':'+r['identity']);continue
                if a.get('status')!='reviewed':reasons.append('unreviewed_attribution:'+r['identity'])
                u[key]+=int(a['harness_attributed'])
        counts.append(c);harness.append(u);contamination.append(flags)
    if sum(counts[1].values())<sum(counts[0].values()):reasons.append('total_success_regression')
    if sum(harness[1].values())>sum(harness[0].values()):reasons.append('harness_failures_increased')
    for cell,n in counts[2].items():
        if n>0 and counts[1][cell]<counts[0][cell]:
            reasons.append('policy_winning_cell_regressed:'+str(cell))
    if contamination[1]:reasons.append('candidate_contamination')
    return {'decision':'reject' if reasons else 'eligible_for_broader_regression','reasons':reasons,
            'source':'arXiv:2609.40306v1 Eq.(5), pp5/14-15/32/37',
            'success_totals':[sum(c.values()) for c in counts],
            'harness_failure_totals':[sum(c.values()) for c in harness[:2]],
            'candidate_contamination':contamination[1],'pairs':len(old),
            'rule':'cell success counts, not preservation of every individual seed win'}


def admission(target_gate,broad_gate,*,candidate_hash,target_hash,broad_hash,required_cells,covered_cells):
    reasons=[]
    if not candidate_hash or candidate_hash!=target_hash or candidate_hash!=broad_hash:
        reasons.append('candidate_revision_changed_between_checks')
    for label,gate in (('target',target_gate),('broader',broad_gate)):
        if not gate or gate.get('decision')!='eligible_for_broader_regression':reasons.append(label+'_gate_not_passed')
    if not set(required_cells).issubset(set(covered_cells)):reasons.append('broader_coverage_incomplete')
    return {'decision':'reject' if reasons else 'admit_offline_candidate','reasons':reasons,
            'candidate_hash':candidate_hash,'deployment_authorized':False,
            'rule':'Admission changes an experiment library; it never authorizes hardware motion.'}


# Authoritative paper layer names and exact d_j checks are not in the supplied PDF.
# This configurable 13-label diagnostic is a transparent reconstruction.
LAYERS=(
 ('infrastructure',('transport','socket','connection','infrastructure')),
 ('evidence_integrity',('hash_mismatch','journal','partial_control')),
 ('context_freshness',('stale','epoch','expired')),
 ('plan_serialization',('schema','serialization','intent_must','numeric_or_nested')),
 ('semantic_entity_binding',('unresolved_entity','ambiguous_or_missing')),
 ('capability_catalog',('not_in_catalog','unimplemented_capability')),
 ('physical_grounding',('geometry','cavity','receptacle','mechanism_state')),
 ('command_admission',('cannot_afford','budget_exhausted','precondition')),
 ('execution_envelope',('velocity','command_lease','safety')),
 ('local_motion',('pose_not_reached','stagnation')),
 ('local_effect',('grasp_not_verified','effect_not_verified','joint_error')),
 ('recovery',('keyframe','reseat','recovery')),
 ('termination_or_policy',('planner_requested_finish','policy_segment_unverified','environment_step_budget','fixed_retry_exhaustion','tick_limit')),
)


def diagnose(events):
    """Return earliest supported layer. Never silently map no evidence to success."""
    messages=[]
    for e in events:
        if e.get('kind') in ('command_receipt','error','candidate_failed'):
            d=e.get('data',{});messages.append((str(d.get('reason','')),e.get('hash',str(e.get('seq')))))
    for i,(name,needles) in enumerate(LAYERS,1):
        hits=[h for text,h in messages if any(n in text for n in needles)]
        if hits:return {'candidate_layer':i,'name':name,'evidence':hits,'status':'unreviewed',
                       'harness_attributed':None,'causal_status':'diagnostic_hypothesis',
                       'taxonomy':'13-label reconstruction; not the unpublished original checks'}
    return {'status':'attribution_error','candidate_layer':None,'name':None,'evidence':[],
            'harness_attributed':None,'reason':'No matching diagnostic check; manual evidence review required'}
