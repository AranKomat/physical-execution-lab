"""Compact within-episode context. No cross-task retrieval, recipes or action demos."""
from __future__ import annotations
import base64
import io
import json
from collections import deque
from dataclasses import dataclass, field
import numpy as np
from scipy.spatial.transform import Rotation
from k1lab.errors import ContractError
from k1lab.model_client import Client
from .types import Action

SYSTEM = '''You supervise one robot episode using current camera images, robot proprioception,
robot-only proposal previews, and receipts from this episode. No task solutions or cross-episode memory.
Use the original instruction. Separately assess the LAST execution outcome and the NEXT proposed intent.
A valid trajectory is not a correct task action. Gripper commands are not measured attachment.
Completion/progress claims are fallible and retractable. Preserve the original task objective.
Choose accept/shorten when the motor proposal is useful, including self-recovery. Correct only an observed
execution failure or a semantically misaligned next action. Uncertainty alone does not justify a correction:
shorten the action horizon for observation, or stop as an unsuccessful/incomplete attempt if proceeding
is inappropriate. Do not claim that robot-only FK predicts contact or object movement.
For direct mode there is no motor policy. Choose bounded robot actions from the current observation.
Each decision returns a compact public evidence summary, not a private chain of thought.
Do not read simulator internals, evaluator rewards, target-task scripts or other episodes.
'''

@dataclass
class Decision:
    mode: str
    steps: int = 0
    actions: list[Action] = field(default_factory=list)
    execution: str = 'uncertain'
    intent: str = 'uncertain'
    evidence: str = ''
    progress: dict = field(default_factory=dict)


def schema(space, max_steps, direct=False):
    return {'type':'function','function':{
        'name':'robot_decision','description':'One bounded execution decision; no task-specific routine.',
        'parameters':{'type':'object','additionalProperties':False,
        'properties':{
            'mode':{'type':'string','enum':['correct','stop'] if direct else ['accept','shorten','correct','stop']},
            'steps':{'type':'integer','minimum':0,'maximum':max_steps},
            'actions':{'type':'array','maxItems':max_steps,'items':{'type':'array','items':{'type':'number'}}},
            'execution':{'type':'string','enum':['not_started','progressing','failed','uncertain','recovered']},
            'intent':{'type':'string','enum':['aligned','misaligned','uncertain']},
            'evidence':{'type':'string'},
            'progress':{'type':'object','additionalProperties':False,'properties':{
                'completed_claims':{'type':'array','items':{'type':'string'},'maxItems':12},
                'currently_attempting':{'type':'string'},
                'uncertain_or_invalidated':{'type':'array','items':{'type':'string'},'maxItems':12}},
                'required':['completed_claims','currently_attempting','uncertain_or_invalidated']}},
        'required':['mode','steps','actions','execution','intent','evidence','progress']}}}


def decode(value, obs, proposal, correction_space, max_steps, *, direct=False,
           translation_limit=.05, rotation_limit=.35):
    if not isinstance(value,dict) or set(value)!= {'mode','steps','actions','execution','intent','evidence','progress'}:
        raise ContractError('invalid decision keys')
    mode=value['mode']; steps=value['steps']
    if mode not in (('correct','stop') if direct else ('accept','shorten','correct','stop')):
        raise ContractError('invalid decision mode')
    if type(steps) is not int or not 0<=steps<=max_steps:
        raise ContractError('invalid decision length')
    if value['execution'] not in ('not_started','progressing','failed','uncertain','recovered') or value['intent'] not in ('aligned','misaligned','uncertain'):
        raise ContractError('invalid outcome/intent status')
    if not isinstance(value['evidence'],str) or not 1<=len(value['evidence'])<=1800:
        raise ContractError('bounded public evidence summary required')
    p=value['progress']
    if not isinstance(p,dict) or set(p)!= {'completed_claims','currently_attempting','uncertain_or_invalidated'}:
        raise ContractError('invalid progress ledger')
    if not isinstance(p['currently_attempting'],str) or len(p['currently_attempting'])>400:
        raise ContractError('invalid current goal')
    for key in ('completed_claims','uncertain_or_invalidated'):
        if not isinstance(p[key],list) or len(p[key])>12 or any(not isinstance(t,str) or len(t)>300 for t in p[key]):
            raise ContractError('bounded progress list required')
    actions=[]
    if mode=='correct':
        if not direct and value['execution']!='failed' and value['intent']!='misaligned':
            raise ContractError('takeover needs observed failure or wrong intent, not uncertainty alone')
        if steps<1 or not isinstance(value['actions'],list) or len(value['actions']) not in (1,steps):
            raise ContractError('correction needs one held target or one action per step')
        actions=[Action(correction_space,a) for a in value['actions']]
        if correction_space=='x5_eef16_wxyz':
            for a in actions:
                for arm,off in (('left',0),('right',8)):
                    now=obs.eef[arm]
                    if np.linalg.norm(a.values[off:off+3]-now['xyz'])>translation_limit+1e-6:
                        raise ContractError('correction target outside translation bound')
                    q=a.values[off+3:off+7][[1,2,3,0]]
                    angle=(Rotation.from_quat(q)*Rotation.from_quat(now['quaternion_xyzw']).inv()).magnitude()
                    if angle>rotation_limit+1e-6:raise ContractError('correction rotation bound')
        elif correction_space=='robocasa12':
            # Arm-only bounded normalized corrections. No unqualified mobile-base or mode switching.
            for a in actions:
                if np.any(np.abs(a.values[:6])>.25+1e-6) or abs(a.values[6])>1 or np.any(a.values[7:11]!=0) or a.values[11]!=-1:
                    raise ContractError('RoboCasa correction: |arm controls|<=.25, |gripper|<=1, base=0, mode=-1')
        else:raise ContractError('unsupported correction convention')
    elif mode=='stop':
        if steps or value['actions']:raise ContractError('stop executes no actions')
    else:
        if proposal is None or not 1<=steps<=len(proposal.actions) or value['actions']:
            raise ContractError('accept/shorten must use the fresh unmodified proposal')
    return Decision(mode,steps,actions,value['execution'],value['intent'],value['evidence'],p)


class ModelReviewer:
    def __init__(self, config, output, journal=None, allow_api=False, client=None):
        self.config=dict(config)
        self.client=client or Client(config,output,journal,allow_api)
        self.memory=deque(maxlen=int(config.get('history_rounds',4)))
        self.progress={}
        self.last_images=[]
        self.last_service_tier=None

    def reset(self):self.memory.clear();self.progress={};self.last_images=[]

    def note_execution_start(self,obs):
        self.last_images=[(obs.step,k,v.copy()) for k,v in sorted(obs.rgb.items())]

    def review(self, obs, proposal, reasons, receipt, contract, direct=False):
        from PIL import Image
        space=contract['correction_space']
        context=obs.actor_state()
        context.update(reasons_for_review=reasons,previous_execution=receipt,
                       task_progress_claims=self.progress,action_contract=contract,
                       episode_history=list(self.memory))
        if proposal is not None:
            # Only robot motion geometry: do not infer semantic intent in a deterministic summarizer.
            ids=np.unique(np.linspace(0,len(proposal.actions)-1,min(8,len(proposal.actions))).astype(int))
            context['proposal']={'length':len(proposal.actions),'sampled_indices':ids.tolist(),
                                 'actions':[proposal.actions[i].json() for i in ids],
                                 'robot_preview':proposal.diagnostics.get('robot_preview'),
                                 'warning':'Proposed robot motion only; no future object or contact prediction.'}
        blocks=[{'type':'text','text':json.dumps(context)}]
        image_sets=[(obs.step,k,v,'CURRENT') for k,v in sorted(obs.rgb.items())]
        image_sets += [(step,k,v,'HISTORICAL before last executed segment') for step,k,v in self.last_images if step!=obs.step]
        for frame,label,arr,when in image_sets:
            image=Image.fromarray(arr)
            edge=int(self.config.get('image_max_edge',480))
            if edge>0:image.thumbnail((edge,edge))
            buf=io.BytesIO();image.save(buf,format='JPEG',quality=90)
            blocks.extend([{'type':'text','text':f'{when} {label} frame {frame}; original {arr.shape[1]}x{arr.shape[0]}; preview {image.width}x{image.height}. No depth supplied.'},
                {'type':'image_url','image_url':{'url':'data:image/jpeg;base64,'+base64.b64encode(buf.getvalue()).decode()}}])
        request={'model':self.config['model'],'messages':[{'role':'system','content':SYSTEM},
                  {'role':'user','content':blocks}],
                 'tools':[schema(space,contract['max_decision_steps'],direct)],'tool_choice':'required'}
        reply=self.client.post('',headers={},json=request).json()
        call=reply['choices'][0]['message']['tool_calls'][0]
        value=json.loads(call['function']['arguments'])
        dec=decode(value,obs,proposal,space,contract['max_decision_steps'],direct=direct,
                   translation_limit=contract.get('translation_limit_m',.05),rotation_limit=contract.get('rotation_limit_rad',.35))
        if dec.mode=='correct' and dec.steps>contract.get('max_correction_steps',5):
            raise ContractError('correction exceeds configured correction horizon')
        self.progress=dec.progress
        self.memory.append({'step':obs.step,'mode':dec.mode,'evidence':dec.evidence,
                            'last_receipt':receipt,'progress_is_model_claim':True})
        return dec

    def close(self):self.client.__exit__()
