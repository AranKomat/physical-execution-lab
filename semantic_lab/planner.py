"""General-language subtask planning; no motor actions and no task recipe lookup."""
from __future__ import annotations
import base64
import io
import json
from collections import deque
from PIL import Image
from k1lab.errors import ContractError
from k1lab.model_client import Client
from .contracts import SemanticDecision

SYSTEM = '''You choose the next semantic subtask for a frozen robot policy.
The overall task is immutable. Use current RGB, robot proprioception and current-episode
receipts/memory only. Return one coherent, observable physical state transition, normally
lasting multiple motor action chunks. Use concise natural language with the relevant object,
relation and arm only when supported by observation. Do not produce joint coordinates,
EEF waypoints, executable code, a task recipe, or a list of low-level motions.
Examples of granularity (not solutions): grasp a handle; open an appliance; put an object
in a receptacle. Prefer one useful physical state change, not an entire long task.
CONTINUE means exactly retain the current goal; it does not shorten, reset or resample the
motor policy. For CONTINUE, subtask must be empty or an exact copy of the current goal;
for STOP it must be empty. Do not rephrase an unchanged goal. SET_SUBTASK updates language at a normal
motor boundary. RECOVER is an evidence-backed replacement semantic goal after a failed
subtask and is allowed only if the run enables it. STOP means incomplete/abstention, never
benchmark success. A closed gripper is not proof of holding anything. Revoke progress
claims contradicted by later observations. Cite available observation step IDs for claims.
Use uncertainty honestly: a moving hand or robot FK is not task progress or future contact.
Do not use hidden simulator state, scoring predicates, previous-episode solutions or demos.
The underlying motor policy may not understand added prompt fields; do not assume it does.
Return a compact public evidence summary, not private chain-of-thought.
RECOVER requires assessment exactly "failed", evidence identifying that failure, and
allow_semantic_recovery=true. Never convert uncertainty into failure to pass this gate.
If assessment is "uncertain", use CONTINUE or ordinary SET_SUBTASK replanning where
the minimum-dwell rule permits it; do not use RECOVER. Disabled recovery stays disabled.
'''


def tool_schema(binding=None):
    claim = {'type': 'object', 'additionalProperties': False,
             'properties': {'text': {'type': 'string', 'maxLength': 400},
                            'evidence_steps': {'type': 'array', 'minItems': 1, 'maxItems': 12,
                                               'items': {'type': 'integer', 'minimum': 0}}},
             'required': ['text', 'evidence_steps']}
    props = {
        'episode': {'type': 'string'},
        'based_on_step': {'type': 'integer', 'minimum': 0},
        'based_on_stamp': {'type': 'string', 'minLength': 64, 'maxLength': 64},
        'expected_epoch': {'type': 'integer', 'minimum': 0},
        'operation': {'type': 'string', 'enum': ['continue', 'set_subtask', 'recover', 'stop'],
                      'description': 'recover requires assessment=failed and recovery enabled; uncertain replanning uses set_subtask subject to minimum dwell, or continue.'},
        'subtask': {'type': 'string', 'maxLength': 600},
        'assessment': {'type': 'string', 'enum': ['not_started', 'progressing', 'complete', 'failed', 'uncertain'],
                       'description': 'Honest observed assessment. recover is legal only with failed, never uncertain.'},
        'evidence': {'type': 'string', 'maxLength': 1800},
        'completed_claims': {'type': 'array', 'maxItems': 12, 'items': claim},
        'uncertain_or_invalidated': {'type': 'array', 'maxItems': 12, 'items': {'type': 'string', 'maxLength': 400}},
    }
    if binding is not None:
        if set(binding) != {'episode', 'based_on_step', 'based_on_stamp', 'expected_epoch'}:
            raise ContractError('semantic tool binding requires all request identity fields')
        for name, value in binding.items():
            props[name]['enum'] = [value]
    return {'type': 'function', 'function': {'name': 'semantic_goal',
            'description': 'One language subtask decision, never a motor-control decision.',
            'parameters': {'type': 'object', 'additionalProperties': False,
                           'properties': props, 'required': list(props)}}}


class SemanticPlanner:
    def __init__(self, config, output, *, allow_api=False, client=None, journal=None):
        self.config = dict(config)
        self.client = client or Client(config, output, journal, allow_api)
        self.history = deque(maxlen=int(config.get('history_rounds', 4)))
        self.last_images = []

    def reset(self):
        self.history.clear()
        self.last_images = []

    def decide(self, obs, state, reasons, receipt):
        packet = {'observation': obs.actor_state(), 'semantic_state': state.packet(),
                  'request_binding': {'episode': obs.episode, 'based_on_step': obs.step,
                                      'based_on_stamp': obs.stamp, 'expected_epoch': state.context.epoch},
                  'reasons': reasons, 'last_execution_receipt': receipt,
                  'schedule': {'allow_semantic_recovery': state.schedule.allow_semantic_recovery},
                  'previous_reviews': list(self.history),
                  'depth_available': False,
                  'model_progress_is_not_native_success': True}
        blocks = [{'type': 'text', 'text': json.dumps(packet, ensure_ascii=False)}]
        images = [(obs.step, k, a, 'CURRENT') for k, a in sorted(obs.rgb.items())]
        images += [(step, k, a, 'HISTORICAL previous semantic review')
                   for step, k, a in self.last_images if step != obs.step]
        for step, camera, arr, when in images:
            image = Image.fromarray(arr)
            edge = int(self.config.get('image_max_edge', 480))
            if edge > 0:
                image.thumbnail((edge, edge))
            buf = io.BytesIO()
            image.save(buf, format='JPEG', quality=90)
            blocks += [{'type': 'text', 'text': f'{when}; step={step}; camera={camera}; '
                        f'sensor pixels={arr.shape[1]}x{arr.shape[0]}; preview={image.width}x{image.height}; RGB only'},
                       {'type': 'image_url', 'image_url': {'url': 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()}}]
        payload = {'model': self.config['model'],
                   'messages': [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': blocks}],
                   'tools': [tool_schema(packet['request_binding'])], 'tool_choice': 'required'}
        response = self.client.post('', headers={}, json=payload).json()
        calls = response['choices'][0]['message'].get('tool_calls', [])
        if len(calls) != 1 or calls[0]['function']['name'] != 'semantic_goal':
            raise ContractError('exactly one semantic_goal response required')
        value = json.loads(calls[0]['function']['arguments'])
        decision = SemanticDecision.from_wire(value)
        self.history.append({'step': obs.step, 'decision': decision.wire()})
        self.last_images = [(obs.step, k, a.copy()) for k, a in sorted(obs.rgb.items())]
        return decision

    def close(self):
        self.client.__exit__()
