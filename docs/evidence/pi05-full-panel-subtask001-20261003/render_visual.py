"""Render retained legal sensor frames, not generated or future simulator views."""
import json
from pathlib import Path
import subprocess
import sys
import textwrap

import numpy as np
from PIL import Image, ImageDraw, ImageFont

root = Path(sys.argv[1])
out = Path(sys.argv[2])
out.mkdir(exist_ok=False)
font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 18)
small = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 15)
index = []
for group in sorted(root.glob('group[0-9]')):
    episodes = {}
    for p in sorted(group.glob('episodes/*/controller/result.json')):
        idx = int(p.parents[1].name)
        result = json.loads(p.read_text())
        events = [json.loads(s) for s in (p.parent / 'events.jsonl').read_text().splitlines()]
        proposals = [e['data'] for e in events if e['event'] == 'policy_proposal']
        episodes[idx] = dict(result=result, proposals=proposals, frames={}, controller=p.parent)
    for path in sorted(group.glob('request-*.npz')):
        with np.load(path, allow_pickle=False) as data:
            for row, idx in enumerate(data['env_ids']):
                episodes[int(idx)]['frames'][int(data['steps'][row])] = {
                    k: Image.fromarray(data[k][row]).copy()
                    for k in ('cam_high', 'cam_left_wrist', 'cam_right_wrist')}
    for idx, episode in episodes.items():
        task = episode['result']['task']
        epochs = []
        for p in episode['proposals']:
            context = p['diagnostics']['semantic']['context']
            if not epochs or context['epoch'] != epochs[-1]['epoch']:
                epochs.append(dict(epoch=context['epoch'], start=p['step'],
                    subtask=context['subtask'] or '[Original task only]'))
        initial_only = not episode['frames']
        if initial_only:
            assert episode['result']['native_steps'] == 0 and not episode['proposals']
            with np.load(episode['controller'] / 'observations/000000/sensors.npz', allow_pickle=False) as data:
                episode['frames'][0] = {k: Image.fromarray(data[k]).copy()
                    for k in ('cam_high', 'cam_left_wrist', 'cam_right_wrist')}
            epochs = [dict(epoch=0, start=0,
                subtask='[No active subtask; planner stopped before motor prediction]')]
        steps = sorted(episode['frames'])
        def tile(step):
            frame = episode['frames'][step]
            canvas = Image.new('RGB', (480, 266), 'white')
            canvas.paste(frame['cam_high'].resize((320, 240)), (0, 26))
            canvas.paste(frame['cam_left_wrist'].resize((160, 120)), (320, 26))
            canvas.paste(frame['cam_right_wrist'].resize((160, 120)), (320, 146))
            ImageDraw.Draw(canvas).text((5, 4), f'step {step} | head + left/right wrist', font=small, fill='black')
            return canvas
        sheet = Image.new('RGB', (1440, 55 + len(epochs) * 340), 'white')
        draw = ImageDraw.Draw(sheet)
        source_label = 'initial actor view; zero actions' if initial_only else 'retained policy inputs'
        draw.text((8, 8), task + ' | ' + source_label + '; not continuous video', font=font, fill='black')
        for n, epoch in enumerate(epochs):
            end = epochs[n+1]['start'] if n+1 < len(epochs) else steps[-1]
            desired = [epoch['start'], min(end, epoch['start'] + 45), end]
            selected = [min(steps, key=lambda s: abs(s-t)) for t in desired]
            y = 55 + n * 340
            label = f'epoch {epoch["epoch"]}, goal starts at {epoch["start"]}: {epoch["subtask"]}'
            draw.multiline_text((8, y), '\n'.join(textwrap.wrap(label, 140)), font=font, fill='black', spacing=2)
            for col, step in enumerate(selected):
                sheet.paste(tile(step), (480*col, y+68))
            epoch['inspected_sheet_steps'] = selected
        sheet_path = out / (task + '.jpg')
        sheet.save(sheet_path, quality=92)
        video_path = out / (task + '.mp4')
        cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-f', 'rawvideo',
               '-pixel_format', 'rgb24', '-video_size', '960x330', '-framerate', '5/3',
               '-i', '-', '-an', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-y', str(video_path)]
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        try:
            for step in steps:
                epoch = max((e for e in epochs if e['start'] <= step), key=lambda e:e['start'])
                canvas = Image.new('RGB', (960, 330), 'white')
                d = ImageDraw.Draw(canvas)
                d.multiline_text((8, 5), '\n'.join(textwrap.wrap(
                    f'{task} | step {step} | {epoch["subtask"]}', 105)), font=font, fill='black')
                frame = episode['frames'][step]
                for col, key in enumerate(('cam_high', 'cam_left_wrist', 'cam_right_wrist')):
                    canvas.paste(frame[key].resize((320, 240)), (320*col, 90))
                process.stdin.write(canvas.tobytes())
        finally:
            process.stdin.close()
        if process.wait() != 0:
            raise RuntimeError('video encoding failed')
        index.append(dict(task=task, group=group.name, env_idx=idx,
            native_result=episode['result']['status'], epochs=epochs,
            sheet=str(sheet_path), video=str(video_path), sampled_steps=steps,
            sampling=('initial actor sensor snapshot only; zero motor actions' if initial_only
                else 'one retained policy input per native H15 prefix; no interpolation'),
            final_native_steps=episode['result']['native_steps']))
(out / 'index.json').write_text(json.dumps(index, indent=2) + '\n')
print('Rendered', len(index), 'task sheets/videos from retained legal observations.')
