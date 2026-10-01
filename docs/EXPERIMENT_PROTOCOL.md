# Experiment protocol: generic harness, not benchmark recipes

## 1. Claim to test

**With the same general model and sensor interface, does bounded multi-stage execution improve held-out task success and/or reduce model calls and total completion time?**

This is a hypothesis, not a measured result. A CPU kinematic demonstration cannot answer it. Do not choose a weak baseline just to make a large bar-chart gap.

## 2. Primary and diagnostic arms

| Arm | Original K1 tools | New executor | Candidate grasp macro | Frozen VLA |
|---|---|---|---|---|
| `k1_baseline` | Yes, unchanged registry | No | No | No |
| `k1_stepwise` | Yes | One pose/gripper segment per model call | No | No |
| `k1_sparse` | Yes | Up to six pose/gripper segments per call | Yes | No |
| `hybrid_stepwise` | Yes | Original K1 motion; short policy window (default 8 native steps) | No | Yes |
| `hybrid_sparse` | Yes | Sparse multi-stage execution; policy window up to 40 steps | Yes | Same policy |
| `policy_only` | Not called | No analytic task execution | No | Same policy on original task |

Primary: baseline versus sparse. This measures the complete extension (tool granularity, local execution behavior and receipts); it does not isolate batching alone. Stepwise versus sparse controls the new local engine more closely, but sparse also offers candidate-grasp composition. For a tighter batching-only ablation, disable the grasp macro in a separately named, frozen config/code revision on both sides before testing.

Hybrid is a separate experiment. Comparing no-VLA K1 to hybrid changes model availability. Do not call that “same models, better harness.” The policy-only arm can contextualize the hybrid stack, not isolate a single component.

## 3. Shared conditions

Same explicit model ID/revision where available; serving endpoint; reasoning effort; service tier; sampling behavior; input images; resolution; camera identities; calibration; controller; gripper; physical-step budgets; model-call limit; perception/tracker/grasp backend; within-episode history size; source freeze; state files; initial-state vectors and task instructions.

The underlying controller stays at 20 Hz. No speed-up by changing video playback or environment time. The extension's default Cartesian command caps are engineering starting points, not proven optimal values. Changing those caps requires documenting the condition, not claiming a pure reduction in model calls.

The native task-success flag stops every arm. Main configs reject actor-requested `completion_feedback`, so the model cannot repeatedly ask the hidden benchmark predicate whether a hypothetical task is done. No hidden target coordinates, object poses, instance masks, articulated axes or geometric thresholds are given to perception/planning. Robot-only kinematics and calibrated simulated sensors are allowed and declared.

## 4. Memory contract

Allowed: current instruction, generic tool documentation, current RGB-D, calibrated robot self-geometry, proprioception, current-episode observations, tracked references, model-authored progress, and receipts from the same attempt.

Disallowed in the primary result: benchmark-specific solution notes, exploration-memory downloads, prior successful trajectories for that task, resets to explore a scored task, tasks encoded in new API names, scene-name-specific thresholds, and memory carried between evaluation episodes.

A strong pretrained model may already contain related knowledge; a frozen VLA may have trained on related datasets. “No task-specific inference memory or new adaptation” is **not** “the model never saw any related task during pretraining.” Record checkpoint data provenance instead of claiming unknowable contamination freedom.

## 5. Holdout

`make-manifest` fingerprints BDDL files, official state archives and every selected vector. It groups a base task (suite family + task index) across Task/Swap variants, then splits whole groups into development and test. Different seeds of the same base task do not go on both sides.

Inspect the benchmark's task-index mapping when building the manifest. The split is conservative with respect to those task indices; it does not establish unseen object-family, mechanism-family, embodiment or real-world transfer.

Build the manifest before tuning. Use only development cases for debugging. `freeze.py` binds the concrete model ID (resolving `K1_MODEL`), runtime source, scripts, configs and manifest before test. The test runner refuses unfrozen or changed configurations. Freeze files are local integrity controls, not proof that a human never inspected test cases.

A stronger later experiment holds out task/mechanism families or a second environment. Do not claim that experiment from more LIBERO seeds alone.

## 6. Budgets and failure accounting

Official suite-step profiles: Spatial 220, Object 280, Goal 300, LIBERO-10 520. K1's standard ten-step reset settling is recorded as a shared excluded initialization convention. Native execution never renews the episode budget when a macro/VLA subgoal retries.

Every expected case stays in the denominator. Missing results and launch/transport/render failures count as failures, with separate labels. Do not cherry-pick successful seeds or rerun only failed test episodes. A hardware/host outage replacement must be predeclared, symmetric, and preserve original records.

Model-call and output-token caps are per episode, not a campaign-wide dollar ceiling. Use the development subset and provider-side total spend controls. Unknown API usage retains its output-token reservation. No implicit HTTP retry, model substitution or Flex-to-standard fallback. Input tokens are provider-reported when available, not estimated as a guaranteed dollar budget. Set a provider-side spend cap too.

## 7. Metrics

Report success rate, Wilson intervals, paired exclusive wins/losses, paired difference and base-task-cluster bootstrap intervals. Small pilot intervals will be wide; failure to find significance is not equivalence.

Report physical steps, success by fraction of step budget, all-attempt wall time and its measurement coverage, model requests, reported input/output tokens, usage completeness, policy requests, successful model/policy request latency, timeouts and failure categories. The report distinguishes setup-inclusive episode wall time from upstream agent-loop time.

Success-only median steps is conditional. Also show failure-penalized steps per expected episode (unsuccessful cases charged the declared horizon). This penalty is an accounting choice, **not measured motion**. Missing results otherwise make cost-per-success look artificially attractive. Do not judge success only among completed/successful runs.

Model wait, local control, perception, rendering and environment setup have different costs. Inclusive timers can overlap and must not be added. A slow renderer can dominate despite sparse model calls; a robot moving fewer native steps is a different gain from API latency reduction.

## 8. Recording and statistical caveats

Alternate condition order per case; use the same recording mode. Log exact requested and returned model IDs. A changing cloud alias cannot be made immutable by our code; record and report the provider limitation.

K1 returns fresh RGB-D frequently, and the extension currently observes every native step. No asynchronous state advances during model wait are assumed. There is no force-based insertion safety monitor, certified collision planner, or hardware controller here.

File/subprocess actors must be restricted to their request bundle. The process is trusted and not sandboxed; access to simulator source or other episode solutions would invalidate the clean comparison.

## 9. Interpretation

Acceptable result: success is unchanged within uncertainty, but model calls and end-to-end time decrease. Also acceptable: bundling reduces calls but harms success, revealing where reobservation is needed. Do not engineer every test failure into a task-specific skill.

The deliverable is evidence for a general execution interface, not a replication of K1's 18-case chart, RPent's memory-enabled 800 episodes, or DynaHarness's privileged-geometry contact library.
