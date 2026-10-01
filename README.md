# Physical Runtime Lab · paper-grounded revision 2

**A separate DynaHarness reproduction experiment, now grounded in the complete attached paper.**

Read **[START_HERE.md](START_HERE.md)** and **[HANDOFF.md](HANDOFF.md)**. The main implementation is `prl/dyna/`; the main CLI is `paper_run.py`. The old `run.py run` path is retained for legacy sensor-grounded experiments, not the new reproduction.

## What changed after reading the paper

- **Simulator-state geometry** for the LIBERO reproduction, exactly as the paper discloses in Appendix A. K1/RGB-D-only grounding becomes a separately measured extension.
- **Symbolic Qwen planning**, with numeric geometry resolved by the execution interface.
- **Analytic capability competence**, including staged pick/place, contact/lift verification, object-to-TCP transport, explicit corridor climb, support/cavity distinction, receptacle slots, and articulated mechanisms.
- **A2static / A2seq / A2ctrl** with distinct retry, planning and substitution semantics, instead of relabeling arbitrary nominal/dynamic controllers.
- **Official per-suite step budgets**, separate control/governor/safety clocks, completion latching, command affordability and leases.
- **Ten-action pi0.5 chunks** via an explicit RPent server wrapper, not its default five.
- **Cell-level paired admission plus broader regression**, not v1's per-seed preservation rule.

The PDF and a source-to-implementation fidelity matrix are included. Missing source details are listed explicitly: this is **not the authors' released code**, and no native success rate has yet been reproduced here.

## Run offline

```bash
python -m pip install -e '.[test]'
python -m pytest -q
python paper_run.py audit

python scripts/run_paper_matrix.py \
  --configs configs/dyna/fixture_bare.json configs/dyna/fixture_A2static.json \
            configs/dyna/fixture_A2seq.json configs/dyna/fixture_A2ctrl.json \
  --manifest manifests/synthetic_dev.json --output runs/first-check --execute
```

Open `runs/first-check/A2ctrl/report.html`. **This is a synthetic software fixture**, not a simulation benchmark. Its authored planner and kinematics cannot establish the paper's gains.

## External GPU continuation

Use Linux/Python 3.10–3.12 and the pinned RPent/RLinf/LIBERO stack. The handoff gives bootstrap commands, checkpoint fingerprinting, the ten-action policy server, Qwen connection settings, native smoke checks, state manifests and the evaluation sequence.

Start with one real analytic skill and a bare-policy episode under the correct budget. Then freeze a library and compare **the same library** under nominal and dynamic execution. Do not start by polishing reports or adding more framework layers.

| Resource | Purpose |
|---|---|
| [HANDOFF.md](HANDOFF.md) | Self-contained external-agent instructions, source links and commands |
| [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) | Implemented / tested / native-unqualified boundaries |
| [docs/PAPER_FIDELITY.md](docs/PAPER_FIDELITY.md) | Exact source statements versus reconstruction decisions |
| [docs/EXPERIMENTS.md](docs/EXPERIMENTS.md) | Ordered experiments and stopping rules |
| [configs/dyna/paper_spec.json](configs/dyna/paper_spec.json) | Machine-readable source specification |
| [references/2609.40306v1.pdf](references/2609.40306v1.pdf) | Complete paper supplied by the user |
| [TAKEOVER_PROMPT.md](TAKEOVER_PROMPT.md) | Initial prompt for external Codex |

Original MIT code; external dependencies retain their own licenses. No model weights or upstream repositories are bundled. No real-hardware backend is enabled.
