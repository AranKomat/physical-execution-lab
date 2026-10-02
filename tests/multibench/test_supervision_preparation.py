import json
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize('benchmark,prefix', [
    ('robodojo', 'robodojo_g05'), ('robocasa365', 'robocasa365_xiaomi')])
def test_supervision_preparation_preserves_motor_provider(tmp_path, benchmark, prefix):
    source = tmp_path / 'bound'
    source.mkdir()
    provider = {'identity': {'name': 'bound-provider'}, 'port': 19611}
    for mode in ('motor_only', 'review_every_chunk', 'sparse'):
        (source / f'{prefix}_{mode}.json').write_text(json.dumps({
            'benchmark': benchmark, 'policy': provider,
            'environment': {'backend': 'unchanged', 'xiaomi_root': '/bound/xr1'},
            'model': {'model': 'gpt-6.1-sol', 'service_tier': 'flex'}}))
    script = Path(__file__).resolve().parents[2] / 'scripts/multibench/prepare_supervision_pilot.py'
    out = tmp_path / 'pilot'
    subprocess.run([sys.executable, str(script), '--benchmark', benchmark,
                    '--bound-root', str(source), '--output', str(out)], check=True)
    for mode in ('motor_only', 'review_every_chunk', 'sparse'):
        cfg = json.loads((out / f'{prefix}_{mode}.json').read_text())
        assert cfg['policy'] == provider
        assert cfg['model']['service_tier'] == 'flex'
        assert cfg['model']['max_requests'] == cfg['max_reviews'] == 75
        assert cfg['paid_route']['request_normalization']['remove'] == ['parallel_tool_calls']
        if benchmark == 'robocasa365':
            assert 'gpt_as_policy_root' not in cfg['environment']


def test_pi05_comparison_profile_is_explicit(tmp_path):
    source=tmp_path/'bound';source.mkdir()
    provider={'identity':{'name':'pi05'},'endpoint':'http://127.0.0.1:19611'}
    for mode in ('motor_only','review_every_chunk','sparse'):
        (source/f'robodojo_pi05_{mode}.json').write_text(json.dumps({
            'benchmark':'robodojo','policy':provider,'environment':{},
            'model':{'model':'gpt-6.1-sol','service_tier':'flex'}}))
    script=Path(__file__).resolve().parents[2]/'scripts/multibench/prepare_supervision_pilot.py'
    out=tmp_path/'comparison'
    subprocess.run([sys.executable,str(script),'--bound-root',str(source),
        '--output',str(out),'--prefix','robodojo_pi05','--profile','comparison180'],check=True)
    for mode in ('motor_only','review_every_chunk','sparse'):
        cfg=json.loads((out/f'robodojo_pi05_{mode}.json').read_text())
        assert cfg['policy']==provider
        assert cfg['max_reviews']==cfg['model']['max_requests']==180
        assert cfg['model']['max_total_output_tokens']==368640
        assert cfg['wall_limit_s']==3600
        assert cfg['paid_route']['local_cap_usd']=='3'
        assert cfg['paid_route']['shared_ceiling_usd']=='85'
