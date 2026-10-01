from __future__ import annotations
from pathlib import Path
from ..contracts import Proposal
from ..errors import ValidationError
from ..util import digest, atomic_json

SYSTEM_PROMPT = '''You operate a simulator through bounded physical capabilities. Use only supplied
observations, task text and evidence. Never infer hidden task success from a tool's
return value, gripper gap, or TCP arrival. A measured pixel is a visible surface,
not necessarily the object's center or a grasp. Choose targets and justified
small offsets. Inspect before and after contact. Use analytic motion for bounded
geometry, a frozen VLA for appropriate contact, and request fresh evidence when
uncertain. A long move is not collision-certified. Maintain a short observable
decision summary, not private chain of thought. Do not request resets, edit code,
read evaluator files or change budgets. No arbitrary execution tools are exposed.
Nominal and dynamic conditions have the same catalog. Supply one capability per
turn. Predeclared alternatives must preserve the original semantic effect.
The runtime supplies observation/proposal IDs; never replace them. The original
task remains authoritative. Only native environment termination establishes task
success. Finish is a request to stop, not a success claim.'''


def make_context(obs,registry,receipts,budget,proposal_id):
    return {'system':SYSTEM_PROMPT, 'proposal_id':proposal_id,
            'observation':obs.actor_view(),'capabilities':registry.catalog(),
            'recent_receipts':[r.actor_view() for r in receipts[-8:]],
            'budget':{'remaining_native_steps':budget.max_steps-budget.steps,
                      'remaining_decisions':budget.max_decisions-budget.decisions},
            'response_contract':{'capability':'name from catalog','arguments':{},
                'max_steps':'integer <= remaining budget, 0 for query',
                'decision_summary':'brief evidence-based decision',
                'objective':'physical goal for this operation','alternatives':[]}}


def bind_response(answer,context):
    if not isinstance(answer,dict): raise ValidationError('Planner response must be object')
    supplied=dict(answer)
    for key,value in [('proposal_id',context['proposal_id']),
                      ('observation_id',context['observation']['observation_id'])]:
        if key in supplied and supplied[key]!=value:
            raise ValidationError(f'Planner response changed {key}')
        supplied[key]=value
    return Proposal.from_dict(supplied)
