from copy import deepcopy
import pytest
from k1lab.errors import ContractError
from k1lab.multibench.manifest import seal
from semantic_lab.reference import bind_reference_wave


def manifest():
    rows = [{'case_id': f't__l{i}', 'task': 't', 'runtime_task': 't_random',
             'task_group': 't', 'partition': 'test', 'benchmark': 'robodojo',
             'eval_seed': 0, 'layout_id': i, 'layout_sha256': 'a' * 64,
             'layout_path': f'Assets/{i}.json', 'horizon': 1050, 'native_hz': 25}
            for i in range(2)]
    return seal({'formal': True, 'cases': rows})


def test_reference_binding_preserves_order_variant_and_test_partition():
    source = manifest(); original = deepcopy(source)
    rows = bind_reference_wave(source, ['t__l1', 't__l0'], 't_random')
    assert [r['layout_id'] for r in rows] == [1, 0]
    assert all(r['partition'] == 'test' for r in rows)
    rows[0]['layout_path'] = 'changed'
    assert source == original


@pytest.mark.parametrize('ids,task', [(['t__l0', 't__l0'], 't_random'),
                                    (['absent'], 't_random'), (['t__l0'], 't')])
def test_reference_binding_refuses_replacement_duplicates_and_variant_mix(ids, task):
    with pytest.raises(ContractError):
        bind_reference_wave(manifest(), ids, task)


def test_reference_binding_refuses_changed_manifest():
    data = manifest(); data['cases'][0]['layout_id'] = 99
    with pytest.raises(ContractError, match='manifest hash mismatch'):
        bind_reference_wave(data, ['t__l0'], 't_random')
