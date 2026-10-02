"""Export legal current observations to the released Tau proposal input contract.

No Tau model is downloaded or trained; this is a future planner-comparator seam.
Prediction tags are not copied into the motor prompt. No world-model goal images
are injected into an untrained vision slot.
"""
from pathlib import Path
from PIL import Image
from k1lab.errors import ContractError
from k1lab.util import atomic_json


def export_sample(obs, context, output, *, memory='(empty)', cameras=None):
    cameras = cameras or {'head': 'cam_high', 'left': 'cam_left_wrist', 'right': 'cam_right_wrist'}
    if set(cameras) != {'head', 'left', 'right'} or len(set(cameras.values())) != 3:
        raise ContractError('explicit distinct head/left/right camera mapping required')
    if any(k not in obs.rgb for k in cameras.values()):
        raise ContractError('missing camera; do not fabricate a second wrist view')
    root = Path(output)
    root.mkdir(parents=True, exist_ok=False)
    paths = {}
    for role in ('head', 'left', 'right'):
        path = root / f'{role}.png'
        Image.fromarray(obs.rgb[cameras[role]]).save(path)
        paths[role] = path.name
    row = {'id': f'{obs.episode}:{obs.step}', 'task_type': 'full_qa',
           'instruction': context.original_task, 'memory': memory or '(empty)', 'images': paths}
    import json
    (root / 'proposal.jsonl').write_text(json.dumps(row) + '\n')
    atomic_json(root / 'provenance.json', {'observation_sha256': obs.stamp,
                'native_step': obs.step, 'camera_mapping': cameras,
                'no_reference_answer': True, 'within_episode_memory_only': True})
    return row
