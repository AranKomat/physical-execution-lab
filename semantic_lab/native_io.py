"""Small atomic file protocol used by separately owned simulator/model processes."""
import json
import subprocess
import time


def write_json(path, value):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, indent=2) + '\n')
    tmp.replace(path)


def wait_file(path, child=None, timeout=900):
    start = time.monotonic()
    while not path.exists():
        error = path.parent / 'worker-error.json'
        if error.exists():
            raise RuntimeError(error.read_text())
        if child is not None and child.poll() is not None:
            raise RuntimeError('policy worker exited; no retry')
        if time.monotonic() - start > timeout:
            raise TimeoutError(str(path))
        time.sleep(.05)


def memory():
    return subprocess.check_output(['nvidia-smi', '--query-gpu=index,memory.used,memory.free',
                                   '--format=csv,noheader,nounits'], text=True)
