# K1 Execution Lab — self-contained implementation and research handoff

**Date:** 2026-10-01  
**Version:** 0.3.0  
**Repository directory:** `k1-execution-lab/`  
**Working claim:** Generic physical tools, sparse model decisions, no task-solution memory.  
**Evidence boundary:** The delivered software was CPU-tested. No native LIBERO episode, live VLM request, GPU policy inference or physical robot action was performed on the build host.

## 1. Direction and why this is a separate repository

The founder is exploring the execution/harness layer for physical AI, with a background in model training and agent systems. The immediate goal is a credible, measurable robotics result, not a factory-animation demo or a fully chosen industrial vertical. Manufacturing/deployment remains a possible application, but should not determine benchmark-specific control code before customer evidence exists.

The discussion moved through DynaHarness reproduction, RPent/Harness VLA, and K1. The current choice is **K1's general sensor/tool interface, extended with sparse bounded execution**. This supersedes the earlier `physical_runtime_lab_paper_v2` package for the immediate research objective. It does not delete or merge that work, the BEHAVIOR-oriented harness, or the closed EmbodiedSWE GPU-insertion branch.

The desired boundary resembles a general software agent: tool documentation can describe a robot, camera or gripper, but the system should not receive a previously solved recipe for the exact evaluation task. Strong general models should compose a small tool library at inference time. We are not trying to maximize benchmark numbers by accumulating task-specific scripts.

**Primary question:** Can the same VLM and sensor stack complete held-out tasks with higher success and/or fewer model calls and less time when it can delegate short, bounded sequences to a native executor?

This is not guaranteed. Batching can remove important reobservation opportunities; generic grasp macros can fail when geometry or correspondence is poor. The implementation is designed to measure those tradeoffs rather than hard-code a positive result.

## 2. What is allowed, and what is deliberately excluded

Allowed inputs are the original task instruction, current calibrated RGB-D, robot proprioception and robot-only geometry, generic tool documentation, current-episode history, tracked references and execution receipts. The agent may create its own plan and notes **inside the current attempt**. It may revise that plan after observing a failure.

Excluded from the main experiment: RPent's published task-exploration memory, prior successful task trajectories, cross-episode retrieval, benchmark-specific skills, per-scene thresholds, hidden object transforms, simulator instance masks, ground-truth scene articulation axes and benchmark success geometry. Native task success is used for shared stopping/evaluation. Main configurations disable actor-requested completion queries.

“No task memory” is not “no memory.” Removing current-episode context would cripple the agent artificially. Conversely, “no new task adaptation” does not prove that a pretrained VLM or VLA never encountered related data. Record each checkpoint's training provenance and describe the evaluation accurately.

The implementation contains no task-specific drawer, knob, microwave, GPU or screw routine. Its motion-plan API accepts **pose and gripper segments**, and its grasp API belongs to a parallel-jaw manipulator rather than an object/task category.

## 3. Corrected source findings

### K1 already does substantial local execution

K1 is not a naive “ask GPT to move two centimeters forever” baseline. Its `move_toward` can spend up to 120 native steps on an absolute-position target, with stagnation and arrival checks. It already tracks evidence, checks request frames, supports episode memory and stops on native success.

We use K1's actual `run_agent(... registry_class=..., client_factory=...)` extension seams rather than rewriting its perception or prompt loop. The stock arm uses the original registry. Claims must credit what K1 already provides.

### DynaHarness is a methodological donor, not this experiment's oracle backend

The uploaded DynaHarness PDF disclosed simulator-state grounding in LIBERO and a benchmark-developed analytic contact library. Its large frozen-policy-to-full-system gain was not a pure scheduler improvement. That approach was relevant to the previous reproduction package, but conflicts with the user's latest generality standard.

We retain task-independent ideas—bounded execution, freshness, progress checks and structured evidence—without importing privileged grounding or the task-family skill catalog. Do not compare this package's unrun results against DynaHarness's headline percentage.

### FLUX is not yet a LIBERO drop-in

The official FLUX 3 Action DROID release consumes wrist/left/right camera frames plus joint state, and produces absolute joint/gripper commands: `(1, 32, 8)`. K1's LIBERO adapter uses agentview/wrist RGB-D and normalized 7D Cartesian OSC commands. These are not interchangeable merely because both involve a Franka-family arm.

The package therefore provides an offline FLUX recorded-observation probe, and an explicit frozen-policy integration contract. The implemented optional executable bridge targets RPent's π0.5 LIBERO interface instead. This is **source-inspected, not native-qualified**. No fake third camera, silent joint-to-OSC conversion, zero-action fallback or synthetic policy success is used.

## 4. Architecture and implemented modules

```text
actual K1 run_agent
  ├─ existing prompt, current RGB-D, tools, episode history
  ├─ original registry — baseline
  └─ extended registry
       ├─ execute_motion_plan
       ├─ grasp_from_candidate
       └─ vla_act [only with explicit compatible policy]
                ↓
        bounded local execution / per-native-step evidence
                ↓
        receipt: achieved pose, stop reason, uncertainty, actual steps
                ↓
        model observes and chooses what happens next
```

`k1lab/k1_extension.py` subclasses K1's registry lazily. It preserves original tools and caches only the sensor-derived grasp candidate geometry actually returned to the model. Candidate ranks and hidden diagnostics are not turned into executor truth. After a new macro, superseded K1 active intentions are invalidated, but historical evidence remains available.

`k1lab/engine.py` executes short lists of generic pose/gripper segments. Every pose has an explicit position and quaternion. Pose motion preserves the gripper; opening/closing is a separate segment. The native adapter is stepped one action at a time, with shared episode limits, per-command budgets, lease expiry, arrival tolerances and stagnation checks. There is no full collision planner, force controller or certified safe path.

`k1lab/evidence.py` handles tracked-point co-motion. It compensates for translation **and rotation** of the hand. Lost correspondence, a depth-layer jump, insufficient excitation and contradictory motion remain different outcomes. “Co-motion supported” is not “verified identity” or “verified attachment.”

`k1lab/model_client.py` implements K1's HTTP-client-shaped hook for OpenAI Responses, compatible chat, a file decision queue, or a trusted subprocess. It preserves actual multimodal requests and histories. It does not generate model actions itself.

`k1lab/native.py` extends the inspected K1 LIBERO adapter, preserving the sensor-only observation boundary. Native task success is latched consistently for every condition, not introduced only for the treatment. The optional policy encoder has explicit camera orientation/proprioception conventions and requires qualification.

`k1lab/policy.py` and `policy_bridge.py` define a hash-bound, loopback policy service. Actions are checked for shape, finiteness, action space and normalized bounds. Predictions execute one native action at a time; unexecuted actions are discarded at a handoff. A policy subgoal receipt does not assert local task completion.

`manifests.py`, `qualification.py`, `evaluation.py`, `journal.py` and `runner.py` handle immutable state fingerprints, source/config freezing, policy qualification, alternating condition order, all-attempt outcomes, paired statistics and append-only evidence.

## 5. Tool semantics and limits

### `execute_motion_plan`

Example **illustrative command**, not a prerecorded task solution:

```json
{
  "frame_id": 12,
  "arm": "arm",
  "command_id": "transit-001",
  "segments": [
    {
      "kind": "pose",
      "target_xyz_world_m": [0.1, 0.0, 0.5],
      "target_quaternion_xyzw": [0, 0, 0, 1],
      "profile": "transit"
    },
    {"kind": "gripper", "gripper": 0.0, "settle_steps": 10}
  ],
  "max_native_steps": 120,
  "watch_points": [],
  "decision_note": "Short observable rationale grounded in the current input."
}
```

The model must determine a meaningful target from current evidence. A successful numeric command is not proof that the object reached its destination. An optional `watch_points` list watches **stationary** features and stops on loss or displacement; do not put a deliberately moving carried target in that list.

The schema allows at most six segments. Unknown fields, nonfinite values, unnormalized quaternions, stale frames, impossible minimum budgets and overlong single moves are rejected. Command IDs bind to request hashes: replaying an identical command returns its historical receipt, not a second physical execution.

### `grasp_from_candidate`

Requires a fresh K1 candidate ID, the corresponding arm, a current tracked target point and already-open jaws. It attempts pregrasp, approach, closure and a small 8–30 mm lift probe. It stops when evidence is lost/contradictory and never automatically transports far, releases an uncertain object or repeats a failed grasp. The model reviews the returned receipt and fresh images.

This is a generic device-level macro, but still a hypothesis about useful granularity. It should remain optional if it does not improve held-out behavior. It is not intended to solve deformable objects, insertion, arbitrary contact or full-arm collision checking.

### `vla_act`

Available only when a compatible frozen policy is configured. The actor provides a bounded textual subgoal, not a task-specific script. Missing perception does not automatically imply that a VLA can solve the problem. No hidden analytic rescue is invoked on a policy failure.

### Default limits are engineering starting points

20 Hz native control; 160 native steps per macro; 120-second command lease; 0.5 m maximum individual displacement; 4 mm/3-degree arrival tolerance; three settled frames; 24 non-progress steps; nominal transit cap 0.15 m/s, approach cap 0.025 m/s and angular cap 60 degrees/s. The workspace box is a coarse bound, not obstacle avoidance. Do not treat these defaults as tuned or safety-qualified.

More classical control does not guarantee faster physical motion: K1 already uses it. The likely benefit to test is fewer model round trips, better persistence of pose intentions and useful multi-stage execution. Native rendering and observation reconstruction can still dominate wall time.

## 6. Experiment conditions

**No-VLA primary:** `k1_baseline` versus `k1_sparse`. Same VLM, images, history, state bank and no policy. The change includes macro tools, execution profiles and receipts, so it is a complete extension comparison rather than an isolated scheduler bit.

**Closer execution diagnostic:** `k1_stepwise` versus `k1_sparse`. Stepwise uses the new engine for a single segment at a time and omits the grasp macro. This helps distinguish native-control implementation changes from sparse multi-stage control. A batching-only experiment should explicitly disable the grasp macro for the sparse arm too in a separately frozen revision.

**Optional hybrid:** `hybrid_stepwise` versus `hybrid_sparse`, with the exact same policy checkpoint/spec. Short policy windows default to eight native steps; sparse windows to forty. `policy_only` provides a contextual frozen-policy baseline. It is not a controlled comparison to a no-VLA model stack.

Do not add a deliberately crippled direct-motor baseline before the competent K1 baseline works. Direct-A/B, RoboICL, task-memory comparisons, active-camera extensions, distillation and robot training are not implemented in this revision. They can be separate later experiments, not prerequisites to the first useful result.

## 7. Offline setup and tests

From the repository root:

```bash
python -m pip install -e '.[test]'
python run.py doctor
python -m pytest -q
python run.py synthetic --output runs/my-cpu-check
python scripts/analyze.py --run runs/my-cpu-check \
  --left scripted_unbundled --right scripted_bundled
```

The synthetic check uses four authored kinematic cases: normal motion, blocked motion, a terminal-stop event and lost feature evidence. Both control conditions are authored scripts, not LLM policies. Accuracy is deliberately not manufactured to favor bundling. All eight case-condition runs preserve receipts and journals.

Open `runs/my-cpu-check/report.html`. It is offline and clearly labeled. Optional plot production after installing Matplotlib:

```bash
python scripts/plot_results.py --run runs/my-cpu-check \
  --left scripted_unbundled --right scripted_bundled --output runs/my-cpu-plots
```

These plots are software-check illustrations only. Plotting code does not import any paper's success rates as our data.

## 8. Native K1/LIBERO environment

The build host cannot clone GitHub directly and has no MuJoCo/robotics runtime or GPU. The bootstrap therefore has not completed here. On the external machine:

```bash
python scripts/bootstrap.py --group core --allow-network
python scripts/source_probe.py --k1 external/k1
```

The lock pins K1 and **Zxy-MLlab/LIBERO-PRO**, not the incompatible newer RLinf LIBERO layout. Prepare K1's documented RoboSuite 1.4 environment in a fresh virtual environment. Do not blindly combine historical benchmark model pins with your serving environment. Install K1 and this package after preparing that environment:

```bash
python -m pip install -e external/k1
python -m pip install -e '.[native,test]'
```

Obtain benchmark assets, BDDL files and initial-state archives under the upstream terms. No datasets are bundled. Use only trusted local archives because the official state format is loaded via `torch.load(... weights_only=False)`.

```bash
robo-harness configure-libero \
  --repo external/LIBERO-PRO --data data/libero-pro --output configs/libero.local
export LIBERO_ROOT="$PWD/external/LIBERO-PRO"
export LIBERO_CONFIG_PATH="$PWD/configs/libero.local"
export MUJOCO_GL=egl
```

Default configs enable region tools, which require K1's SAM3 package/weights. Set `ROBO_HARNESS_SAM3_CHECKPOINT` and verify segmentation independently. LK tracking itself is lightweight. A no-SAM3 smoke can disable `region_tools` in **all** arms, but candidate grasp will then be unavailable; label that protocol separately.

Build a fixed task-state manifest without running test episodes:

```bash
python run.py make-manifest \
  --native-config configs/file/k1_baseline.json \
  --suites libero_goal_task libero_goal_swap \
  --indices 0 1 2 --trust-local-state-archives \
  --output manifests/goal-paired.json
python scripts/select_dev.py --manifest manifests/goal-paired.json \
  --count 2 --output manifests/goal-smoke.json
```

The selector prints the two development case IDs. Use one for reset/render and one zero-target tick:

```bash
python scripts/native_smoke.py --config configs/file/k1_baseline.json \
  --manifest manifests/goal-smoke.json --case <PRINTED_DEV_CASE_ID> \
  --output runs/native-smoke-001 --move-one-step
```

This is a real simulator invocation, not a mock. Inspect camera orientation, depth, frame conventions and robot response. The smoke tests interface execution, not grasp/contact competence.

## 9. Live model or external Codex decision transport

Set an **actually available** model ID; do not assume the names discussed in chat are API identifiers available to your account.

```bash
export K1_MODEL='<available-model-id>'
export OPENAI_API_KEY='<your-key>'
python run.py run \
  --configs configs/responses/k1_baseline.json configs/responses/k1_stepwise.json configs/responses/k1_sparse.json \
  --manifest manifests/goal-smoke.json --partition dev \
  --output runs/native-dev-001 --allow-native --allow-api --pilot
```

Responses transport uses K1's same task/prompt/tools/history, translated to the official API. Compatible chat is also supported. Model outputs must select exactly one supplied tool per decision. No model is substituted after an error. Reasoning effort, output limit and service tier are explicit config choices; Flex may be cheaper but slower or unavailable and is not a latency optimization.

Calls are capped by count and reserved output tokens **per episode**. There is not yet a shared dollar-budget ledger across an entire matrix; start with the two-case pilot and use an external campaign/account spend limit. Failed/unknown calls retain reservations. Provider input-token totals are recorded when available, but no input-dollar ceiling is promised. Set account-level spending controls. The transport does not silently retry an uncertain request.

For external Codex without a directly available API client, use `configs/file/` and omit `--allow-api`. A request is written under each episode's `wire/` directory with `PENDING.json`, `request.json`, exact camera images and `ACTOR_REQUEST.md`. The external actor returns `response.json` atomically:

```json
{
  "request_sha256": "<copied from current pending request>",
  "tool": "<one available tool>",
  "arguments": {"frame_id": 0, "decision_note": "..."}
}
```

Arguments must follow the actual tool schema, not this abbreviated example. The bridge checks request binding and tool identity. The optional `chat_response` format can preserve full provider usage metadata. Missing usage is recorded as unknown, not zero cost.

**File/subprocess mode is trusted and not a sandbox.** Use a fresh external actor session for each episode; do not let the coding agent retain previous evaluation-task solutions in its own conversation or filesystem. To measure cleanly, give the actor only the exported request bundle and generic tool docs—not the benchmark state files, source geometry or other episode solutions. `examples/respond_once.py` is a transport test that requests `done`; it is not a robotics planner.

## 10. Optional frozen-policy lane

First complete the no-VLA native comparison. Then fetch the policy-side repositories:

```bash
python scripts/bootstrap.py --group policy --allow-network
```

Prepare a **separate** GPU environment following the pinned RPent/RLinf/openpi instructions. Serve the model there rather than installing RPent's simulator/controller dependencies into K1's environment.

```bash
python scripts/serve_rpent_policy.py \
  --rpent external/RPent --checkpoint /absolute/path/to/qualified-checkpoint \
  --model-id '<exact-checkpoint-name>' --spec-output runs/policy-spec.json \
  --port 8811 --cuda-device 0 --allow-gpu
```

The server fingerprints actual supplied checkpoint files, loads RPent's real `Pi05VLAFacade` and emits an explicit spec. Loading a model or reaching `/health` is **not** native qualification. The actor observations, normalization, gripper sign, action units and controller state must be checked with recorded native evidence.

Generate new configs in a fresh directory:

```bash
python scripts/make_configs.py --transport responses --model "$K1_MODEL" \
  --policy-spec runs/policy-spec.json --output configs/hybrid-local
```

For development only, `--pilot --allow-policy` permits qualification attempts. Formal hybrid evaluation requires `native_qualification_path` and its SHA-256 in the policy config. Start from `examples/policy_qualification.template.json`; fill it with actual checks and hashed artifacts, never fabricated passes. A local SSH tunnel can expose a remote policy server on loopback. The bridge has no public unauthenticated write interface.

FLUX's recorded DROID probe is separately available:

```bash
python scripts/flux_offline_probe.py --observation /path/to/droid-observation.npz \
  --checkpoint /path/to/flux-droid --task '<recorded instruction>' \
  --output runs/flux-recorded-probe
# Add --execute only inside the prepared FLUX GPU environment.
```

It validates camera/state shapes and optionally runs the official CLI. Predicted joint8 actions are saved, **not executed** on LIBERO. A genuinely compatible FLUX backend is future work.

## 11. Freeze, run, analyze

After development, choose final settings and freeze them before seeing test outcomes:

```bash
python scripts/freeze.py \
  --configs configs/responses/k1_baseline.json configs/responses/k1_stepwise.json configs/responses/k1_sparse.json \
  --manifest manifests/goal-paired.json --output manifests/goal-freeze.json
python run.py run \
  --configs configs/responses/k1_baseline.json configs/responses/k1_stepwise.json configs/responses/k1_sparse.json \
  --manifest manifests/goal-paired.json --partition test \
  --output runs/native-test-001 --allow-native --allow-api
python scripts/analyze.py --run runs/native-test-001 --partition test \
  --left k1_baseline --right k1_sparse
```

`freeze.py` resolves `K1_MODEL` into the config. Changing an environment variable later cannot silently swap the frozen actor. Code or config changes invalidate the freeze. Do not regenerate a freeze after reading failures and continue calling those cases held-out.

The runner alternates condition order across cases. It keeps failures, missing cases and infrastructure errors in the denominator. The analyzer refuses mismatched comparison signatures. Report paired differences with uncertainty and cluster by base task; repeated states of one task are not independent task-generalization evidence.

Native step totals and wall times answer different questions. The report includes physical success by budget fraction, model/policy calls, provider-reported tokens and usage coverage, all-attempt wall time, conditional successful-step medians and a declared failure-penalized step metric. Missing cost data is not evidence that a run was cheap. Optional plots are generated from actual saved outcomes.

## 12. First milestones and stopping rules

**M0:** Local tests and source seam checks pass. This is software bring-up only.

**M1:** Real K1 reset, calibrated render, one measured control tick and one real VLM decision. Fix environment/API faults before calling the architecture bad.

**M2:** The stock baseline completes a useful development task or produces an interpretable failure. A native pose/gripper sequence and honest grasp-evidence receipt execute through the extension. Do not proceed to a large campaign on unqualified motion.

**M3:** A frozen paired no-VLA test. Success may tie; fewer model calls without a statistically obvious reliability loss is worth examining. If bundling harms success, diagnose generic reobservation boundaries. Do not write a task-specific rescue script.

**M4:** Optional matched-policy test after the observation/action bridge is qualified. Record the checkpoint's prior training distribution; do not present a strong benchmark-finetuned VLA as untrained zero-shot manipulation.

**M5:** New task families or a second environment through a thin adapter, then active perception using physically available sensors. The current runner implements LIBERO only. RATs is pinned as a future reference, not a functioning second benchmark in this package.

Stop adding abstraction when the next unknown requires an actual rollout. Do not return to factory visualization, benchmark oracle skills, model training, autonomous skill evolution or robot distillation before measuring the present question.

## 13. Limitations that must survive the handoff

The CPU tests use injected K1/interface doubles and synthetic kinematics. Actual upstream K1 was inspected via the connector but was not cloned or imported on this host. Dependencies, CUDA/rendering kernels, SAM3 integration, controller calibration, policy inference, grasp success and model quality remain unqualified.

The extension performs no certified collision avoidance, force limiting or hardware safety enforcement. Its source checks and hashes are reproducibility aids, not an adversarial sandbox or proof of generalization. The broad workspace box is not a substitute for scene geometry. No extra free-floating inspection camera is introduced.

The current system is synchronous. It reduces model round trips but still pays for frequent sensor processing. End-to-end speedup is an empirical question. A grasp probe can add overhead and false refusals; the co-motion thresholds are generic development defaults.

No released score, old screenshot or synthetic success is a result for this repository. The previous EmbodiedSWE branch achieved assisted motions but did not establish a matched hybrid-versus-direct task-success win. That history motivates the design; it cannot justify a performance claim.

## 14. Links and source pins

- K1 code: https://github.com/Robo-Harness/k1 — `ee46363101fcf3ef87182fb2dbad99a92ce77fc0`
- K1 paper: https://arxiv.org/abs/2609.29389
- K1 environment setup: https://github.com/Robo-Harness/k1/blob/ee46363101fcf3ef87182fb2dbad99a92ce77fc0/docs/environments.md
- LIBERO-PRO source: https://github.com/Zxy-MLlab/LIBERO-PRO — `eafdb809426b13153aa1e4c42d6601844217dfec`
- RPent: https://github.com/RLinf/RPent — `d2595ff270c7d66dbb2effb803f5e6d4d8e08f82`
- Harness VLA paper: https://arxiv.org/abs/2607.08448v5
- RPent memory/provenance: https://rpent.readthedocs.io/en/latest/rst_source/guides/memory.html
- RLinf: https://github.com/RLinf/RLinf — `88f9867ff5b3004b482d6788a871081a43098620`
- openpi fork: https://github.com/RLinf/openpi — `a560f4dd8205b8423ecd4c8a0fabb5f54140b8a0`
- FLUX source/setup: https://github.com/black-forest-labs/flux-action ; https://github.com/black-forest-labs/flux-action/blob/main/docs/setup.md
- FLUX DROID checkpoint: https://huggingface.co/black-forest-labs/flux-3-action-droid
- DynaHarness paper/project: https://arxiv.org/abs/2609.40306v1 ; https://denghaoyuan123.github.io/Dynaharness_page/
- Future RATs/RoboSuite transfer: https://github.com/Playful-RATs/RATs — `1df65a180562e91911214fa1caba7c7ed9407b3d`
- OpenAI vision: https://developers.openai.com/api/docs/guides/images-vision
- OpenAI Flex: https://developers.openai.com/api/docs/guides/flex-processing

`docs/SOURCE_AUDIT.md` gives exact inspected files and distinguishes inherited pins from newly inspected interfaces. `IMPLEMENTATION_STATUS.md` records what was tested. The archive's release manifest allows byte-level integrity verification after transfer.

**The next meaningful artifact is a small real paired K1 experiment with honest failure accounting—not another rewrite, not a forecast score, and not a polished robot animation.**
