from __future__ import annotations
import html
import json
from pathlib import Path
from .evaluation import summarize,full_rows


def render(path,cases,conditions,domain):
    out=Path(path);out.parent.mkdir(parents=True,exist_ok=True)
    blocks=[];summaries={}
    for name,rows in conditions.items():
        s=summarize(full_rows(cases,rows));summaries[name]=s
        width=round((s['success_rate'] or 0)*420)
        blocks.append(f'<section><h2>{html.escape(name)}</h2><p>{s["successes"]}/{s["episodes"]} completed</p>'
            f'<svg viewBox="0 0 450 42" role="img" aria-label="Completion fraction"><rect x="0" y="4" width="420" height="24" fill="#e4e8ef"/>'
            f'<rect x="0" y="4" width="{width}" height="24" fill="#435875"/></svg>'
            '<table>'+''.join(f'<tr><td>{html.escape(k)}</td><td>{html.escape(str(v))}</td></tr>' for k,v in s.items() if k!='success_by_budget_fraction')+'</table></section>')
    banner='SYNTHETIC SOFTWARE CHECK — NOT A ROBOTICS BENCHMARK' if domain=='synthetic' else 'NATIVE RUN — REVIEW PROTOCOL AND HOLDOUT BEFORE INTERPRETING'
    source=html.escape(json.dumps(summaries,indent=2))
    doc=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>K1 Execution Lab — evidence report</title><style>body{{font:16px system-ui;max-width:1200px;margin:36px auto;padding:0 24px;color:#172234;background:#f6f8fb}}
header,section{{background:white;padding:24px;border:1px solid #dce1ea;border-radius:12px;margin:16px 0}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:16px}}
strong{{display:block;padding:14px;background:#fff2c7}}table{{width:100%;font-size:13px;border-collapse:collapse}}td{{border-bottom:1px solid #e4e8ef;padding:8px;word-break:break-word}}pre{{white-space:pre-wrap}}h1{{margin-bottom:8px}}</style>
<header><strong>{banner}</strong><h1>K1 Execution Lab</h1><p>Generic execution, current-episode evidence, no task-solution memory.</p>
<p>Completion alone is insufficient. Compare full-denominator success, physical steps, model requests, wall time and frozen model identities. No missing episode is removed.</p></header>
<div class="grid">{''.join(blocks)}</div><details><summary>Machine-readable metric values</summary><pre>{source}</pre></details>
<p>Success-only durations are conditional diagnostics. Failure-penalized steps are a declared accounting metric, not measured motion. Model wait and simulator/render time must be distinguished.</p></html>'''
    out.write_text(doc);return out
