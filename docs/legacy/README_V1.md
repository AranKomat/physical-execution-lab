# Physical Runtime Lab

**Independent RPent-backed, DynaHarness-inspired robotics runtime experiment.**
A new repository for quick LIBERO-Pro experiments, separate from the larger
BEHAVIOR-oriented physical-agent-harness project.

**Delivered status:** CPU contract tests and synthetic end-to-end runs work.
RPent native integration is source-inspected and mock-tested, not GPU-qualified.
No live model calls, no real LIBERO-Pro success rates, no exact DynaHarness
reproduction, and no hardware-safety claim are included.

Start with **[HANDOFF.md](HANDOFF.md)** and **[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)**.
The external coding agent should then read **[AGENTS.md](AGENTS.md)**.

## Run without a GPU or API

From this directory, Python 3.10+:

```bash
python run.py doctor
python run.py protocol-audit
python scripts/run_matrix.py \
  --configs configs/synthetic_frozen.json configs/synthetic_nominal.json configs/synthetic_dynamic.json \
  --manifest manifests/synthetic_dev.json --output runs/cpu-check
```

Open `runs/cpu-check/dynamic/report.html`. Everything in this report is labeled
**synthetic contract testing**, not robot performance. Both scripted harness
conditions solve the same two nominal fixtures and fail the blocked fixtures;
the monitor can shorten a stalled attempt without inventing task competence.

**125 CPU tests passed in the build environment.** Tests require pytest, NumPy and Pillow:

```bash
python -m pip install -e '.[test]'
python -m pytest -q
```

The core runtime and synthetic command runner themselves use only the standard
library. Geometry/native adapters import optional dependencies lazily. The local
CPU checks used Python 3.13.5; **native RPent requires a separate Python 3.10–3.12
venv**, preferably 3.11.

## Architecture

```text
planner: local VLM / API / external Codex file bridge
    ↓ bounded semantic proposal + evidence IDs
shared capability registry
    ↓ analytic / VLA / perception stages
nominal OR deterministic dynamic governor
    ↓ per-action checks; no bypass through VLA chunks
RPent native environment + frozen policy clients
    ↓ fresh observations, receipts, native terminal verdict
append-only evidence → paired evaluation → offline regression gate
```

## What to run next

1. Fetch pinned sources with `scripts/bootstrap.py --execute`; inspect the
   source-derived install plan and qualify RPent on a fresh simulation worker.
2. Create an initial-state catalog and hashed, disjoint dev/test manifests.
3. Run E0 frozen policy, then E1/E2 with identical capabilities and model settings.
4. Add K1 geometry tools as a separate E3 intervention.
5. Only after useful native results, extend contact skills or try offline revision.

Detailed commands, all source URLs, limitations, exact experiment distinctions,
and the continuation checklist are in [HANDOFF.md](HANDOFF.md).

## Scientific boundary

DynaHarness's project page attributes a major part of its large gain to its
analytic contact skill library. Our generic compositions are **not** that exact
library. The fixed-library governor ablation and the full-system improvement
must remain separate. `protocol-audit` intentionally reports unresolved parity.

No model weights, private episodes, original project state, or third-party source
archives are bundled. The upstream lock pins source downloads rather than
pretending the untested native Python dependency graph is fully locked.
