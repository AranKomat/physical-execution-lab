# K1 Execution Lab

**Generic physical tools, sparse model calls, current-episode evidence.**

This is an independent experimental extension of [Robo-Harness K1](https://github.com/Robo-Harness/k1), not an official K1 release. It tests whether a strong vision-language agent can do more work per decision without task-specific scripts, exploration recipes, privileged object state, or fine-tuning.

**Status:** runnable CPU software checks; source-inspected K1/LIBERO and RPent integrations; **no native robotics benchmark, live model request, GPU inference, or physical robot result has been run on the build host.** Synthetic completion numbers are not robotics results.

## Start here

- [HANDOFF.md](HANDOFF.md): self-contained architecture, commands, protocol, source links, and continuation sequence.
- [TAKEOVER.md](TAKEOVER.md): concise instructions for the external implementation/research agent.
- [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md): implemented versus tested versus still unqualified.
- [docs/EXPERIMENT_PROTOCOL.md](docs/EXPERIMENT_PROTOCOL.md): matched comparisons and holdout rules.
- [docs/SOURCE_AUDIT.md](docs/SOURCE_AUDIT.md): exact upstream interfaces and important corrections.

## Run without GPU or API credentials

Python 3.10+ with NumPy, SciPy, and HTTPX is enough for the core. Tests also use pytest and Pillow.

```bash
python run.py doctor
python -m pytest -q
python run.py synthetic --output runs/my-cpu-check
# Open runs/my-cpu-check/report.html locally.
```

The included `runs/cpu-example/` contains an authored unbundled/bundled kinematic check. It intentionally does **not** invent a success-rate improvement. No K1, VLM, VLA, MuJoCo, or trained policy is executed in that check.

## Architecture

```text
Strong VLM — K1's existing prompt, perception, history, tool loop
     |
     +-- Original generic K1 tools (unchanged)
     |
     +-- execute_motion_plan: short pose/gripper sequence
     +-- grasp_from_candidate: sensor candidate → bounded grasp/probe
     +-- vla_act: optional, explicitly compatible frozen policy
              |
        native local controller, one action at a time
              |
        actual pose residuals / event receipts / uncertain co-motion
              |
        return to the VLM at completion, ambiguity, stall or budget
```

A motion plan is a **new per-episode command**, not a saved solution for a benchmark task. No `open_task_7_drawer()` skill is added. A grasp candidate is a hypothesis, not an attachment or collision certificate.

K1 already provides native closed-loop movement, stale-frame checks, history, geometric tools, and native success stopping. We reuse those. The proposed change is larger, bounded execution units and a clean optional policy handoff—not claiming to invent IK or memory.

## Comparisons

| Configuration | Purpose |
|---|---|
| `k1_baseline` | Original K1 tool registry through the same environment and model transport. |
| `k1_stepwise` | New local engine but one segment per decision; no grasp macro. |
| `k1_sparse` | Short multi-stage execution plus generic candidate grasp. |
| `hybrid_stepwise` | K1 with a compatible frozen policy available in short windows. |
| `hybrid_sparse` | Same policy plus sparse execution and longer bounded windows. |
| `policy_only` | The configured frozen policy on the original task, without a VLM or task memory. |

**Primary:** `k1_baseline` versus `k1_sparse`, without any VLA. **Diagnostic:** `k1_stepwise` versus `k1_sparse`. **Separate hybrid experiment:** same checkpoint on both sides. A comparison that adds a policy is not a same-model harness-only result.

## Native path

```bash
python scripts/bootstrap.py --group core --allow-network
python scripts/source_probe.py --k1 external/k1
```

Prepare the pinned K1-compatible LIBERO environment and benchmark data, then follow [HANDOFF.md](HANDOFF.md). Upstream code, datasets, segmentation weights, and policy weights are not bundled. Downloads and model calls require explicit flags.

**FLUX is not silently substituted for a LIBERO policy.** Its released DROID interface uses three cameras and absolute joint targets; this LIBERO adapter uses two cameras and Cartesian OSC. `scripts/flux_offline_probe.py` supports recorded DROID observations only. The optional native bridge currently targets RPent's π0.5 interface and still requires calibration/rollout qualification.

## License and scope

Original code: MIT. Upstream projects retain their own licenses. This is a simulator research tool, **not a safety-rated industrial or real-robot controller**. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
