"""Symbolic slow-brain interface. Exact source prompt is not published in the PDF."""
from dataclasses import dataclass
from pathlib import Path
import time
from ..errors import ValidationError
from ..util import digest, plain, atomic_json
from ..planners.compatible_api import CompatibleAPIPlanner
from ..planners.local import FilePlanner, CommandPlanner
from .capabilities import SCHEMAS

PROMPT = '''You are the semantic slow brain in a simulated manipulation experiment.
Read the original task, scene entities, two current images, and recorded local
outcomes. Propose an available capability with symbolic entity names and goal
relations. Never emit metric poses, numeric offsets, velocities, gains, budgets,
or invented object names. The physical governor grounds all geometry, checks
preconditions, and may refuse an unresolvable step. Do not equate TCP arrival or
a closed gripper with a successful grasp. Use the actual local execution evidence
and preserve entity identity. Completed operations remain in history. A destination
may be a support, a receptacle, or a cavity; do not turn a support placement into
an insertion. Use the frozen VLA only when no suitable analytic route is available.
Perception acquires a fresh context; finish requests stopping, not success.
Do not read experiment files, benchmark goal clauses, or future observations.
Give a short observable decision summary, not a private reasoning transcript.
The same prompt/catalog is used for nominal and dynamic single-step planners.
'''


@dataclass(frozen=True)
class Advisory:
    capability: str
    arguments: dict
    summary: str = ''


@dataclass(frozen=True)
class Plan:
    steps: tuple[Advisory,...]
    observation_id: str
    created_at: float
    scene_epoch: int
    task_epoch: int


def decode_plan(answer,context):
    sequence=context.get('output_mode')=='sequence'
    if not isinstance(answer,dict):raise ValidationError('plan_not_object')
    if sequence:
        if set(answer)-{'steps','decision_summary'}:raise ValidationError('sequence_extra_fields')
        raw=answer.get('steps')
    else:raw=[answer]
    if not isinstance(raw,list) or not 1<=len(raw)<=24:raise ValidationError('invalid_plan_length')
    known={c['name'] for c in context['capabilities']};out=[]
    for step in raw:
        if not isinstance(step,dict) or set(step)-{'capability','arguments','decision_summary'}:
            raise ValidationError('intent_must_be_symbolic')
        name=step.get('capability');args=step.get('arguments')
        if name not in known or not isinstance(args,dict):raise ValidationError('invalid_intent')
        req,opt=SCHEMAS[name]
        if set(req)-set(args) or set(args)-set(req+opt):raise ValidationError('symbolic_schema_mismatch')
        if any(not isinstance(v,str) or not v or len(v)>2000 for v in args.values()):
            raise ValidationError('numeric_or_nested_slow_brain_argument')
        if 'relation' in args and args['relation'] not in ('on','in','left_of','right_of','front_of','behind','next_to'):
            raise ValidationError('invalid_relation')
        if 'state' in args and args['state'] not in ('open','closed','on','off'):
            raise ValidationError('invalid_mechanism_state')
        if 'method_constraint' in args and args['method_constraint'] not in ('final_relation','push_only'):
            raise ValidationError('invalid_method_constraint')
        text=step.get('decision_summary','')
        if not isinstance(text,str) or len(text)>2000:raise ValidationError('bad_decision_summary')
        out.append(Advisory(name,args,text))
    o=context['observation']
    return Plan(tuple(out),o['observation_id'],context.get('context_created_monotonic',time.monotonic()),o['scene_epoch'],o['task_epoch'])


def context_for(scene,library,memory,remaining,request_id,*,sequence=False,reason='initial'):
    step={'type':'object','properties':{
        'capability':{'type':'string','enum':list(library.names)},
        'arguments':{'type':'object','additionalProperties':{'type':'string'}},
        'decision_summary':{'type':'string'}},'required':['capability','arguments'],
        'additionalProperties':False}
    schema=({'type':'object','properties':{'steps':{'type':'array','items':step,'minItems':1,'maxItems':24},
                                         'decision_summary':{'type':'string'}},
             'required':['steps'],'additionalProperties':False} if sequence else step)
    return {'system':PROMPT+('\nReturn a complete ordered sequence once; it will be frozen.' if sequence else
                              '\nReturn exactly one next capability.'),
            'observation':scene.symbolic_view(),'capabilities':library.catalog(),
            'history':memory.summary(),'remaining_native_steps':remaining,
            'proposal_id':request_id,'context_created_monotonic':time.monotonic(),'output_mode':'sequence' if sequence else 'one_step',
            'request_reason':reason,'json_schema':schema}


class PaperPlanner:
    def __init__(self,config,ledger,settings,allow_api=False):
        kind=config['kind']; self.settings=settings
        if kind=='api':
            cfg={**config,'max_output_tokens':settings.planner_max_tokens,
                 'timeout_s':settings.planner_timeout_s,
                 'extra_request':{**config.get('extra_request',{}),'temperature':settings.planner_temperature}}
            self.inner=CompatibleAPIPlanner(cfg,ledger,allow_api=allow_api,decoder=decode_plan)
        elif kind=='file':self.inner=FilePlanner(config['queue'],settings.planner_timeout_s,decoder=decode_plan)
        elif kind=='command':self.inner=CommandPlanner(config['command'],settings.planner_timeout_s,decoder=decode_plan)
        else:raise ValidationError('unsupported_paper_planner:'+kind)
        self.identity=self.inner.identity
        self.calls=0

    def decide(self,context,out):
        # One serialization-only repair. Never silently retry an uncertain HTTP
        # request, action, or failed plan for a better answer.
        from ..errors import BudgetExceeded
        for attempt in range(self.settings.serialization_repairs+1):
            if self.calls>=self.settings.max_planner_calls:raise BudgetExceeded('planner_call_ceiling')
            d=Path(out)/f'serialization_{attempt}';d.mkdir(parents=True,exist_ok=False)
            c=dict(context)
            if attempt:
                c['proposal_id']+=f':repair{attempt}'
                c['serialization_error']=error
                c['system']+='\nRepair serialization/schema only; follow the supplied JSON schema.'
            atomic_json(d/'context.json',c); self.calls+=1
            try:
                answer=self.inner.decide(c,d)
                atomic_json(d/'decoded.json',plain(answer)); return answer
            except ValidationError as e:
                error=str(e);atomic_json(d/'rejected.json',{'reason':error})
                if attempt==self.settings.serialization_repairs:raise
