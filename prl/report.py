from __future__ import annotations
import html
import json
from pathlib import Path


def write_report(path,summary):
    e=lambda x:html.escape(str(x))
    rows=''.join(f"<tr><td>{e(r['case']['case_id'])}</td><td>{e(r['status'])}</td>"
        f"<td>{e(r['native_success'])}</td><td>{e(r['reason'])}</td>"
        f"<td>{r['native_steps']}</td><td>{r['planner_calls']}</td><td>{r['vla_calls']}</td>"
        f"<td>{r['wall_s']:.2f}</td></tr>" for r in summary['episodes'])
    title='Physical Runtime Lab — '+summary['benchmark']
    doc=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>{e(title)}</title><style>
body{{font:15px system-ui,sans-serif;background:#0e1625;color:#e9edf5;max-width:1260px;margin:40px auto;padding:0 24px}}
h1{{font-size:30px}}h2{{font-size:20px}}.warning{{border:1px solid #d4ad60;background:#332c1d;padding:18px;line-height:1.6}}
.metrics{{display:flex;gap:16px;flex-wrap:wrap;margin:24px 0}}.metric{{background:#192638;padding:18px;min-width:125px}}.metric b{{font-size:27px;display:block}}
table{{width:100%;border-collapse:collapse;background:#172235}}th,td{{padding:10px;text-align:left;border-bottom:1px solid #354257}}td:first-child{{font-family:monospace}}.scroll{{overflow:auto}}
pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:#172235;padding:20px}}small{{color:#bac6da}}a{{color:#9cccff}}
</style><h1>Physical Runtime Lab</h1><p>Frozen weights · bounded capabilities · measured execution · independent native verdict</p>
<div class="warning"><b>{e(summary['claim'])}</b><br>Mode: {e(summary['mode'])}. Missing episodes and infrastructure errors remain visible. This page contains no paper-reference numbers presented as measurements.</div>
<div class="metrics">{''.join(f'<div class="metric"><small>{e(k)}</small><b>{e(summary[k])}</b></div>' for k in ['planned','completed','successes','missing','infrastructure_or_protocol_errors'])}</div>
<h2>Episode ledger</h2><div class="scroll"><table><thead><tr><th>Case</th><th>Run status</th><th>Native success</th><th>Termination reason</th><th>Steps</th><th>Planner calls</th><th>Policy calls</th><th>Wall s</th></tr></thead><tbody>{rows}</tbody></table></div>
<h2>Interpretation</h2><p>Capability execution is not task completion. Gripper width is not attachment. Tracking error is not contact force. Synthetic fixtures establish software behavior only.</p>
<p>Paired comparisons should hold initial-state content, weights, sensors, capabilities, planner, budgets and native scoring fixed. Report generalization only on frozen held-out manifests.</p>
<details><summary>Summary JSON</summary><pre>{e(json.dumps({k:v for k,v in summary.items() if k!='episodes'},indent=2))}</pre></details>
</html>'''
    Path(path).write_text(doc)
