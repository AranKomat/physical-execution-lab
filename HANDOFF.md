# Physical Runtime Lab — PDF-grounded DynaHarness reproduction, revision 2

**Date:** October 1, 2026. **Entry point:** `START_HERE.md`, then this document and `AGENTS.md`.

## 1. Objective and what changed

Build a separate, narrow LIBERO-Pro experiment repository that reproduces the important mechanisms and aims to reproduce the substantial gains of **DynaHarness: A Dynamic Physical Harness for Self-Evolving Robot Agents**, arXiv:2609.40306v1. Do not merge this experiment into the earlier BEHAVIOR harness, reopen GPU assembly, or spend time on industrial animations. Those are separate projects.

The user explicitly rejected treating a loosely inspired wrapper as an adequate reproduction. The uploaded **complete 37-page PDF** has now been read, including Appendices A–I. It is included at `references/2609.40306v1.pdf`, SHA-256 `e07c7fd79a2e6690f64cbc07f501894bc96d07c9bc091a735a7ef403572ddd1d`. This version materially changes the implementation, not just its name or documentation.

The build host has Python 3.13, NumPy/SciPy and CPU test tools, but no working LIBERO installation, NVIDIA GPU, model weights or LLM credentials. **No native robotics success rate is claimed.** Our objective remains comparable gains, but those gains must be established by running and improving the actual skills on the external GPU host. An implementation checklist cannot establish them.

The most consequential correction is Appendix A, page 14: **the paper's LIBERO grounding uses simulator state**. Hardware uses images. The old package emphasized RGB-D-only geometry and therefore did not implement the same experimental problem. The new main track deliberately uses disclosed simulator geometry behind a symbolic planner. The old sensor/K1 track is retained for a later, separately reported extension.

A second correction is the source of competence. On page 9 and Table 16, removing the analytic contact skills reduces success from 592/800 to 133/800. Bare policy scores 130/800. In contrast, changing the executor while retaining the library gives 592/800 versus 511/800. The initial harness without evolution was worse than the policy on its own early seed block (page 8). **A good governor around a weak analytic library is not expected to reproduce the headline. Native analytic competence is the next engineering priority.**

## 2. Precise claims to reproduce

Keep these experiments separate; all numbers in this section are the authors' results, not local measurements.

| Source condition | Evaluation | Source result |
|---|---|---:|
| Final archived development build | Four Goal/10 task/swap suites, indices 21–40 | 594/800, 74.25% |
| Separate development remeasurement | Same block, separate run | 593/800, 74.125% |
| A2ctrl concurrent executor control | Development block | 592/800, 74.0% |
| A2static nominal one-step replanning | Same library/block | 511/800, 63.875% |
| A2seq initial frozen sequence | Same library/block; changed planning schema | 510/800, 63.75% |
| Bare public pi0.5 LIBERO | Development block | 130/800, 16.25% |
| No analytic contact capabilities | Concurrent ablation | 133/800, 16.625% |
| No recovery/intervention | Concurrent ablation | 585/800, 73.125% |
| Champion, new-state block C | 800 states generated after freezing | 602/800, 75.25%, shown as 75.2% |
| Bare policy, block C | Same new states | 140/800, 17.5% |

References: Sections 4.2–4.7, Tables 2, 12, 14–17, and Appendices C.1/D.1. The 75.2/17.5 comparison is not the same state bank as the 74.0/63.9 executor comparison. Block C measures **new initial states of the same task families**, not previously unseen task families. Its exact state bank/generation procedure is not supplied in the PDF. Do not rename a new local index slice “the authors' block C.”

The most useful first result is a strong analytic library plus a matched frozen-policy control. The clean executor experiment follows: A2static versus A2ctrl with the **same** geometry, library, model, weights, environment, and budgets. K1 and a stronger planner are subsequent interventions, not changes silently folded into that comparison.

## 3. What the PDF specifies, and what it does not

### Explicit source settings

- Slow model: **Qwen3-VL-4B-Instruct**; Appendix G describes a local 4-bit build. The slow brain returns capability names and symbolic arguments, **not numeric poses** (page 4).
- Motor policy: public frozen **pi0.5 LIBERO** checkpoint. This is not the RLinf `pi05_libero130_fullshot` checkpoint used by some cited baselines (pages 5/17).
- Controller: 20 Hz. Deterministic fast governor: 2 Hz. Safety/envelope check: 50 Hz. Velocity envelope: 2 rad/s (pages 4/14/27).
- Policy execution: ten-action chunks; one illustrated `vla_act` call executes two chunks, twenty steps (page 28).
- Environment steps: Spatial 220, Object 280, Goal 300, LIBERO-10 520. Main reproduction covers Goal-task, Goal-swap, 10-task, 10-swap (pages 5/16).
- Shared executor settings: temperature 0.1, 2,048 output tokens, 90-second request timeout, 180-second plan validity, one serialization-repair allowance, 600 orchestration ticks (page 25).
- A2seq: initial complete sequence; one same-step retry, one replay of that single-step plan, then one further retry; twelve blocked-precondition ticks; no online branching or replanning (page 26).
- A2static: replanning after nominal local success only. No failure-triggered replan, substitution, reordering, inserted recovery, or verifier-triggered branch. It retains fixed retries/reexecution (page 24).
- Native success predicate, not model self-report, supplies LIBERO task completion. Completion sampling and the 2 Hz decision clock are separate; latching retains detected events (pages 4/14).
- Drawer revisions: 20 mm along-handle grasp shift, a widened closure limit, reseating after misaligned contact, and waiting for two consecutive stalled pulls (pages 31–32).
- Eq. (5): nondecreasing aggregate cell successes, nonincreasing harness-attributed failures, nondecreasing successes in policy-winning cells, zero contamination, **then broader regression checks** (pages 5/15/32/37).

### Not fully specified in the PDF

Exact skill source, all seven analytic-removal IDs, all six recovery-removal IDs, the original prompt, every geometry heuristic, gains/tolerances, precise closure threshold, command lease, full scheduler thresholds, the ordered thirteen diagnostic checks, exact weight revision/hash, normalization/sampler settings, quantization implementation, exact camera configuration, and block-C state bytes are not provided in sufficient detail for bit-identical reproduction.

The paper says an anonymized supplementary implementation/configuration/records package exists (page 11). The uploaded PDF has no embedded package or direct supplementary download link. The linked public implementation repository returned 404 during this revision's check. **Check for the release again or obtain the supplement from the authors; do not wait idly for it.** Replace uncertain local reconstructions with source code when it becomes available, preserving a reviewed provenance/diff.

`docs/PAPER_FIDELITY.md` maps source requirements to files and remaining gaps. Every unsupported default is a reconstruction choice, not a newly discovered paper constant.

## 4. Actual implementation

The new namespace is `prl/dyna/`; the new command is `python paper_run.py ...`.

### Protocol and semantic planning

`protocol.py` encodes the rates, suite budgets, source reference blocks, and explicit reconstruction settings. `planner.py` uses the same one-step prompt/catalog for A2static/A2ctrl and a full-sequence schema for A2seq. It rejects numeric/nested action arguments and invented output fields, permits one serialization-only repair, checks snapshot identity/epochs, and checks plan age.

The planner sees the actual language instruction, two current images, symbolic scene entities/mechanisms, robot state, and within-episode history. It does not receive object metric geometry or parsed benchmark goal clauses. The original source prompt is unavailable; this prompt is reconstructed. Observation IDs/paths remain experiment metadata, not a hardened adversarial information boundary.

Existing API/file/command transports are reused through decoder injection. The API transport supports an explicit OpenAI-compatible endpoint; no model ID or paid endpoint is silently selected. A file queue lets external Codex act as a planner, but that is a **different planner/scaffold experiment**, not the Qwen reproduction.

### Simulator grounding and physical skills

`scene.py` defines objects, regions, mechanisms, contact observations, geometry provenance and within-episode execution memory. `native.py` obtains current poses, collision-geometry bounds, sites, joint axes/limits, and actual finger/object contact pairs from the native simulator.

`capabilities.py` reconstructs the documented families: pick-and-place, insertion/placement, push, drawer slide, knob turn, hinged door, handle turn, keyframe return, release/retreat, regrasp/reseat, perception and frozen policy execution. Capabilities have local completion evidence distinct from native task success.

Concrete improvements over v1 include:

- Geometric approach, descent, jaw closure, lift, overhead transport, lowering, release and retreat stages.
- Grasp verification using both finger contacts plus object lift, rather than treating gripper closure as attachment.
- Measured object-to-TCP transform after lifting; transport targets are converted accordingly.
- Separate cavity/receptacle versus support handling. A flat thin hob must not be treated as an insertion cavity—the exact class of regression discussed on page 32.
- Distinct placement-slot selection for multiple objects, and a conservative object-level overhead corridor.
- Push-span refusal with pick/place substitution only where the instruction permits achieving the same final relation; no substitution when a push-only method constraint is present.
- Joint-axis-grounded drawer/door/knob trajectories, a four-step wrist ramp, the documented 20 mm drawer shift, and a bounded reseat route.
- Keyframe recovery scoped to the current episode and physical state.
- Preflight refusal when the remaining budget cannot afford the capability.

**Important limitations:** the insertion implementation is presently staged cavity placement, not a qualified general connector insertion controller. The corridor is not full-arm collision planning. Grasp features, jaw axis, mechanism endpoint meaning and cavity entrances require actual simulator qualification. Four recovery families are implemented; this is not a claim to have recovered the original six-entry ablation roster. Drawer reseating is not the exact unpublished two-stalled-pull mechanism.

Table 4 lists approximate stage costs whose midpoint values sum to 211, while it reports approximately 230 for the whole pick/place command. The implementation reserves at least 230 before starting an unheld-object pick/place but counts only actual actions. It does not fabricate nineteen actions to force agreement. These source costs are useful budget anchors, not validated local trajectory durations.

### Runtime / controlled executors

`engine.py` separates per-action control, periodic governor decisions and physics-substep safety callbacks. Every executed action consumes the same episode budget. Native completion is sampled every completed action and latched until read; `unlatched` changes retention, not the sampling period. Receipt status and benchmark verdict remain distinct.

A2static replans after local nominal success, not failure. A2seq freezes the initial plan. Both have bounded fixed retries. A2ctrl additionally permits refusal/substitution, failure replanning and a bounded drawer reseat. All share the same capability implementation and basic safety/budget rules. A policy segment ending without a trustworthy intermediate effect is not silently declared a completed task.

There are explicit differences from the original implementation: unknown scheduler thresholds use recorded defaults; precondition-block counters are bounded scheduler events rather than a native recreation of every original wait; A2static's four-attempt count is reconstructed from its prose and the explicit A2seq schedule. Native runs must characterize these differences.

`native.py` uses **a direct LIBERO-PRO environment seam plus RPent's frozen-policy client**, not the old complete RPent episode wrapper. The latter strips some geometry and terminates immediately on native success, complicating the independent latching experiment. It is still the pinned RPent/RLinf/LIBERO ecosystem, not an unrelated simulator.

The source-inspected policy server defaults to **five-action chunks**. `scripts/serve_paper_policy.py` explicitly overrides both relevant preset fields to ten, hashes requested model bytes, loads the model and serves a live attestation. The backend checks that live attestation against the file and expected checkpoint hash. It does not claim that a local hash establishes equality with the authors' undisclosed model revision.

### Evaluation and evolution

`runner.py` retains all planned cases in the denominator, labels missing/infrastructure rows, and records config/source/PDF/manifest fingerprints. Its comparison reports paired wins/losses, exact discordant-pair tests and task-cell bootstrap intervals. The default bootstrap is 20,000 resamples with seed 20260926, following Table 17. Avoid interpreting a tiny pilot's p value as a broad capability result.

`admission.py` implements the **cell-count** interpretation of Eq. (5), replacing v1's stricter per-seed winning-episode preservation. The thirteen-label diagnostic is explicitly reconstructed and produces reviewable hypotheses. Unmatched diagnostics stay unresolved. Admission requires attribution review and broader coverage; it does not edit a production library or authorize hardware.

Failed-state archives currently save physics state and metadata, not controller integrators, RNG, action-chunk cursor and full agent state. They are useful diagnostic probes, **not exact branch-resume checkpoints**. Complete this if undertaking matched failure-state interventions.

## 5. Run the CPU version first

From the repository root:

```bash
python -m pip install -e '.[test]'
python -m pytest -q
python paper_run.py audit
python scripts/verify_release.py

python scripts/run_paper_matrix.py \
  --configs configs/dyna/fixture_bare.json \
            configs/dyna/fixture_A2static.json \
            configs/dyna/fixture_A2seq.json \
            configs/dyna/fixture_A2ctrl.json \
            configs/dyna/fixture_unlatched.json \
  --manifest manifests/synthetic_dev.json \
  --output runs/paper-cpu --execute

python paper_run.py compare \
  runs/paper-cpu/A2static runs/paper-cpu/A2ctrl \
  --output runs/paper-cpu/paired.json
python scripts/audit_paper_run.py runs/paper-cpu/A2static
python scripts/audit_paper_run.py runs/paper-cpu/A2seq
```

The included synthetic fixture is a kinematic test double with authored decisions and no learned policy. It tests implementation behavior; it is not LIBERO. The nominal/dynamic controllers can tie on these simple fixtures. No artificial large improvement is inserted into the report.

## 6. External native setup

Use a fresh Linux Python **3.10–3.12** environment; the build host's Python 3.13 is unsuitable for pinned RPent. Keep Qwen serving and robot policy dependencies isolated if their Transformers/CUDA requirements conflict. Start with one simulator and one policy service. Do not saturate the host before measuring latency and failures.

```bash
python3.11 -m venv .venv-native
source .venv-native/bin/activate
python -m pip install --upgrade pip
python scripts/bootstrap.py --group core       # inspect pins/paths
python scripts/bootstrap.py --group core --execute
python scripts/install_native.py               # inspect installation plan
python scripts/install_native.py --execute
python -m pip install -e '.[test]'
python -m pip check
python scripts/freeze_environment.py --output runs/native-environment.json
```

These bootstrap/install recipes were source-inspected, not installed end-to-end here. The installer avoids blindly requesting moving-branch RPent extras, but it is not a fully solved transitive CUDA environment lock. Review the installed packages and archive an exact environment snapshot. MuJoCo is deliberately pinned to **3.3.0**, as required by the inspected RPent configuration. This is the chosen upstream stack, not proof of the authors' exact simulator version.

The pinned revisions are:

| Checkout | Commit |
|---|---|
| RLinf/RPent | `d2595ff270c7d66dbb2effb803f5e6d4d8e08f82` |
| RLinf/RLinf | `88f9867ff5b3004b482d6788a871081a43098620` |
| RLinf/openpi | `a560f4dd8205b8423ecd4c8a0fabb5f54140b8a0` |
| RLinf/LIBERO | `a8323074d93a09e32bd898630a70531b1f51bc77` |
| RLinf/LIBERO-PRO | `d1e11fb181b8544487d27742c0caa3a4d46452ad` |
| Robo-Harness/k1, optional later | `ee46363101fcf3ef87182fb2dbad99a92ce77fc0` |

The bootstrap refuses to overwrite modified checkouts. No upstream implementation is vendored; obtain dependencies and assets under their licenses. An explicit reviewed new pin is preferable to silently changing installed upstream code.

### Model serving

Obtain the **public Physical Intelligence pi0.5 LIBERO** weights using the official provider instructions and verify their model/configuration provenance. Archive the download revision, normalization and model configuration. Do not use an SFT/RLinf fullshot model merely because a default path points to it.

```bash
python scripts/fingerprint_checkpoint.py /absolute/path/to/pi05_libero \
  --output runs/pi05-libero-weights.json

python scripts/serve_paper_policy.py \
  --rpent-root external/RPent \
  --model-path /absolute/path/to/pi05_libero \
  --checkpoint-manifest runs/pi05-libero-weights.json \
  --checkpoint-id YOUR_VERIFIED_PUBLIC_PI_CHECKPOINT_ID_AND_REVISION \
  --attestation-out runs/policy-attestation.json \
  --cuda-device 0 --port 8911
```

Serve Qwen3-VL-4B-Instruct at an explicit OpenAI-compatible endpoint. Configure its actual served model name, tokenizer/chat template, quantization and image support. The PDF's “local 4-bit” description does not establish a particular AWQ/GPTQ/BitsAndBytes implementation; record your choice as a difference unless source code confirms it. The client imposes source temperature/output/timeout settings and JSON validation; decoder-constrained output support varies by server and needs testing.

### State catalog and manifests

```bash
python run.py catalog --rpent-root external/RPent --output manifests/native_catalog.json
python run.py manifest --catalog manifests/native_catalog.json \
  --split smoke --states 21 --tasks 0 1 --output manifests/native_smoke.json
python run.py manifest --catalog manifests/native_catalog.json \
  --split dev --states $(seq 21 40) --output manifests/paper_dev_800.json
```

The default catalog selects the four paper suites. State indices refer to entries in stored initial-state archives; the hash of each state is checked on reset. No modulo wrapping is allowed. Verify actual task order, BDDL hashes and bank sizes. The eight-case smoke selection is for integration, not a result to pitch.

For your own held-out confirmation, select a disjoint bank, freeze code/prompts/settings first, then verify it using `run.py check-splits`. Calling it “independent held-out initial states” is accurate; claiming the authors' block C is not.

### Configuring and qualifying native execution

Copy the desired `configs/dyna/*.template.json` files to local configs. Set `checkpoint_id`, `checkpoint_sha256` from the weights manifest, live attestation path, endpoints, RPent path and model name. Freeze the same geometry overrides and settings across conditions. The example call ceiling of 150 is a **pilot ceiling**, not a sufficient budget for an 800-episode campaign; explicitly review any increase. Token reservations are not a guaranteed dollar cap.

```bash
python scripts/native_paper_smoke.py \
  --config configs/dyna/A2ctrl.local.json --manifest manifests/native_smoke.json \
  --output runs/native-inspect --allow-native

python scripts/native_paper_smoke.py \
  --config configs/dyna/A2ctrl.local.json --manifest manifests/native_smoke.json \
  --output runs/native-motion --allow-native --move-up-1cm

python scripts/native_paper_smoke.py \
  --config configs/dyna/A2ctrl.local.json --manifest manifests/native_smoke.json \
  --output runs/native-policy-inspect --allow-native --policy-probe
```

These create new simulation episodes, not connections to real robots. The policy probe checks a `[10,7]` chunk but does **not** execute it. Next run a bare-policy smoke episode to test the entire actual policy path.

Inspect physical object bounds, sites, handle identity, joint axes/open-versus-closed direction, camera orientation and OSC scales before a full run. The library currently uses named physical-asset heuristics for region type and range endpoints for joint state. Freeze corrected **asset/mechanism** annotations; never add branches keyed by task ID, seed or success label. The simulator geometry is intentional, but native goal clauses must not be fed into the planner as an answer.

The 50 Hz watchdog hooks native simulation substeps. It verifies that callbacks actually fire. If the MuJoCo binding bypasses or forbids the hook, fix the adapter rather than calling a per-action 20 Hz check “50 Hz.” An exception after partial native stepping is marked uncertain and is not retried automatically. No hardware safety certification is implied.

## 7. Experiment sequence and stopping rules

**Stage 0 — parity audit and native bring-up.** Read the PDF, compare the fidelity matrix, check the supplemental code again, qualify state/geometry/controller/policy seams. Stop after repeated setup errors. Preserve complete failures rather than launching more workers.

**Stage 1 — analytic competence.** Use a small disclosed development set covering surface placement, two-object receptacle placement, relational placement, a knob, a drawer, and a hinged door. Exercise the actual skills and inspect physical traces. This is development, not a held-out score. The first objective is useful physical behavior inside 300/520 steps. Fix gripping/presentation/corridor/entry geometry rather than adding more agent abstractions.

**Stage 2 — matched systems and executor comparisons.** Freeze a candidate library and run `bare`, `A2static`, `A2seq`, `A2ctrl` on the same predeclared states. Start with a modest balanced pilot, then expand. Use the weak source reasoner first to avoid changing the central hypothesis.

```bash
python scripts/run_paper_matrix.py \
  --configs configs/dyna/bare.local.json configs/dyna/A2static.local.json \
            configs/dyna/A2seq.local.json configs/dyna/A2ctrl.local.json \
  --manifest manifests/paper_dev_800.json --output runs/paper-development \
  --execute --allow-native --allow-api

python paper_run.py compare runs/paper-development/A2static \
  runs/paper-development/A2ctrl --contrast executor --output runs/paper-development/executor.json
python paper_run.py compare runs/paper-development/bare \
  runs/paper-development/A2ctrl --contrast system --output runs/paper-development/system.json
```

The matrix runs sequentially in isolated processes and stops on incomplete/infrastructure-error arms. Parallelization should come only after a one-worker baseline is stable. Measure host load and make infrastructure replacement rules independent of which episodes succeed.

**Stage 3 — mechanism checks.** Audit actual traces for no forbidden A2static/A2seq branching; verify disabled capabilities are never dispatched. Run contact removal, recovery removal, no-policy and unlatched conditions as separate contrasts. Because the original exact rosters are absent, label our removals by their implemented names. Removing the policy can also affect routing; do not call that a pure causal estimate of VLA usefulness.

**Stage 4 — failure-directed revision.** Cluster failed physical effects. Inspect the failed current state, not just a fresh reset. Change one reusable physical mechanism at a time, in physical quantities. Evaluate a paired targeted gate and then the broader set with the same candidate hash. Do not promote solely because one task improves. Keep diagnostic labels distinct from causal proof and record human/agent involvement in proposing the patch.

**Stage 5 — post-selection initial-state transfer.** Freeze everything before selecting/generating the new bank. Rerun the frozen-policy control on exactly the same bank. Report local counts, intervals, per-task breakdown, failure types, calls, environment steps and wall time. An improvement on known development cases is not proof of unseen-state generalization.

**Stage 6 — K1 and stronger planners.** Replace privileged grounding with measured RGB-D plus K1, keeping execution constant where possible. This is the valuable harder extension, not the fastest route to reproducing the paper. Separately test a stronger planner and measure cost/latency. Neither intervention should be inserted silently into the source-matched row. Broader benchmarks come after the first result, not before.

## 8. Acceptance criteria and interpretation

There is no target percentage hard-coded into control or scoring. Aim to recover the source's qualitative pattern and competitive scale of gains through actual testing: competent analytic execution materially above the bare policy, and dynamic execution improving the same-library nominal comparator. Diagnose non-reproduction rather than extending budgets or changing a checkpoint under the same label.

A credible result bundle contains frozen code/config/checkpoint/environment hashes; a complete manifest; native videos for representative successes **and failures**; per-action evidence; full-denominator outcomes; actual A2static/A2seq audits; paired statistics; and a clearly listed source-parity gap table. Report sampling uncertainty and task-level distribution. Do not claim general industrial reliability from LIBERO-Pro.

Synthetic tests verify software contracts, not grasping or a 75% task success rate. Comparable gains have **not** been measured on this host. The repository is materially closer to the paper's experiment, but native calibration, capability quality and complete evaluation remain the external agent's work.

## 9. Source links and donor boundaries

- Main paper: https://arxiv.org/abs/2609.40306 and https://arxiv.org/pdf/2609.40306v1
- Project: https://denghaoyuan123.github.io/Dynaharness_page/
- Linked implementation, unavailable when checked: https://github.com/Denghaoyuan123/DynaHarness
- Project-page source (not runtime source): https://github.com/Denghaoyuan123/Dynaharness_page
- RPent: https://github.com/RLinf/RPent
- RPent docs: https://rpent.readthedocs.io/
- RPent policy server: https://github.com/RLinf/RPent/blob/d2595ff270c7d66dbb2effb803f5e6d4d8e08f82/rpent/robots/components/pi05_vla_server.py
- RLinf: https://github.com/RLinf/RLinf
- Policy loader fork: https://github.com/RLinf/openpi
- Official Physical Intelligence source/model documentation: https://github.com/Physical-Intelligence/openpi
- LIBERO-PRO fork: https://github.com/RLinf/LIBERO-PRO
- Original LIBERO-PRO: https://github.com/Zxy-MLlab/LIBERO-PRO
- K1: https://github.com/Robo-Harness/k1 and https://arxiv.org/abs/2609.29389
- K1 geometry: https://github.com/Robo-Harness/k1/blob/ee46363101fcf3ef87182fb2dbad99a92ce77fc0/src/robo_harness/geometry.py

RPent is a dependency donor, not evidence its published Harness VLA score uses our checkpoint/protocol. K1 is a later sensor-grounding donor. Intrinsic, Botrail, NVIDIA warehouse, industrial presentation, model training and BEHAVIOR integration are deliberately out of this reproduction's critical path.

**First action for external Codex:** run the CPU tests, inspect the source/fidelity documents, provision one native environment, and make the first actual analytic pick/place complete under the official step budget. Then establish a matched baseline. Do not spend the next session rewriting the architecture or polishing a synthetic scorecard.
