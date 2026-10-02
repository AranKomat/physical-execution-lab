import pytest
from semantic_lab.report import summarize_wave_results
from k1lab.errors import ContractError


def result(status, terminal, calls):
    return {'status': status, 'native_terminal_observed': terminal,
            'metrics': {'semantic_calls': calls}}


def test_wave_keeps_paid_calls_and_contract_error_row():
    summary = summarize_wave_results({
        0: result('native_completed', True, 7),
        1: result('infrastructure_or_contract_error', False, 7)})
    assert summary['status'] == 'incomplete_semantic_wave'
    assert summary['paid_calls'] == 14
    assert summary['controller_status_counts'] == {'native_completed': 1, 'infrastructure_or_contract_error': 1}
    assert not summary['all_rows_native_terminal']
    assert summary['contains_controller_or_contract_error']


def test_wave_preserves_abstention_and_native_horizon_completion():
    summary = summarize_wave_results({0: result('native_completed', True, 11),
                                      1: result('planner_stop_incomplete', False, 8)})
    assert summary['paid_calls'] == 19
    assert summary['status'] == 'incomplete_semantic_wave'
    assert not summary['contains_controller_or_contract_error']
    assert summarize_wave_results({0: result('native_completed', True, 11)})['status'] == 'native_terminal_semantic_wave'


def test_wave_rejects_missing_rows_and_bad_call_counts():
    with pytest.raises(ContractError, match='empty semantic wave'):
        summarize_wave_results({})
    with pytest.raises(ContractError, match='invalid semantic call count'):
        summarize_wave_results({0: result('native_completed', True, True)})
