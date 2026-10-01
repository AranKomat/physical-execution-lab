#!/usr/bin/env python3
"""Plot measured outcomes only. Requires matplotlib; no reference-paper scores.

Each metric is a separate figure. Missing wall-time data is not plotted as zero.
"""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from k1lab.evaluation import compare
from k1lab.util import load_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', required=True)
    parser.add_argument('--left', default='k1_baseline')
    parser.add_argument('--right', default='k1_sparse')
    parser.add_argument('--partition', choices=['dev', 'test'], default='dev')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    root = Path(args.run)
    outcomes = load_json(root / 'outcomes.json')
    if (root / 'manifest.json').exists():
        cases = [case for case in load_json(root / 'manifest.json')['cases']
                 if case['partition'] == args.partition]
    else:
        cases = load_json(root / 'cases.json')
    result = compare(cases, outcomes[args.left], outcomes[args.right])
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=False)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    names = [args.left, args.right]
    summaries = [result['left'], result['right']]
    scope = ('SYNTHETIC SOFTWARE CHECK — NOT A ROBOTICS RESULT'
             if result['domain'] == 'synthetic' else 'Native reported outcomes: inspect frozen protocol')
    for metric, ylabel in [('success_rate', 'Success fraction'),
                            ('failure_penalized_steps_per_case', 'Failure-penalized steps per case'),
                            ('llm_calls', 'Total model requests'),
                            ('all_attempt_mean_wall_s', 'All-attempt mean wall time (seconds)')]:
        values = [summary[metric] for summary in summaries]
        if any(value is None for value in values):
            continue
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.bar(names, values)
        ax.set_ylabel(ylabel)
        ax.set_title(scope, fontsize=10)
        ax.tick_params(axis='x', labelrotation=10)
        fig.tight_layout()
        fig.savefig(out / f'{metric}.png', dpi=180)
        plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 5))
    for name, summary in zip(names, summaries):
        points = summary['success_by_budget_fraction']
        ax.plot([point['fraction'] for point in points],
                [point['rate'] for point in points], marker='o', label=name)
    ax.set(xlabel='Fraction of declared physical-step budget', ylabel='Success fraction',
           title=scope, ylim=(0, 1))
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / 'success_vs_step_budget.png', dpi=180)
    plt.close(fig)
    print(out)


if __name__ == '__main__':
    main()
