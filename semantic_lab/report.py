"""Full-denominator paired summaries. Synthetic data remains explicitly synthetic."""
from collections import Counter
from pathlib import Path
import html
import numpy as np
from k1lab.errors import ContractError
from k1lab.util import atomic_json, load_json


def aggregate(cases, results, conditions):
    ids = {c['case_id'] for c in cases}
    if len(ids) != len(cases):
        raise ContractError('duplicate manifest cases')
    rows = {}
    for r in results:
        key = (r['condition'], r['case_id'])
        if r['case_id'] not in ids or r['condition'] not in conditions:
            continue
        if key in rows:
            raise ContractError('duplicate attempts; choose a preregistered attempt explicitly')
        rows[key] = r
    summary = {}
    for cond in conditions:
        rr = [rows[(cond, c['case_id'])] for c in cases if (cond, c['case_id']) in rows]
        successful = sum(r['success'] for r in rr)
        scores = [r['native_score'] for r in rr if r['native_score'] is not None]
        summary[cond] = {'scheduled': len(cases), 'observed': len(rr), 'missing': len(cases) - len(rr),
            'successes': successful, 'success_rate_full_denominator': successful / len(cases) if cases else None,
            'statuses': dict(Counter(r['status'] for r in rr)),
            'partial_score_mean_observed': float(np.mean(scores)) if scores else None,
            'partial_score_coverage': len(scores),
            'total_native_steps_observed': sum(r['native_steps'] for r in rr),
            'wall_seconds_observed': sum(r['elapsed_s'] for r in rr),
            'semantic_calls_observed': sum(r['metrics']['semantic_calls'] for r in rr),
            'gpt_induced_resamples': sum(r['metrics']['gpt_induced_motor_resamples'] for r in rr),
            'evidence_kinds': sorted(set(r['evidence_kind'] for r in rr))}
    return summary, rows


def paired(cases, rows, baseline, candidate, seed=7, draws=2000):
    differences = {}
    for c in cases:
        a, b = rows.get((baseline, c['case_id'])), rows.get((candidate, c['case_id']))
        if a and b:
            for k in ('case_sha256', 'policy_identity', 'environment_contract_sha256'):
                if a.get(k) != b.get(k):
                    raise ContractError('paired comparison differs on ' + k)
            if a.get('evidence_kind') != b.get('evidence_kind'):
                raise ContractError('cannot pool native and synthetic evidence')
        group = c.get('task_group', c['task'])
        differences.setdefault(group, []).append(float(bool(b and b['success'])) - float(bool(a and a['success'])))
    means = np.array([np.mean(v) for v in differences.values()])
    if not len(means):
        raise ContractError('empty paired comparison')
    rng = np.random.default_rng(seed)
    interval = None
    if len(means) > 1:
        samples = rng.choice(means, size=(draws, len(means)), replace=True).mean(axis=1)
        interval = np.quantile(samples, [.025, .975]).tolist()
    return {'task_weighted_success_delta': float(means.mean()), 'task_cluster_bootstrap_95': interval,
            'task_groups': len(means), 'missing_counts_as_not_successful': True,
            'caution': 'small development panels do not establish broad generalization; no automatic claim of significance'}


def write_report(cases, results, output, conditions, baseline=None, candidate=None):
    root = Path(output)
    root.mkdir(parents=True, exist_ok=True)
    summary, indexed = aggregate(cases, results, conditions)
    document = {'conditions': summary}
    if baseline and candidate:
        document['paired'] = paired(cases, indexed, baseline, candidate)
    atomic_json(root / 'summary.json', document)
    tr = []
    for c, d in summary.items():
        tr.append(f'<tr><td>{html.escape(c)}</td><td>{d["successes"]}/{d["scheduled"]}</td>'
                  f'<td>{d["missing"]}</td><td>{d["semantic_calls_observed"]}</td><td>{d["total_native_steps_observed"]}</td>'
                  f'<td>{d["wall_seconds_observed"]:.3f}</td><td>{html.escape(str(d["statuses"]))}</td></tr>')
    synthetic = all(r.get('evidence_kind') == 'synthetic' for r in results)
    label = 'SYNTHETIC SOFTWARE TEST — NOT A ROBOT BENCHMARK' if synthetic else 'NATIVE EXPERIMENT — CHECK COVERAGE AND QUALIFICATION'
    page = f'''<!doctype html><meta charset="utf-8"><title>Semantic Execution Lab</title>
<style>body{{font:16px system-ui;max-width:1150px;margin:40px auto;padding:20px}}table{{border-collapse:collapse;width:100%}}td,th{{padding:12px;text-align:left;border-bottom:1px solid #ddd}}small{{line-height:1.6}}</style>
<h1>Semantic hierarchy · execution audit</h1><h2>{label}</h2>
<p>Language changes at native motor boundaries. No shortening or per-task executable skills.</p>
<table><tr><th>Condition</th><th>Success</th><th>Missing</th><th>Semantic calls</th><th>Native steps</th><th>Observed wall seconds</th><th>Statuses</th></tr>{''.join(tr)}</table>
<p>CPU elapsed time and synthetic successes are not robotics latency or accuracy evidence. Native results must retain failures, budget stops and contract errors.</p>'''
    (root / 'report.html').write_text(page)
    return document
