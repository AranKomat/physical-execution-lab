# Codex takeover — Physical Execution Lab v0.4

2026-10-02 update: one G0.5 motor-only native development case succeeded; other
policy qualifications and all paid supervision comparisons remain pending. Read
`docs/EXPERIMENT_PROGRESS.md` and `docs/NATIVE_PILOT_20261002.md` before repeating
bring-up work. This is not a completed benchmark comparison.

You are continuing a CPU-built research repo, not consuming a completed robotics
result. Read `HANDOFF.md`, `IMPLEMENTATION_STATUS.md`, and `AGENTS.md` first.

**Goal:** a clean, measurable improvement from sparse physical-agent supervision.
No task-specific solution memory, no benchmark-script generation, no new weight
training in this phase. Current-episode memory is allowed. General robot controls,
robot-only FK and classical local controllers are allowed.

**Models/benchmarks:**
- Supervisor: `gpt-6.1-sol`, Responses API. **Flex is the active default**;
  Standard/default remains an explicit latency comparison. No automatic
  downgrade/fallback.
- RoboDojo: π0.5, Xiaomi R1, G0.5, InternW0-Δ. First measure policy-only latency
  and native competence, then retain useful speed/quality candidates. For each:
  motor-only, every-chunk review, sparse review. Also direct dense vs direct sparse
  with no motor model or extra demonstrations.
- RoboCasa365: official Xiaomi RoboCasa365 checkpoint, alone vs sparse Sol;
  every-chunk control available. Preserve source preprocessing and task seed rules.
- Keep original `run.py` K1/LIBERO runner. Do not rewrite everything around it.

**Critical source facts:**
- RoboDojo donor exports RGB and robot measurements, not calibrated depth.
- X5 has 6 joints + opening per arm. Do not inject FLUX DROID/Panda geometry.
- InternW0-Δ requires every actual action ACK. Reset on intervention currently
  loses temporal memory; measure that, do not invent queued acknowledgements.
- Xiaomi RoboDojo EEF→DLS is a controller variant; qualify versus the original
  XPolicyLab path before comparing published scores.
- Source FK requires H50; our adapter pads repeated final joints ONLY for pure FK
  evaluation and discards those outputs. No extra action is executed.
- RoboCasa365 `target50` does not mean target kitchen split. Pinned XR1 reference:
  pretrain kitchens, 50 trials/task, seed7 + global index, history4/interval2,
  crop.95, prefix16. New kitchen split is a separate experiment.

**Execution order:**
1. `python -m pip install -e '.[test,multibench]'`; `python -m pytest -q`.
2. `python run_bench.py synthetic --output runs/check`; no result claims.
3. Bootstrap source pins; acquire legally permitted assets/weights yourself.
4. Capture/reset/render one development case, no GPT. Then one bounded local
   action and a real policy chunk with per-tick receipts. Verify nonvacuous native
   task completion, normalizers, gripper conventions, timing and camera inputs.
5. Bind actual artifacts and provider settings with `bind_policy.py`. Measure
   warmed policy latency and VRAM plus full-episode performance before ranking.
6. Run development pilots. Attach actual native evidence in qualification records.
7. Freeze source/configs/cases. Run matched held-out comparisons and report every
   scheduled case, failures, input/cached/output/reasoning tokens, native time,
   simulator wall time, policy time, GPT time and call counts.

**Do not say:** “we reproduced the headline” / “we beat Xiaomi” / “5× faster”
unless actual matched native evidence supports it. The build host ran no GPU or
paid model experiment. Do not turn missing failures into zeros in partial-score
means or silently select best retries. Reference task-demonstration streams
intrinsic to imitation tasks are allowed, but must be labeled separately from
external few-shot examples.

Deliver a native pilot report with exact revisions/configuration, before expanding
scope. The main immediate risk is native adapter fidelity, not missing abstractions.
