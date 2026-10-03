"""Contact sheets for closer visual review of retained legal observations."""
import json
from pathlib import Path
import textwrap

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'runs/pi05-semantic001-visual-audit001'
index = json.loads((OUT / 'index.json').read_text())
font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 15)
windows = {
    'build_tower': [(300, 615)],
    'imitate_sorting_sequence': [(450, 615)],
    'make_kong': [(90, 300)],
    'classify_objects': [(210, 330), (510, 705)],
    'organize_table': [(0, 315)],
    'pack_objects_into_box': [(840, 1020), (1140, 1290)],
    'put_bottles_into_dustbin': [(0, 90)],
    'classify_objects_by_language': [(630, 810), (930, 1095)],
}
for entry in index:
    task = entry['task']
    if task not in windows:
        continue
    frames = {}
    for path in sorted((ROOT / 'runs/pi05-full-panel-semantic001' / entry['group']).glob('request-*.npz')):
        with np.load(path, allow_pickle=False) as data:
            if entry['env_idx'] not in data['env_ids']:
                continue
            row = data['env_ids'].tolist().index(entry['env_idx'])
            step = int(data['steps'][row])
            if any(start <= step <= end for start, end in windows[task]):
                frames[step] = {key: Image.fromarray(data[key][row]).copy()
                    for key in ('cam_high', 'cam_left_wrist', 'cam_right_wrist')}
    for part in range(0, len(frames), 9):
        selected = sorted(frames)[part:part+9]
        sheet = Image.new('RGB', (1440, 30 + ((len(selected)+2)//3)*340), 'white')
        draw = ImageDraw.Draw(sheet)
        draw.text((8, 5), task + ' | each retained H15 input; no interpolation', font=font, fill='black')
        for cell, step in enumerate(selected):
            x, y = (cell % 3)*480, 30+(cell//3)*340
            epoch = max((e for e in entry['epochs'] if e['start'] <= step), key=lambda e:e['start'])
            label = f'step {step}: {epoch["subtask"]}'
            draw.multiline_text((x+4,y+3), '\n'.join(textwrap.wrap(label, 58)), font=font, fill='black')
            sheet.paste(frames[step]['cam_high'].resize((320,240)), (x,y+95))
            sheet.paste(frames[step]['cam_left_wrist'].resize((160,120)), (x+320,y+95))
            sheet.paste(frames[step]['cam_right_wrist'].resize((160,120)), (x+320,y+215))
        sheet.save(OUT / f'{task}-dense-{part//9}.jpg', quality=94)
    print(task, len(frames), 'frames')
