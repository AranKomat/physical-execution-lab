"""Read-only runtime identity, without model or GPU initialization."""
import importlib.metadata,platform,subprocess,sys

def capture():
    out={'python':sys.version,'executable':sys.executable,'platform':platform.platform(),'packages':{}}
    for name in ('numpy','scipy','torch','jax','transformers','mujoco','robosuite','robocasa','isaacsim','isaaclab','httpx'):
        try:out['packages'][name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:out['packages'][name]=None
    try:
        p=subprocess.run(['nvidia-smi','--query-gpu=name,driver_version,memory.total','--format=csv,noheader'],
              capture_output=True,text=True,timeout=10,check=True);out['gpus']=p.stdout.strip().splitlines()
    except (OSError,subprocess.SubprocessError):out['gpus']=None
    return out

