"""Offline report. Scores must come from event-audited local measurements."""
from html import escape
import json

def write_report(path,summary):
    rows=''.join(f'<tr><td>{escape(k)}</td><td>{v}</td></tr>' for k,v in summary['totals'].items())
    by=''.join(f'<tr><td>{escape(k)}</td><td>{v["successes"]}/{v["planned"]}</td><td>{100*v["full_denominator_rate"]:.1f}%</td></tr>' for k,v in summary['by_suite'].items())
    source='SYNTHETIC SOFTWARE TEST' if summary['source']=='synthetic' else 'LOCAL NATIVE SIMULATION'
    path.write_text(f'''<!doctype html><meta charset="utf-8"><title>Physical Runtime Lab — PDF track</title>
<style>body{{font:16px/1.6 system-ui;max-width:1000px;margin:50px auto;padding:0 25px;background:#f5f7fa;color:#13243a}}h1{{font-size:38px;line-height:1.15}}.banner{{padding:18px;background:#fff1cc;border-left:5px solid #a46800}}section{{background:white;padding:25px;margin:22px 0}}table{{border-collapse:collapse;width:100%}}td,th{{text-align:left;border-bottom:1px solid #dce1e8;padding:8px}}small{{color:#455c73}}</style>
<small>{source} / PAPER-GROUNDED V2</small><h1>Physical Runtime Lab</h1><p class="banner">{escape(summary['claim'])}</p>
<section><h2>Run: {escape(summary['arm'])}</h2><p>Planned {summary['planned']} · Started {summary['started']} · Missing {summary['missing']} · Errors {summary['errors']}</p><p>Full-denominator success: <b>{summary['successes']}/{summary['planned']}</b>. This is not a DynaHarness paper result.</p><table><tr><th>Suite</th><th>Count</th><th>Rate</th></tr>{by}</table></section>
<section><h2>Execution accounting</h2><table>{rows}</table></section><section><h2>Interpretation</h2><p>The fixture checks symbolic planning, geometric skills, the retry/replanning distinction, budgets, and completion. It cannot establish real grasping, contact physics, model quality, or comparable LIBERO-Pro gains.</p><p>PDF: arXiv:2609.40306v1. Source paper, local reconstruction assumptions, and native qualification gaps are separated in the handoff and fidelity matrix.</p></section>''')
