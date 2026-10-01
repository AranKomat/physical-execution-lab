#!/usr/bin/env python3
"""Plot measured aggregate results. Synthetic results stay explicitly labeled."""
import argparse,json
from pathlib import Path

def plot(root,out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    root=Path(root);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    rows=json.loads((root/'aggregates.json').read_text())
    results=json.loads((root/'outcomes.json').read_text())
    synthetic=any(r.get('evidence_kind')=='synthetic' for r in results)
    subtitle='SYNTHETIC SOFTWARE CHECK — NOT ROBOTICS PERFORMANCE' if synthetic else 'Run data; inspect protocol and missing-outcome coverage'
    for key,label,name in [('mean_episode_wall_s_available','Mean episode wall time (seconds)','success_vs_wall'),
                           ('review_calls','Total supervisor calls across reported episodes','success_vs_calls')]:
        fig,ax=plt.subplots(figsize=(11,7))
        for r in rows:
            x=r.get(key);y=r.get('success_rate_full_denominator')
            if x is None or y is None:continue
            ax.scatter([x],[100*y],label=r['condition'])
            ax.annotate(r['condition'],(x,100*y),xytext=(6,8),textcoords='offset points',fontsize=8)
        ax.set_xlabel(label);ax.set_ylabel('Success over scheduled cases (%)')
        ax.set_title('Physical Execution Lab\n'+subtitle);ax.set_ylim(-5,105)
        ax.grid(alpha=.3);fig.tight_layout();fig.savefig(out/(name+'.png'),dpi=180);plt.close(fig)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--report',required=True);p.add_argument('--output',required=True);a=p.parse_args();plot(a.report,a.output)
