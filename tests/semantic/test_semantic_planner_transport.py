from dataclasses import asdict
import json
import pytest
from k1lab.errors import ContractError
from k1lab.util import digest
from k1lab.multibench.transport import encode_obs
from semantic_lab.contracts import SemanticContext
from semantic_lab.policy import InstructionPolicy
from semantic_lab.planner import SemanticPlanner, tool_schema
from semantic_lab.synthetic import ToyEnvironment, ToyPolicy, ToyPlanner
from semantic_lab.state import SemanticState
from semantic_lab.transport import SemanticDispatcher, SemanticRemotePolicy
from semantic_lab.tau_reference import export_sample


def test_planner_exact_tool_contract_and_no_lowlevel_actions(tmp_path):
    class Response:
        def __init__(self, body): self.body = body
        def json(self): return self.body
    class Client:
        def post(self, _, headers, json):
            self.payload = json
            return Response({'choices': [{'message': {'tool_calls': [{'function': {
                'name': 'semantic_goal', 'arguments': __import__('json').dumps(d.wire())}}]}}]})
        def __exit__(self): pass
    obs = ToyEnvironment().obs(); state = SemanticState(obs.instruction, 'subtask_only'); state.observe(obs)
    d = ToyPlanner().decide(obs, state, [], None)
    client = Client(); planner = SemanticPlanner({'model': 'configured-model'}, tmp_path, client=client)
    assert planner.decide(obs, state, [], None) == d
    schema = tool_schema()['function']['parameters']['properties']
    assert 'actions' not in schema and 'steps' not in schema
    assert schema['operation']['enum'] == ['continue', 'set_subtask', 'recover', 'stop']
    assert 'assessment=failed' in schema['operation']['description']
    assert 'never uncertain' in schema['assessment']['description']
    assert len([b for b in client.payload['messages'][1]['content'] if b['type'] == 'image_url']) == 1
    bound = client.payload['tools'][0]['function']['parameters']['properties']
    for name, value in {'episode': obs.episode, 'based_on_step': obs.step,
                        'based_on_stamp': obs.stamp, 'expected_epoch': state.context.epoch}.items():
        assert bound[name]['enum'] == [value]
    assert bound['based_on_stamp']['minLength'] == bound['based_on_stamp']['maxLength'] == 64


def test_planner_rejects_overlength_stamp_even_if_provider_ignores_schema(tmp_path):
    obs = ToyEnvironment().obs()
    state = SemanticState(obs.instruction, 'subtask_only'); state.observe(obs)
    value = ToyPlanner().decide(obs, state, [], None).wire()
    value['based_on_stamp'] += 'extra'
    class Client:
        def post(self, _, headers, json):
            class Response:
                def json(self):
                    return {'choices': [{'message': {'tool_calls': [{'function': {
                        'name': 'semantic_goal', 'arguments': __import__('json').dumps(value)}}]}}]}
            return Response()
    planner = SemanticPlanner({'model': 'configured-model'}, tmp_path, client=Client())
    with pytest.raises(ContractError, match='decision requires observation SHA256'):
        planner.decide(obs, state, [], None)
    assert not planner.history and not planner.last_images
    assert state.context.epoch == 0


def test_tool_schema_rejects_partial_request_binding():
    with pytest.raises(ContractError, match='all request identity fields'):
        tool_schema({'based_on_stamp': 'a' * 64})


def test_dispatcher_context_and_prefix_ops_reject_sequence_replay():
    wrapper = InstructionPolicy(ToyPolicy(), kind='test'); server = SemanticDispatcher(wrapper)
    seq = 0
    def call(op, args):
        nonlocal seq
        req = {'op': op, 'args': args, 'owner': 'owner', 'seq': seq}
        envelope = {'request': req, 'request_sha256': digest(req)}
        result = server.dispatch(envelope); seq += 1
        return result, envelope
    r, _ = call('acquire', {}); assert r['result']['semantic_protocol'] == 'semantic-policy.v1'
    call('reset', {})
    env = ToyEnvironment(); obs = env.obs()
    call('semantic_context', {'context': asdict(SemanticContext(obs.instruction))})
    _, envelope = call('observe', {'observation': encode_obs(obs)})
    with pytest.raises(ContractError): server.dispatch(envelope)
    r, _ = call('propose', {'observation': encode_obs(obs)})
    assert r['result']['diagnostics']['semantic']['effective_prompt'] == obs.instruction
    with pytest.raises(ContractError): call('finish_prefix', {'executed': 3, 'reason': 'natural_boundary'})


def test_tau_export_requires_actual_three_cameras(tmp_path):
    env = ToyEnvironment(); obs = env.obs(); ctx = SemanticContext(obs.instruction)
    with pytest.raises(ContractError): export_sample(obs, ctx, tmp_path / 'bad')
    obs.rgb.update(cam_left_wrist=obs.rgb['cam_high'].copy(), cam_right_wrist=obs.rgb['cam_high'].copy())
    row = export_sample(obs, ctx, tmp_path / 'good')
    assert row['task_type'] == 'full_qa' and 'answer' not in row
    assert row['memory'] == '(empty)'


def test_tau_export_rejects_duplicate_camera_alias(tmp_path):
    obs = ToyEnvironment().obs()
    with pytest.raises(ContractError):
        export_sample(obs, SemanticContext(obs.instruction), tmp_path,
                      cameras={'head': 'cam_high', 'left': 'cam_high', 'right': 'cam_high'})


def test_remote_policy_end_to_end_via_mock_http(tmp_path):
    import httpx
    from semantic_lab.runner import run_episode
    from semantic_lab.audit import audit
    wrapper = InstructionPolicy(ToyPolicy(), kind='test')
    dispatcher = SemanticDispatcher(wrapper)
    operations = []
    def transport(request):
        envelope = json.loads(request.content)
        operations.append(envelope['request']['op'])
        return httpx.Response(200, json=dispatcher.dispatch(envelope))
    client = httpx.Client(transport=httpx.MockTransport(transport))
    remote = SemanticRemotePolicy({'identity': asdict(wrapper.identity), 'endpoint':'http://127.0.0.1:9999'},
                                  allow_policy=True, client=client)
    env = ToyEnvironment(horizon=12)
    case = dict(case_id='c',task='t',task_group='t',benchmark='synthetic',partition='dev')
    cfg = dict(name='remote', mode='semantic_subtask_hierarchy',prompt_mode='task_plus_subtask',
               semantic_schedule=dict(review_interval_steps=6,minimum_dwell_steps=3,event_cooldown_steps=3))
    result = run_episode(env,remote,ToyPlanner(),case,cfg,tmp_path)
    assert result['success'] and operations.count('propose') == 4
    assert operations.count('observe') == 13
    assert operations.count('finish_prefix') == 4
    assert operations.count('semantic_context') == 2
    assert 'invalidate' not in operations
    assert audit(tmp_path)['actual_control_acks'] == 12
