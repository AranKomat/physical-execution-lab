"""Explicit, lazy construction of approved simulator/model adapters."""
from k1lab.errors import Unavailable,ContractError


def policy(config,allow_policy=False):
    if not allow_policy:raise Unavailable('model loading/network requires --allow-policy')
    backend=config['backend']
    if backend=='remote':
        from .transport import RemotePolicy
        return RemotePolicy(config,allow_policy=True)
    if backend=='xpolicylab':
        from .adapters.xpolicylab import XPolicyModel
        return XPolicyModel(config)
    if backend=='pi05':
        from .adapters.pi05 import Pi05Policy
        return Pi05Policy(config)
    if backend=='xiaomi_robocasa':
        from .adapters.robocasa import XiaomiRoboCasaPolicy
        return XiaomiRoboCasaPolicy(config)
    raise ContractError('unknown policy backend')


def environment(config,allow_native=False):
    if not allow_native:raise Unavailable('native simulation requires --allow-native')
    if config['backend']=='robodojo_rpc':
        from .adapters.robodojo import RoboDojoRPC
        return RoboDojoRPC(config)
    if config['backend']=='robocasa':
        from .adapters.robocasa import RoboCasaEnv
        return RoboCasaEnv(config)
    raise ContractError('unsupported simulator adapter')
