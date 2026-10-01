# Physical Execution Lab — v0.4

**Frozen models, generic controls, sparse supervision.** This repository extends
K1 Execution Lab without replacing its original LIBERO/K1 runner.

> Build status: CPU-tested research implementation. **No native RoboDojo,
> RoboCasa365, GPU policy inference, or paid language-model evaluation has been
> run on the build host. No accuracy, leaderboard, or speed gain is claimed.**

## Start here

Read **[HANDOFF.md](HANDOFF.md)** for the self-contained implementation and
experiment plan, **[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)** for
qualification boundaries, and **[TAKEOVER.md](TAKEOVER.md)** for external Codex.

```bash
python -m pip install -e '.[test,multibench]'
python -m pytest -q
python run_bench.py doctor
python run_bench.py synthetic --output runs/my-multibench-check
# Open runs/my-multibench-check/report.html
```

The included `runs/multibench_cpu/` is a synthetic, authored contract fixture,
not a simulator evaluation. Its purpose is to exercise action acknowledgements,
review scheduling, budget handling, archival and full-denominator reporting.

## Experiments

| Track | Conditions | Scientific interpretation |
|---|---|---|
| RoboDojo direct | Sol dense vs Sol sparse local execution | No robot-policy training or external demonstrations; current-episode context allowed |
| RoboDojo hybrid | π0.5 / Xiaomi R1 / G0.5 / InternW0-Δ, each motor-only, every-chunk Sol, sparse Sol | Benchmark-trained motor policies; compare the same policy across harness conditions |
| RoboCasa365 | Xiaomi R1 only, every-chunk Sol, sparse Sol | Official XR1 preprocessing and action conversion; native qualification required |
| Original K1/LIBERO | Existing `run.py` experiments | Retained regression and future cross-environment transfer path |

The supervisor is `gpt-6.1-sol` through **Responses**. Standard (`default`) and
Flex are separate configurations; there is no implicit model/tier fallback.
No task recipe retrieval, extra target-task demonstrations, privileged object
poses, online weight updates, or newly generated task scripts are used.

## Architecture

```text
Actual sensor/robot observation
  → frozen motor policy (optional)
  → current-observation-bound proposal
  → local numerical/event monitors + periodic semantic review
  → accept / shorten / bounded local correction
  → one actual native action ACK
  → policy history update and compact execution receipt
```

A kinematic monitor is **not** a semantic success checker. Periodic GPT review
remains necessary even when motions look smooth. Robot-only FK is not contact
simulation. Gripper commands are not measured attachment.

## Important compatibility limits

* RoboDojo uses dual ARX-X5. FLUX DROID is not retargeted here.
* The donor RoboDojo RPC is RGB-only. K1 depth/geometry tools have **not** been
  silently enabled in this benchmark.
* Xiaomi RoboDojo EEF output currently uses a clearly labeled DLS controller
  variant. It is not an identical reproduction of its upstream native EE run.
* InternW0-Δ receives one observation acknowledgement per executed action.
  Interruptions discard pending actions and reset its source session; that
  temporal-context loss is an explicit cost of the current adapter.
* RoboCasa365 uses its own XR1 checkpoint, four observations sampled every two
  steps, 16 actions per query and 0.95 crop. `target50` is a task set, **not** the
  `target` kitchen split. The pinned XR1 reference uses `split=pretrain`.

## Files

`k1lab/multibench/` contains the new runner, scheduler, policy interfaces,
source-backed adapters, manifest/freeze tools and reporting. `configs/multibench/`
contains 17 experiment configurations and five provider templates.
`scripts/multibench/` contains launch planning, artifact binding, timing, plots
and qualification helpers. Upstream source pins are in `upstream.lock.json`.

Dependencies, simulator assets, model weights, licensed fonts and credentials
are not redistributed. Source bootstrap requires explicit network permission;
model and native execution require separate opt-ins. These contracts are research
controls, not certified hardware-safety mechanisms.
