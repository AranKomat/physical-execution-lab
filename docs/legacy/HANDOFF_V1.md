# Physical Runtime Lab — self-contained research and implementation handoff

**Date:** October 1, 2026.  
**Artifact:** independent `physical-runtime-lab` repository, version 0.1.0.  
**Purpose:** quickly test whether a dynamic physical execution harness improves
an unchanged robot policy, starting with LIBERO-Pro, without first undertaking
new model training or integrating the user's much larger BEHAVIOR harness.

## 1. What the next agent is taking over

The user has been exploring a startup around the systems layer for physical AI:
perception, evidence/state, sparse high-level reasoning, conventional control,
learned manipulation, recovery and deployment. They have already worked on a
BEHAVIOR-oriented harness and an EmbodiedSWE GPU-insertion experiment. Those
projects are not to be modified, restarted or merged as part of this spike.

The immediate goal is much narrower: obtain an honest, interpretable robotics
benchmark result that is legible to an AI-infrastructure investor. The proposed
starting point is a reproduction/extension of DynaHarness ideas using public
RPent and K1 components. A useful near-term statement would be “same frozen robot
policy, measured improvement from the surrounding runtime.” That statement must
be supported by real native runs, not the CPU fixtures in this archive.

The delivered code supplies an executable governor, independent capability
compositions, an RPent native adapter, model/file bridges, reproducible case
manifests, evidence journals and paired reporting. **The CPU software path works;
the native path has not been qualified on a GPU. No paid model API was called.**
The actual source implementations and limitations are described below. This is
not merely a proposed folder structure, but it is also not a finished benchmark
reproduction.

Do not interpret the absence of a real LIBERO-Pro result as a reason to rebuild
all the software. Start by qualifying the existing adapter and one useful skill.

## 2. A source correction that materially changes the replication plan

The primary DynaHarness project page is:

https://denghaoyuan123.github.io/Dynaharness_page/

Its paper is https://arxiv.org/pdf/2609.40306 and its project-owned results source
is https://github.com/Denghaoyuan123/Dynaharness_page/blob/main/assets/js/data.js.
The page links to https://github.com/Denghaoyuan123/DynaHarness, which returned
404 during this build. Check again before doing substantial reconstruction.

The available primary source establishes:

- **Qwen3-VL-4B is the slow semantic model, not the motor policy.** The motor
  family is frozen π0.5; its exact checkpoint still needs confirmation.
- The main fast brain is a deterministic execution rule. Do not add another LLM
  call at every 2 Hz tick under the impression that this reproduces the paper.
- The fixed-library comparison is **592/800 versus 511/800**, or 74.0% versus
  63.9%, on a development-state block. The separate post-freeze new-state
  headline is 75.2% versus 17.5%. These are different evaluation scopes.
- **Removing analytic contact skills gives 133/800; removing the VLA gives
  564/800.** Thus a large part of the headline jump is enabled by the capability
  library, not by monitoring alone. Wrapping a weak/incorrect skill in a governor
  will not recreate the headline result.
- The 800-case groups cover `libero_goal_task`, `libero_goal_swap`,
  `libero_10_task`, and `libero_10_swap`, not every suite on RPent's leaderboard.
- The page describes 20 Hz control, 2 Hz fast decisions, and a separate 50 Hz
  safety check. Our code supplies per-native-action software checks; it does not
  implement or qualify an independent 50 Hz safety controller.

The full PDF was not successfully obtained in this environment. The website HTML
and results JavaScript were inspected through the GitHub connector. Exact skill
code, planner prompts, per-task budgets, the simulation observation contract,
new-state generator, and checkpoint details remain unresolved. The structured
`configs/paper_protocol.json` deliberately contains nulls for these requirements.
`python run.py protocol-audit` reports them rather than pretending parity.

**First goal:** an independently implemented, matched local comparison.
**Separate later goal:** an exact paper reproduction after the missing protocol
is resolved. An exact numerical target is not an acceptance test for our code.

## 3. Deliberate scope and dependency choices

**RPent is the native substrate:** https://github.com/RLinf/RPent. Its existing
LIBERO environment and π0.5 service interfaces avoid reimplementing policy
serving and native control. We use its real `LiberoPrimitives`, not invented SDK
calls. Its Harness VLA paper is https://arxiv.org/abs/2607.08448.

**K1 is a selective geometry donor:** https://github.com/Robo-Harness/k1.
The current bridge calls its backprojection and local plane/axis fitting. It
is not a reproduction of K1's entire SAM3/tracking/grasp/history stack. K1 paper:
https://arxiv.org/abs/2609.29389.

**DynaHarness is a scientific reference:** we independently implement bounded
execution/governance and a simplified offline regression gate. We do not claim
its exact evolved analytic library or 13-layer attribution taxonomy.

**Not on the critical path:** Intrinsic, Botrail, Isaac, industrial animations,
BEHAVIOR integration, humanoid hardware, model pretraining, τ₀ post-training,
new fleet infrastructure, or proprietary factory data. These may become useful
later; none helps us interpret the first paired LIBERO-Pro experiment.

All third-party code remains outside the ZIP and is fetched by an explicit,
pinned bootstrap. No weights or simulator assets are redistributed.

### Reviewed source pins

| Checkout under `external/` | Repository | Commit |
|---|---|---|
| RPent | RLinf/RPent | `d2595ff270c7d66dbb2effb803f5e6d4d8e08f82` |
| RLinf | RLinf/RLinf, release/v0.4 | `88f9867ff5b3004b482d6788a871081a43098620` |
| openpi | RLinf/openpi, rpent | `a560f4dd8205b8423ecd4c8a0fabb5f54140b8a0` |
| LIBERO | RLinf/LIBERO, rpent | `a8323074d93a09e32bd898630a70531b1f51bc77` |
| LIBERO-PRO | RLinf/LIBERO-PRO, rpent | `d1e11fb181b8544487d27742c0caa3a4d46452ad` |
| k1 | Robo-Harness/k1 | `ee46363101fcf3ef87182fb2dbad99a92ce77fc0` |

These are recorded in `upstream.lock.json`. This is a source lock, not a solved
transitive Python/CUDA environment lock. The native installer remains a
source-derived starting recipe. Do not claim that the installation was tested
merely because these revisions were read.

## 4. What is implemented

### A. Shared execution contracts

`prl/contracts.py` defines cases, observations, measured targets, proposals,
stages and receipts. The actor receives task text, calibrated images, robot
proprioception and explicitly labeled targets. It does not receive the hidden
success predicate or the full raw simulator object-state dictionary in the
sensor profile.

A proposal contains a capability, structured arguments, an observation ID, a
command budget, a brief decision summary and optional effect-preserving
alternatives. There is no arbitrary code-execution or reset tool in this actor
interface. A supplied `finish` stops reasoning; it does not certify success.

Targets record source, frame, observed step and evidence ID. Missing uncertainty
is not converted into perfect certainty. Backprojected points describe visible
surfaces, not automatically grasp centers or mechanical joint axes.

### B. Independent capability registry

`prl/registry.py` exposes:

`observe`, `measure_pixel`, `move_to`, `set_gripper`, `release`, `rotate_wrist`,
`pick`, `place`, `pick_place`, `push`, `pull_handle`, `swing_handle`,
`vla_contact`, `vla`, and `finish`. E3 additionally exposes `fit_geometry`.

Analytic operations compile into RPent motion/gripper stages. Long XY movement
is segmented consistently in both conditions. The implementation includes
approach, descent, closure, lift, transfer, release, linear pull, and a measured
pivot/axis arc. These are **basic independently written compositions**, not
collision-certified general manipulation and not the paper's fully evolved
contact skills. The default geometry/offsets are research starting parameters.

A command completing its motion budget or reaching its EEF target is not enough
to declare a grasp, placement, insertion or task successful. These intermediate
physical effects remain `unverified` unless supported by an actual verifier.
Native task termination is recorded separately.

### C. Governor and common guards

`prl/governor.py` mediates **every native step**, including steps inside VLA
chunks. Numeric validation, total action budgets and terminal latching apply to
E0, E1 and E2. Idempotency prevents accidentally reexecuting the same proposal.
A possibly executed action with a missing receipt poisons the episode and
requires reconciliation; it is never retried automatically.

The dynamic condition adds target-age/uncertainty checks, a Cartesian
stage-progress monitor and predeclared capability substitution. Its normal
monitoring interval is ten native steps, corresponding to 2 Hz at 20 Hz control.
It can interrupt a stalled EEF move instead of spending the full command budget.

Crucially, **the current VLA stage has no validated object-level progress
estimator**. EEF movement and gripper gap are not fabricated into one. The VLA
gets bounded execution and terminal checks. This is a major extension opportunity
once native failure evidence identifies a useful metric.

Substitutions are conservative: same capability and same semantic-effect
arguments, usually changing analytic versus learned executor. The governor does
not silently reinterpret “push” as “pick and carry.” A different operation
requires the planner to issue a new justified proposal. This is a local design
choice, not an exact copy of DynaHarness substitution semantics.

### D. Source-inspected native bridge

`prl/backends/rpent.py` uses these inspected RPent interfaces:

- `robots.libero.robot_spec._init_runtime` for owned environment/service startup;
- `LiberoEnvClient` and `Pi05VLAClient` for the native environment and policy;
- `LiberoPrimitives` for actual motion, gripper and frozen-policy execution;
- the native `benchmark` registry for task/state catalogs.

`CheckedEnv` decomposes VLA chunks into per-action calls so no long chunk can
bypass governance. This increases RPC overhead versus upstream chunk execution.
Both local comparison conditions pay the same overhead. Optimize only after
correctness and record the change; physical and wall-clock time are distinct.

An interruption can occur before RPent updates its primitive cache. The adapter
therefore synchronizes the latest authoritative observation in a `finally`
block before another command. It also reuses the newly connected client's
initial reset rather than issuing an unnecessary second reset.

The adapter refuses an out-of-range stored state index instead of allowing
RPent's modulo aliasing, checks the state content hash, and uses a fresh owned
simulator. It will not attach to or reset an existing user's experiment worker.
It stops only daemons it created, not a separately running shared policy server.

Optional native video recording streams one policy-oriented image per executed
step. A `video_manifest.json` records frame count, completeness and recording
errors. These images are NOT the optical-calibration pixel coordinates used by
the geometric tools. This path is implemented but not rendered here.

### E. Perception boundary

`prl/geometry.py` implements conventional metric backprojection and adapters to
K1 `unproject` and `fit_geometry`. Native RPent raw RGB and normalized depth are
vertically flipped together to match its optical calibration. Current wrist
extrinsics are fetched at each capture. Images and depth archives are hashed.

E3 imports K1 from the reviewed checkout and refuses an unpinned/dirty source.
It does not substitute a homemade function when the requested K1 import fails.
Full segmentation, persistent learned tracking, candidate grasp synthesis and
full K1 actor reproduction are not yet integrated.

### F. Planner interfaces

Three routes are provided:

1. **OpenAI-compatible chat/function-call API:** image inputs, explicit model and
   endpoint, one bounded `propose_capability` call, durable request/response
   archives, token reservations, timeout/no-retry semantics. It also supports a
   local compatible server. No specific model ID is invented as a default.
2. **External file queue:** the runtime writes request JSON; external Codex reads
   it and the referenced images and writes a hash-bound response atomically.
   This is useful for getting a real agent involved without building an SDK.
3. **Trusted subprocess:** one JSON request on stdin, one response on stdout;
   no shell interpretation, timeout, explicit argv, secret-like environment
   variables removed. It is not a security sandbox for malicious programs.

The authored `ReferencePlanner` only runs synthetic fixtures and is forbidden
on native benchmarks. It exists to test the software path without an LLM.

### G. Evaluation and offline learning controls

`prl/manifests.py` hashes exact stored-state content and keeps dev/test cases
disjoint. `prl/journal.py` writes hash-linked evidence. `prl/evaluation.py`
reports full denominators, errors, native outcomes, paired wins/losses,
descriptive Wilson and exact McNemar statistics, and a task-cluster paired
bootstrap. It refuses several common mismatched comparisons.

`prl/evolution.py` attributes failures to a simplified diagnostic layer and
produces development-only regression admission records. It does not autonomously
write, promote or deploy new capability code. Passing the local gate means
“eligible for broader regression,” not safe for hardware.

The static HTML report is an evidence browser, not another factory animation.

## 5. Immediate CPU checks

From the repository root:

```bash
python run.py doctor
python run.py protocol-audit
python -m pip install -e '.[test]'
python -m pytest -q
python scripts/run_matrix.py \
  --configs configs/synthetic_frozen.json configs/synthetic_nominal.json configs/synthetic_dynamic.json \
  --manifest manifests/synthetic_dev.json --output runs/cpu-check
```

Open `runs/cpu-check/dynamic/report.html` and
`runs/cpu-check/nominal_vs_dynamic.json`.

The local environment ran Python 3.13.5. The dependency-free core works there;
**RPent native work must use Python 3.10–3.12, preferably a fresh 3.11 venv.**
Tests are synthetic/mocked, and therefore do not certify native imports,
rendering, motion, checkpoint correctness or real benchmark performance.

The fixture has normal and blocked toy scenes. It is deterministic arithmetic,
not a physics simulation. The reference planner is authored code, and its VLA
surrogate is intentionally a no-op. Never use its success gap as an investor
robotics result. Nominal and dynamic fixtures currently complete the same normal
cases; dynamic governance reduces some stalled motion, not task complexity.

## 6. Bootstrap native sources and assets

No installation command below was executed on a GPU during this build. Inspect
and run them on the external host in a fresh working directory.

```bash
python3.11 -m venv .venv-native
source .venv-native/bin/activate
python -m pip install --upgrade pip setuptools wheel

# First inspect the exact plan, then download source only.
python scripts/bootstrap.py
python scripts/bootstrap.py --execute

# Source-derived install recipe; resolve native dependencies on this host.
python scripts/install_native.py
python scripts/install_native.py --execute
python -m pip install -e '.[test]'
python -m pip check

export LIBERO_TYPE=pro
export MUJOCO_GL=egl
export PYOPENGL_PLATFORM=egl
liberopro-download-assets --skip-existing
python run.py doctor --rpent-root external/RPent
python scripts/freeze_environment.py --output local/environment.json
```

The bootstrap refuses to reset an existing dirty or differently pinned checkout.
The installer avoids blindly requesting RPent's moving-branch extras, instead
installing the reviewed native repositories explicitly. Package dependency
solving may still need work. Do not simply upgrade MuJoCo until it imports: the
reviewed profile pins **MuJoCo 3.3.0**, and later releases can change simulation
settling. Record the exact final Python/Torch/renderer stack.

Full K1 benchmarking uses a different LIBERO-Pro source in its docs. We only use
K1 geometry inside our RPent environment for E3. Do not install K1's training
extras or its full alternative simulator into the same venv without checking
compatibility.

## 7. Establish the model and its actual identity

RPent recommends this public checkpoint for its own quickstart:

https://huggingface.co/RLinf/RLinf-Pi05-LIBERO-130-fullshot-SFT

That is **not yet confirmed as DynaHarness's checkpoint**. Using it creates a
valid separately labeled local experiment, not exact reproduction. Determine
the intended checkpoint, record the Hugging Face revision, and download only
needed inference files. One possible RPent-profile setup is:

```bash
hf download RLinf/RLinf-Pi05-LIBERO-130-fullshot-SFT \
  --exclude optimizer.pt --local-dir checkpoints/pi05
python scripts/fingerprint_checkpoint.py checkpoints/pi05 \
  --output local/checkpoint_manifest.json
export PI05_CHECKPOINT_PATH="$PWD/checkpoints/pi05"
```

The download command should additionally use the exact chosen HF revision. Fill
`checkpoint_id` with ID plus revision and `checkpoint_sha256` with the resulting
file-manifest hash in local copies of the templates. The adapter rejects the
placeholder values before native policy evaluation.

A shared RPent VLA server can be launched explicitly in another terminal:

```bash
python external/RPent/rpent/robots/components/pi05_vla_server.py \
  --embodiment libero --transport http --host 127.0.0.1 --port 8911 --cuda-device 1
```

Do not use `--parent-watch` for a foreground manually managed server; RPent uses
that flag with a parent-owned stdin pipe. Adjust GPU indices for the actual
host. A single GPU may fit the chosen stack, but memory feasibility is untested;
do not assume the user's old 2×4090 allocation is still available or free.

Retain server startup metadata and checkpoint evidence. A label in the client
configuration alone does not prove the server loaded the intended weights.
Current policy RNG seed control is not exposed by our adapter. The manifest's
`policy_seed` labels repeats but does not seed native policy sampling.

## 8. Catalog exact states before making experiment manifests

```bash
mkdir -p local
python run.py catalog --rpent-root external/RPent --output local/states.json

# Small development examples; choose task coverage after catalog inspection.
python run.py manifest --catalog local/states.json --split dev \
  --states 0 --tasks 0 1 2 --output local/dev.json

# Example independent pilot: 4 suites × 10 tasks × 2 states, when available.
python run.py manifest --catalog local/states.json --split test \
  --states 1 2 --output local/test80.json
python run.py check-splits local/dev.json local/test80.json
```

These commands use **official stored-state indices**, not newly sampled states
from the paper. They refuse missing indices. `catalog` reads trusted benchmark
state archives; do not load arbitrary untrusted pickle/PyTorch files.

For the website's development labels 21–40, first verify the full paper's state
semantics and available files. Do not guess that all forks share the same state
content just because the suite names match.

## 9. Native qualification before benchmark spending

First run a no-model one-action smoke. The helper
`python scripts/make_native_smoke.py --catalog local/states.json` creates both
the one-case smoke manifest and its local configuration. Alternatively, make a local copy of
`configs/e2_dynamic.template.json`, change `enable_policy` to false, and set:

```json
{
  "kind": "command",
  "command": ["python", "examples/hold_planner.py"],
  "timeout_s": 30
}
```

Use a one-case `smoke` manifest, `max_steps: 10`, `max_decisions: 2`, and a new
output directory. This trusted smoke responder performs one zero-translation,
open-gripper action and then requests finish. Its failure to achieve the task
is expected; it tests only reset/render/control/archive behavior.

```bash
python run.py run --config local/native-smoke.json \
  --manifest local/smoke.json --output runs/native-smoke --allow-native
```

Inspect RGB, depth/calibration, recorded state identity, action scale, gripper
convention, exact step count, terminal handling, video completeness and cleanup.
Next qualify one small free-space target movement, and only then a policy chunk.
Manually inspect camera projections against visible surfaces. A successful Python
import or a rendered image is not a controller qualification.

**Stop after the first infrastructure failure.** The default runner records the
failed case and leaves the rest missing; it does not burn through the whole
manifest or silently count startup failures as task failures. Fix the integration
cause and start a clearly named new run, preserving the negative evidence.

## 10. Connect a real semantic model

### API route

Provide credentials privately, not in repository JSON:

```bash
export PRL_MODEL='exact-model-id-on-your-provider'
export PRL_BASE_URL='https://your-provider/v1'
# Set PRL_API_KEY in your private environment/secret manager.
python run.py run --config local/e2.json --manifest local/dev.json \
  --output runs/e2-dev --allow-native --allow-api
```

The endpoint must support image inputs and function tools. HTTPS is required
except loopback. No endpoint/model fallback, automatic retries, proxy inheritance
or silent substitutions are performed. Provider-specific reasoning options may
be supplied under `extra_request`, without overriding messages/tools/token caps.
The published Qwen family name is not a tested local serving recipe; select and
qualify an exact model revision and server implementation.

Each experiment has one durable API call/token-reservation ledger. Defaults are
small enough to stop before a large evaluation completes. Raise them only after
measuring native pilot consumption and receiving the user's budget approval.
The reservation estimate is not an exact tokenizer or dollar meter. Unknown
usage remains held. Provider errors, malformed replies and unresolved requests
are preserved rather than retried. Cross-process campaigns need explicitly
allocated sub-budgets; copying the same ceiling to every worker multiplies it.

### External Codex file route

Use `configs/e2_file_planner.template.json`. A pending request contains context,
image paths/hashes, the capability catalog and a request hash. The runtime writes
the request directory into that turn's `queue.json`. Directory names include an
output-path namespace so paired runs do not accidentally consume each other's
responses.

Codex writes:

```json
{
  "request_sha256": "copy the request hash exactly",
  "proposal": {
    "capability": "measure_pixel",
    "arguments": {
      "camera": "agentview",
      "observation_id": "copy current observation ID",
      "pixel": [123, 145],
      "coordinate_space": "pixels"
    },
    "max_steps": 0,
    "decision_summary": "Measure the currently visible target surface."
  }
}
```

The coordinates above are schema examples, not targets for any actual task.
Use original-image coordinates from the current camera. Write to a temporary
file and atomically rename to `response.json`; `examples/respond_once.py` shows
the contract. An expired request must not be reused. This interface makes no
claim about which external Codex model, reasoning budget or version was used;
record that separately for matched experiments.

## 11. Experiment sequence

### E0 — local frozen-policy baseline

Use `configs/e0_frozen.template.json`. No high-level planner is invoked. Original
task text goes to the frozen VLA, and the same total step/terminal envelope is
used. Validate actual task success, not just server responses.

### E1 — fixed capabilities plus nominal planning

Use `configs/e1_nominal.template.json`. Keep one fixed analytic/VLA capability
library and one planner configuration. No dynamic stagnation/substitution.
There are still common numeric/budget guards and command-end EEF checks; this
is not an intentionally broken baseline and not a transcript of paper A2static.

### E2 — same library plus dynamic governance

Use `configs/e2_dynamic.template.json`. Change only the declared governor
condition. Initial states, weights, planner/decoding, sensors, budgets, geometry
conventions and memory remain fixed. Compare:

```bash
python run.py compare runs/e1-test runs/e2-test --contrast governor \
  --output runs/paired-e1-e2.json
```

The comparator rejects mismatches in several key factors, including planner
identity/configuration, capability hash and code hash for a governor contrast.
Do not bypass it to assemble a prettier chart.

### E3 — K1 geometry intervention

```bash
python scripts/bootstrap.py --group k1 --execute
python scripts/install_native.py --k1 --execute
```

Use `dynamic_k1`; keep all other variables fixed. The new catalog contains plane/
axis fitting and the exact K1 backprojection path. Compare using
`--contrast perception`. This evaluates a selective perception extension, not
“K1 reproduced” or the source paper's full 18/180-case settings.

### E4 — one failure-directed capability revision

Only after real useful action: inspect failure records, modify one capability,
run paired **development** cases and a broader regression set. Use:

```bash
python run.py attribute runs/e2-dev
python run.py gate runs/e2-dev runs/candidate-dev \
  --policy-reference runs/e0-dev --output runs/admission.json
```

The gate does not change files or deploy code. The output is a review artifact.
There is no live skill generator in this version. Do not use test data to decide
which edit to keep and then advertise the same test set as unseen.

Do not start with multiple simulators. LIBERO-Plus, RoboCasa or harder tasks are
later options after the first result is sound. K1 and RPent already provide
possible adapters, but their task/controller dependencies differ.

## 12. Reporting and speed

A native result packet should include full planned N, successes, failures,
missing cases, infrastructure errors, per-suite results, paired exclusive wins,
uncertainty, native steps, simulated seconds, wall seconds, planner and policy
calls, and governor intervention counts. Include exact config/source/environment/
state/model fingerprints and representative videos, including a failure.

The HTML report is generated from the event/result artifacts. Reproducibility
hashes detect accidental edits, not an adversary replacing the entire evidence
store. Keep raw archives and server logs as well.

Do not report synthetic fixture rates as robotics results. Do not compare an
E0 frozen-policy experiment with an E2 system and call that an isolated governor
gain: E2 adds a planner and alternative physical capabilities. Do not equate
native benchmark success with robust release, real-world safety or industrial
reliability. Additional post-release stability checks are a separate diagnostic.

Native and wall time are different. The current adapter prioritizes correct
per-action interception over RPC throughput, and recording/sensor conversion
adds overhead. Measure before optimizing. One possible later improvement is a
worker-local governed chunk interface, but never restore opaque uninterruptible
chunks merely to obtain a faster-looking video.

## 13. Where to spend the next engineering hours

1. **Source parity audit:** acquire the full PDF/appendix and authors' code if
   now available; settle checkpoint, capabilities, observation privilege and
   evaluation state details. Keep the local experiment viable even if exact
   reconstruction must wait.
2. **Native bring-up:** qualify environment, cameras and one VLA chunk. Fix only
   demonstrated dependency/interface faults; preserve the pinned setup history.
3. **Useful physical capabilities:** establish one simple success, then one
   articulation/contact skill. The independent library is a starting point,
   not a substitute for the paper's major engineering contribution.
4. **Matched pilot:** freeze and run a predeclared small held-out batch. Report
   the actual result even if E1 ties or beats E2.
5. **One extension:** add K1 measurements or a validated progress metric only if
   failures justify it. Defer self-evolution and model training.

A bounded native qualification failure should produce an actionable report,
not another sprawling architecture. Equally, do not spend hours hiding missing
capability under additional governance. We need useful physical execution first.

## 14. Claim wording for the next meeting

Before native results:

> “I have built a separate, CPU-tested implementation for controlled robotics
> harness experiments, using RPent and K1 interfaces. I am independently testing
> DynaHarness-style execution governance around frozen policies. Native
> performance and exact replication are not yet established.”

After a genuinely matched native pilot:

> “On these specific held-out simulator states, with this fixed policy and
> planner, changing the runtime from X to Y changed success from A/N to B/N and
> changed execution/call costs by the measured amounts. This is an independent,
> preliminary reproduction/extension of prior work, not real-factory evidence.”

The user's broader execution/deployment thesis can remain the motivation.
Manufacturing specialization, a cofounder search, future τ₀ post-training and
commercial deployment should not be presented as already validated by this test.

## 15. Further source links

- RPent docs: https://rpent.readthedocs.io/en/latest/
- RPent native setup: https://rpent.readthedocs.io/en/latest/rst_source/simulators/libero.html
- LIBERO-Pro original source: https://github.com/Zxy-MLlab/LIBERO-PRO
- RPent fork: https://github.com/RLinf/LIBERO-PRO/tree/rpent
- K1 execution semantics: https://github.com/Robo-Harness/k1/blob/main/docs/architecture.md
- K1 evaluation scope: https://github.com/Robo-Harness/k1/blob/main/docs/results.md
- K1 dependency separation: https://github.com/Robo-Harness/k1/blob/main/docs/environments.md
- DynaHarness project source: https://github.com/Denghaoyuan123/Dynaharness_page
- Existing user harness, intentionally untouched: https://github.com/AranKomat/physical-agent-harness
- Existing GPU assembly project, intentionally untouched: https://github.com/AranKomat/adaptive-physical-execution

The archive does not contain either old repository or any private transcript,
credentials, GPU-host address, API ledger, model weights or live physics state.
