"""Explicit source cadence for the two qualified full-panel motor paths."""
from k1lab.errors import ContractError


def motor_contract(policy):
    if policy == 'pi05':
        return dict(provider='configs/local/pi05-exact-bound-001/provider.json',
                    python='.venv-pi05/bin/python', policy_name='Pi_05',
                    mode='vmap_source_singleton_sampling', returned=50, execute=15,
                    underlying_horizon=50, name='pi05_robodojo')
    if policy == 'g05':
        return dict(provider='configs/local/g05-fused-b10-bound-20261003/provider.json',
                    python='.venv-g05-fla/bin/python', policy_name='G05',
                    mode='g05_source_fused_sampling', returned=16, execute=16,
                    underlying_horizon=32, name='g05_robodojo_fm')
    raise ContractError('unqualified full-panel motor policy')


def validate_identity(identity, policy):
    contract = motor_contract(policy)
    if (identity.name != contract['name'] or identity.action_space != 'x5_joint14'
            or identity.execute_steps != contract['execute']
            or identity.prediction_horizon != contract['underlying_horizon']
            or identity.native_hz != 25 or identity.stateful != (policy == 'g05')):
        raise ContractError('full-panel source motor identity/cadence changed')
    return contract
