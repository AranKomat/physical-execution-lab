from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

from k1lab.errors import ContractError
from k1lab.multibench.manifest import seal

spec = importlib.util.spec_from_file_location('rcprep', Path(__file__).resolve().parents[2] /
                                            'scripts/multibench/prepare_robocasa_development.py')
prep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prep)


def reference():
    tasks = ['CloseBlenderLid', *prep.ROSTER]
    return seal({'cases': [dict(case_id=f'{task}__e000', task=task, task_group=task,
        benchmark='robocasa365', split='pretrain', partition='test' if i == 0 else 'dev',
        trial=0, task_index=i, global_episode_index=i*50, environment_seed=7,
        episode_seed=7+i*50, horizon=900) for i, task in enumerate(tasks)]})


def categories():
    return {task: ('atomic_seen', 'composite_seen', 'composite_unseen')[i//2]
            for i, task in enumerate(prep.ROSTER)} | {'CloseBlenderLid': 'atomic_seen'}


def test_roster_preserves_seed_indices_and_quarantines_used_task():
    original = reference()
    full, pilot = prep.development_roster(original, categories())
    assert original['cases'][0]['partition'] == 'test'
    assert full['cases'][0]['partition'] == 'dev'
    assert [c['task'] for c in pilot['cases']] == list(prep.ROSTER)
    assert [c['episode_seed'] for c in pilot['cases']] == [7+i*50 for i in range(1, 7)]
    assert pilot['reference_manifest_sha256'] == original['sha256']


def test_roster_rejects_moving_an_unopened_test_task_to_development():
    original = deepcopy(reference())
    original['cases'][1]['partition'] = 'test'
    with pytest.raises(ContractError, match='existing development split'):
        prep.development_roster(seal(original), categories())


def test_roster_checks_balance():
    labels = {task: 'atomic_seen' for task in categories()}
    with pytest.raises(ContractError, match='two tasks per'):
        prep.development_roster(reference(), labels)
