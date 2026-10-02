"""Bind reference case metadata without importing public outcomes into control."""
from copy import deepcopy
from k1lab.errors import ContractError
from k1lab.multibench.manifest import check


def bind_reference_wave(manifest, case_ids, runtime_task):
    check(manifest)
    if not 1 <= len(case_ids) <= 5 or len(set(case_ids)) != len(case_ids):
        raise ContractError('reference wave needs one to five unique case IDs')
    by_id = {case['case_id']: case for case in manifest['cases']}
    if any(case_id not in by_id for case_id in case_ids):
        raise ContractError('case missing from reference manifest')
    rows = [deepcopy(by_id[case_id]) for case_id in case_ids]
    for row in rows:
        if row['benchmark'] != 'robodojo' or row['runtime_task'] != runtime_task:
            raise ContractError('reference wave mixes benchmarks or runtime task variants')
        if row['eval_seed'] != 0 or not row.get('layout_sha256') or not row.get('layout_path'):
            raise ContractError('reference wave requires bound group0 layouts')
        if type(row['horizon']) is not int or row['horizon'] <= 0 or row['native_hz'] != 25:
            raise ContractError('reference wave needs native horizon and25Hz')
    if len({row['layout_id'] for row in rows}) != len(rows):
        raise ContractError('reference wave repeats a layout')
    if len({(row['task_group'], row['partition'], row['horizon']) for row in rows}) != 1:
        raise ContractError('reference wave mixes task groups, partitions or horizons')
    return rows
