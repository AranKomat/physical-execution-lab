# Physical Execution Lab v0.4 — self-contained research handoff

Live execution status: see [EXPERIMENT_PROGRESS.md](docs/EXPERIMENT_PROGRESS.md)
and [the first native pilot report](docs/NATIVE_PILOT_20261002.md). The original
build-host limitations below are historical, not a statement of current results.

**Prepared:** 2026-10-01. **Audience:** an external Codex/research agent with authorized GPU, simulator, model-weight and language-model access. **Status:** implemented and CPU-tested; native integrations remain unqualified.

This handoff supersedes the experiment priorities in K1 Execution Lab v0.3. The old implementation is preserved under `k1lab/` and `run.py`; its documents are archived under `docs/legacy_k1_v3/`. The new multi-benchmark implementation is `k1lab/multibench/` and `run_bench.py`. This is not the earlier privileged-state DynaHarness reproduction and does not reopen the closed EmbodiedSWE GPU-assembly branch.

## 1. Converged objective

Test whether a **generic execution harness** improves useful physical behavior and reduces expensive model calls, without adding task-specific robot scripts, benchmark solution memories or new training.

Use strong frozen models, calibrated controls where available, and a small reusable action interface. Invoke the high-level language model at meaningful boundaries instead of every native control tick. Preserve actual execution feedback, bounded commands, source/observation identity, and within-episode progress. The intended result is a measured success/latency/cost trade-off, not a predetermined leaderboard win.

The current supervisor is **`gpt-6.1-sol` through Responses**, with medium reasoning. **Flex is the default service tier** for active experiments, matching the project operating preference; Standard (`default`) remains an explicit comparison profile. Flex changes serving behavior, not model weights. The code does not automatically change models, reasoning level, tier or provider after a timeout or capacity error. Access to the model/account must be verified on the external host.

### Three research tracks

| Track | Conditions | What the experiment can establish |
|---|---|---|
| RoboDojo, robot-policy-free | Sol direct dense vs Sol direct sparse | Effect of local execution granularity with the same general VLM; no motor-policy training or added demonstrations |
| RoboDojo, practical hybrid | π0.5, Xiaomi R1, G0.5, InternW0-Δ, each motor-only / every-chunk review / sparse review | Whether the same supervision architecture helps benchmark-trained motor policies; policy speed/quality comparisons are a separate factor |
| RoboCasa365 | Xiaomi R1 only vs sparse Sol; every-chunk Sol as control | Incremental benefit of supervision over the same strong XR1 checkpoint and native evaluation configuration |

K1/LIBERO remains a useful low-cost regression and later transfer track. No FLUX DROID retargeter was added: single-Franka/DROID camera and joint conventions do not match dual ARX-X5, and they do not automatically match RoboCasa365's mobile action space either.

## 2. Scientific contract

**Allowed:** current RGB, robot proprioception, robot-only FK, actual controller receipts, original task instructions/public task requirements, current-episode history, bounded local motion, and the explicitly named frozen motor policy. The OpenAI supervisor is a general model; its pretraining contents are not audited by this package.

**Not allowed for the main claim:** cross-episode solution traces, target-task exploration memories, demonstrations added as few-shot examples, hidden simulator object transforms, target coordinates extracted from scoring code, reward/partial-score queries to guide the actor, hypothetical future contact rollouts, or task-specific code written after viewing held-out failures. No weights are updated here.

Native tasks whose instruction inherently includes an in-scene demonstration are a distinct case: their original sensor stream remains part of the task. “No added demonstrations” does not mean deleting the observation required by an imitation task.

Benchmark-specific motor post-training is **not automatically cheating**, but it must be labeled. RoboDojo π0.5/Xiaomi/G0.5/Intern checkpoints are not evidence that the motor model transfers cold to every task. Report the robot-policy-free and trained-motor tracks separately.

The new direct baseline is an independently implemented, matched Sol baseline. It is **not** an identical re-run of GPT-as-Policy's Astra/xhigh/Codex workflow. Its published 26%/48% and partial-score numbers are historical references, not measurements generated here. A switch to Sol, a different camera contract, a new motor policy, or a new controller is not a harness-only improvement.

## 3. Architecture and actual implementation

```text
native observed state + original instruction
                ↓
optional frozen policy → observation-bound action proposal
                ↓
local validity/event monitor + periodic semantic review
                ↓
accept / shorten / bounded correction / unsuccessful stop
                ↓
one actual native control acknowledgement at a time
                ↓
update motor-policy observation history → compact receipt
                ↓
review again at a deadline, stage/event boundary or failure
```

`types.py` keeps `x5_joint14`, `x5_eef16_wxyz` and `robocasa12` distinct. Proposals bind the observation stamp, native step, policy identity and declared native frequency. The stamp hashes actual RGB, instruction and robot measurements; it is **not** a full physics-state checkpoint or an across-episode identity.

`runner.py` owns a single fresh episode, sends native actions one at a time, processes terminal acknowledgements, discards unused actions, and updates a stateful policy only after an actual step. It archives full policy proposals, controller receipts and decision-boundary RGB/proprio captures. Sensor NPZs are lossless; JPEGs are review previews. No unknown physical write is retried. Native termination, model stop, wall/model budget exhaustion, and infrastructure/contract failures remain distinct.

`governor.py` handles numerical validity, repeated low robot motion, gripper-command changes, optional sensor flags and periodic review. Defaults cap unreviewed execution at 50 native steps or four chunks. These are **new experiment defaults**, not a claim to reproduce a paper's thresholds. Gripper command changes are review events, not attachment evidence.

**A cheap monitor cannot reliably detect semantic mistakes.** Smooth valid movement may be aimed at the wrong object. Therefore periodic GPT review is retained even when no numerical fault appears. Whitelisted tracking/contact flags have no magical source: the current RoboDojo adapter does not generate a general object-state or grasp-success estimator.

`actor.py` gives Sol current images, a previous-segment image set, recent compact review records, retractable progress claims, robot measurements and sampled proposal/FK information. The gate separately evaluates the previous execution outcome and the next proposed intent. Hybrid correction requires reported failure or misaligned intent; uncertainty alone can shorten observation intervals but does not justify an arbitrary takeover. Evidence text is a model claim, not a verified certificate.

The supervisor emits bounded **action parameters**, not just a choice of tool. RoboDojo corrections are dual-arm absolute EEF targets; RoboCasa corrections are arm-only normalized controller commands. Direct sparse can hold a target for a longer local execution horizon or submit a bounded sequence. This is not a new task-specific manipulation library.

`transport.py` supplies a separate loopback policy process, single-owner/sequence checking, request/response hashes, no implicit mutation retry, explicit reset/invalidate, and exact observation acknowledgements. This is a research interface for trusted hosts, not an Internet-facing authenticated service or adversarial sandbox.

## 4. Source-backed native interfaces

### RoboDojo environment

The adapter uses GPT-as-Policy's existing single-owner native RPC and its real RoboDojo task setup. It does not implement replacement toy tasks. The source simulator must register native completion conditions before the episode: empty condition lists can otherwise produce vacuous success.

The source exports three RGB cameras, measured arm joints and EEF poses. X5 gripper values are **commands**, not measured finger gaps. There is no exported depth/calibration bundle in this donor interface. K1-style RGB-D localization, surface fitting, active perception and grasp hypotheses have **not been ported to RoboDojo in v0.4**. The first experiment isolates execution scheduling under RGB; adding depth later changes the sensing condition and requires its own comparison.

X5 joint action order: left six joints, left opening, right six joints, right opening. Opening is continuous 0=closed, 1=open. EEF poses are each arm's link6 in shared environment-origin coordinates, metres and **wxyz** quaternion. Do not use DROID pad offsets or confuse these poses with K1's xyzw convention.

The native donor's DLS recomputes after every real ACK. Its internal incremental caps remain unchanged. Our EEF boundary normalizes a supplied near-unit quaternion and includes both the source-required boolean closure flag and the continuous opening value. This normalization is coordinate hygiene, not learned control.

The donor FK API requires exactly 50 joint targets. For G0.5/Intern or other exposed horizons, the adapter evaluates blocks through that pure robot-FK API and pads only its input with repetitions of the final existing target. It drops padded outputs. **No padded action is executed, counted as a policy prediction, used as a recurrent ACK, or presented as a predicted physical future.** Preview timing is separately recorded.

### Four RoboDojo motor candidates

| Provider | Actual interface used | Source defaults retained | Qualification issue |
|---|---|---|---|
| π0.5 | Donor OpenPI/JAX client | H50 joint14; execute at most15 | Exact checkpoint/normalizer and source-server identity must match |
| Xiaomi R1 | XPolicyLab Model; source decodes relative predictions to absolute dual EEF | Leading30 actions, processor/image config from source | Current bridge executes EEF via donor DLS: a controller variant, not the original native EE evaluator |
| G0.5 | XPolicyLab Model, FM path | `action_steps=16`, model config frequency30 | Native donor currently25Hz; the model's frequency setting is not measured inference speed. Qualify timing contract explicitly |
| InternW0-Δ | XPolicyLab stateful WAM adapter | H32 model, exposed10 actions, 10 denoise steps,25Hz | Must acknowledge every actual action; interrupted queue reset loses temporal context |

π0.5 source identity:

```text
configuration: pi05_base_aloha_full_sim_arx-x5_seed_0
normalizer: arx_x5_sim
checkpoint: RoboDojo-sim-arx_x5-joint-0/59999
```

The complete artifact manifest hash and the π0.5 server's native checkpoint hash have different scopes. Keep both; do not declare them equal. The source Pi05Client also expects a fresh identified server when first constructed. Its inference sequence persists during that client lifetime.

Xiaomi's source RoboDojo adapter already handles MiBot-to-simulator frames and restores absolute EEF targets. Do not apply the conversion a second time. The DLS bridge is useful for a matched internal Xiaomi-only/every-chunk/sparse experiment, but original XPolicyLab native EE qualification is needed before claiming source-score reproduction. This limitation is prominent because controller choice can change apparent motor competence.

Intern's source `.update_obs()` consumes pending execution acknowledgements. The wrapper delivers each native frame once, deduplicates the same observation before a new proposal, rejects missing ACKs, and resets the source session when a prefix is abandoned. G0.5's temporal buffers reset on intervention too. `policy_invalidation_requests` counts calls to this boundary; it does not assert that every provider physically reloads weights. Stateless π0.5 and RoboCasa history-backed inference do not need the same reset behavior.

Do not choose the “fastest” policy from model size, denoising count, the frequency YAML key, or historical leaderboard scores. Measure it. DM0.5, OpenWAM, RoboDawn and RoboICL remain possible later reference conditions, not implemented additional policy backends.

### RoboCasa365 and Xiaomi

Use **`XiaomiRobotics/Xiaomi-Robotics-1-RoboCasa365`**, not its RoboDojo or original RoboCasa checkpoint. The integration imports Xiaomi's actual `eval_robocasa365/entry.py` helpers and `EvalClient`, preserving input processing and official action conversion.

Pinned source reference: `split=pretrain`, `task_set=target50`, 50 trials/task, base seed7, observation history4 sampled at interval2, crop0.95, execute16 actions/query. The released reproduction guide reports 1432/2500 (57.28%), distinct from the commonly quoted 57.4%. This package makes no attempt to reconcile that difference or invent a new official score.

`target50` names the task set. It is **not** the `target` kitchen/object split. Composite-unseen task categories and kitchen splits are also different axes. Changing either is a new condition. Category labels remain `unmapped` until obtained from the actual task registry; they are not guessed from task names.

The state helper builds EE-first14 dimensions, which the official client pads to60. The output is12 controller values: arm translation/rotation, gripper, base/torso and control mode. They are not absolute world XYZ positions. Current teacher corrections keep base motion zero and use fixed arm mode with bounded normalized arm inputs. General mobile-base recovery is not implemented.

History receives every actual observation, including after teacher corrections. Source16-action replanning and queue discards are retained; source processing is not replaced with a “similar” custom encoding. Native termination uses the official environment success signal. No fabricated RoboDojo-style partial score is assigned to RoboCasa.

## 5. Repository map

| Path | Purpose |
|---|---|
| `run_bench.py`, `k1lab/multibench/cli.py` | New experiment commands |
| `types.py`, `runner.py`, `governor.py`, `actor.py` | Bound actions, sparse loop, review gate and model interface |
| `adapters/robodojo.py` | Source native RPC, joint actions, local DLS and FK preview |
| `adapters/xpolicylab.py`, `adapters/pi05.py` | Three newer policy wrappers plus source π0.5 client |
| `adapters/robocasa.py` | Native RoboCasa and official Xiaomi preprocessing/client |
| `transport.py`, `latency.py` | Separate model service and recorded-input latency tests |
| `manifest.py`, `report.py` | Identity, held-out splits, freezes, qualification, reporting |
| `configs/multibench/` | 17 conditions, five provider templates, Standard/Flex profiles |
| `scripts/multibench/` | Launch/capture, bind policies, plan matrix, export inputs, fingerprint, plots |
| `tests/multibench/` | New CPU protocol, adapter-double and reporting tests |
| `run.py`, other `k1lab/` files | Preserved K1/LIBERO experiments |

## 6. CPU bring-up

```bash
cd physical-execution-lab
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test,multibench]'
python -m pytest -q
python run_bench.py doctor
python run_bench.py synthetic --output runs/cpu-check
python scripts/verify_release.py
```

Open `runs/cpu-check/report.html`. Its 15 authored toy episodes exercise five conditions on three fixture cases. There are no learned models or contact dynamics. Success is part of the fixture, not a result about robotics. The plotting helper uses actual aggregate files and visibly labels synthetic plots:

```bash
python -m pip install -e '.[plots]'
python scripts/multibench/plot_results.py --report runs/cpu-check --output runs/cpu-plots
```

Do not include those plots in a performance pitch.

## 7. Install sources and prepare real artifacts

Source bootstrap is explicit and downloads no model weights or task assets:

```bash
python scripts/bootstrap.py --group robodojo --allow-network
python scripts/bootstrap.py --group robocasa --allow-network
# Only when working on the retained K1 path:
python scripts/bootstrap.py --group core --allow-network
```

Pins identify expected interfaces, **not** a universal Python/CUDA/Isaac lock. Use separate environments for Isaac/RoboDojo, each motor policy, RoboCasa's simulator/client, and Xiaomi's server. Follow upstream installation guides; do not install incompatible simulator/model pins into one environment. Native environments can install this package with `pip install -e . --no-deps` after their own dependencies are qualified. Read the source README before initializing submodules or downloading licensed assets.

Configure copies of the templates under `configs/local/` with absolute source/model locations. The provider templates contain intentionally invalid `/ABSOLUTE/PATH/...` placeholders and null weight identities. Do not replace them with invented hashes.

For each provider, include weights, processors, normalizers and relevant model configurations under a clearly scoped artifact root:

```bash
python run_bench.py hash-artifacts --root /path/to/provider-artifacts \
  --output /path/to/provider-artifacts-manifest.json
```

Store the manifest **outside** the hashed directory. Point `artifact_manifest` in the provider and experiment configs to it. Model files must stay fixed. Hash all ancillary assets, not merely the small final checkpoint.

For remote RoboDojo policies, bind the actual provider configuration to the experiment identities:

```bash
python scripts/multibench/bind_policy.py \
  --provider-config configs/local/pi05-provider.json \
  --experiments configs/local/robodojo_pi05_motor_only.json \
                configs/local/robodojo_pi05_review_every_chunk.json \
                configs/local/robodojo_pi05_sparse.json \
  --output configs/local/pi05-bound
```

This writes new files, including `provider.json`. Its identity covers actual artifact contents and provider settings, so changed denoising/preprocessing settings cannot silently masquerade as the same policy server. For XPolicyLab providers, initialize from the corresponding five-provider template and use a separate bound directory.

Start one provider in its own prepared policy environment:

```bash
python run_bench.py serve-policy --config configs/local/pi05-bound/provider.json \
  --port 19600 --allow-policy
```

π0.5 additionally needs the donor's OpenPI server listening on its configured port; inspect `python -m hybrid_rollout.robodojo.pi05_server.server --help` in the correct JAX environment and follow the upstream launch guide. Intern/G0.5/Xiaomi load through their source Model implementations in their own interpreter. G0.5 changes working directory internally; use absolute paths. Do not concurrently share one mutable policy session between episodes. The local service only accepts one owner.

## 8. Select cases without importing solutions

RoboDojo import reads the donor's `public_results/evaluation_cases.json`, retaining only task/scene/seed identities, limits and timing. It discards reference successes, scores, token totals and solution histories. A source panel supplies actual layout hashes. The donor panel has60 source entries; the published comparison selects50 of them. Use the panel file that actually contains those selected cases and matches your assets, not a guessed filename.

```bash
python run_bench.py import-robodojo \
  --source-results external/GPT-as-Policy/public_results/evaluation_cases.json \
  --source-panel /path/to/verified-source-panel60.json \
  --output configs/local/robodojo-cases.json
```

The importer groups variants/layouts of the same task together before assigning development/test. This prevents calling new seeds of an already optimized task “held-out tasks.” A formal source panel can be generated and checked using the donor `hybrid_rollout.robodojo.evaluation` module against your real assets. Its native-source file hashes must also match. The scripts never manufacture missing layout files.

For RoboCasa, run in the configured simulator/client environment:

```bash
python run_bench.py robocasa-manifest --trials 50 --seed 7 --split pretrain \
  --output configs/local/robocasa365-cases.json
```

This obtains task order and horizons from the installed registry. Episode seed is `7 + task_index * trials_per_task + trial_index`. Generating a one-trial manifest changes this sequence; do not present it as the first trial of the50-trial official matrix. For a small matched pilot, retain the full manifest and select a fixed number of its cases.

## 9. Native bring-up before any expensive sweep

Prepare the RoboDojo source/assets and its IsaacSim5.1/IsaacLab runtime. The launcher below starts a single donor server and the matching controller; it prints the plan by default. It does not reserve GPUs, acquire credentials or deploy to a cluster.

```bash
python scripts/multibench/launch_robodojo_case.py \
  --config configs/local/pi05-bound/robodojo_pi05_motor_only.json \
  --manifest configs/local/robodojo-cases.json --case-id YOUR_DEV_CASE \
  --source-panel /path/to/verified-source-panel60.json \
  --sim-python /path/to/isaac-env/bin/python \
  --robodojo-root "$PWD/external/RoboDojo" \
  --output runs/capture-001 --development --capture-only
# Review the plan, then repeat the command with --execute.
```

Capture-only uses no motor inference, no paid API, and no robot action. It writes a lossless `observation.wire.json` for the speed bakeoff. It is limited to development cases. A capture does not become a successful benchmark episode.

Readiness is taken from the server's stdout `event=ready` message. **Do not connect a TCP probe to test readiness:** the source accepts one controller connection. For a complete development motor episode, omit `--capture-only`, add `--allow-policy --execute`, and use a fresh output directory. For hybrid runs add `--allow-api`, after configuring authorized credentials. `K1LAB_SIM_PORT` and `K1LAB_NATIVE_OUTCOME_PATH` are per-episode operational locators, not algorithm changes.

The launcher cleans up only its own process groups. Native assets, source revisions, renderer/driver availability, JAX/Torch inference and real controller tracking have not been tested here. Startup failures must be fixed before evaluation, not hidden by resetting until a case works.

For RoboCasa, first run Xiaomi's native smoke command from its evaluation README. Then our runner is direct:

```bash
python run_bench.py run-case --config configs/local/robocasa365_xiaomi_motor_only.json \
  --manifest configs/local/robocasa365-cases.json --case-id YOUR_DEV_CASE \
  --output runs/rc-pilot --development --allow-native --allow-policy
```

The official Xiaomi server must already be running; its checkpoint path must be readable by the official client. Do not change the kitchen split, camera crop/history or normalization merely to make the pilot easier.

## 10. Experiment sequence and stopping rules

**Stage A — qualify execution.** Reset/render one development case with native conditions installed. Verify robot FK against proprioception, camera order, quaternion convention, gripper semantics, native step accounting and actual motor action. Test one complete episode. For Xiaomi RoboDojo, explicitly compare DLS execution with the source EE path. Stop a broken adapter rather than spending GPT tokens to compensate for it.

**Stage B — policy speed/quality screen.** Test all four RoboDojo candidates on the same hardware and recorded observations, with warmup separated from timed calls:

```bash
python run_bench.py latency --config configs/local/pi05-bound/policy-remote.json \
  --observations runs/capture-001/observation.wire.json \
  --warmup 3 --repeats 30 --output runs/pi05-latency.json --allow-policy
```

For this command the config is the **policy object alone** from a bound experiment, not its full experiment JSON. `bind_policy.py` writes this policy-only file automatically. The independent-observation timing resets temporal memory and labels that fact. It is not a measurement of steady-state WAM execution. Warm p50/p90/p99, load time when available, VRAM and nominal milliseconds per exposed action are diagnostics; complete native episodes determine the actual trade-off.

Replay observations may also be exported from a runner capture:

```bash
python scripts/multibench/export_observation.py \
  runs/episode/controller/observations/000000 --output runs/input.wire.json
```

Run5–10 native development cases per candidate after interface checks. Keep failures. Select one or two useful policies based on complete-episode success and measured time, not a speculative architecture ranking. There is no requirement that a heavier policy lose: fewer failed grasps or fewer supervisor interventions can outweigh inference latency.

**Stage C — matched harness comparison.** For each retained policy run motor-only, every-chunk review and sparse review. Keep weights, policy-source preprocessing, sensors, native controller, action horizons, task cases and model tier fixed. Also compare Sol direct dense vs direct sparse without a motor model. Changes to reasoning effort or serving tier are their own factor.

**Stage D — RoboCasa365.** Qualify the official XR1-only baseline, then compare sparse Sol, optionally every-chunk Sol. Begin with a preregistered balanced subset. Full target50/2500 evaluation is downstream of native bring-up and budget review. Re-check live submission rules before any leaderboard claim; they are not automatically validated by this repository.

**Stage E — sensing/transfer extensions.** Only after useful physical results: port K1 calibrated RGB-D/geometry into RoboDojo, add generic observation-driven sensing, or transfer across benchmark/embodiment. Additional depth is a sensor/tool intervention, not an unchanged-input runtime result. Distillation, training, task-specific skill synthesis and FLUX retargeting are out of scope today.

## 11. Freeze and qualification

Generate an initially **unapproved** qualification record:

```bash
python scripts/multibench/qualification_template.py \
  --config configs/local/experiment.json --output configs/local/qualification.json
```

Fill it only after real tests, attaching actual evidence paths and SHA256s. It checks source/config binding, reset/render, action conventions, nonvacuous native completion, legal actor input, policy ACK semantics and native timing. It is an operator-reviewed evidence gate, not automatic proof of robot safety.

After development, freeze source, manifests and resolved configurations:

```bash
python run_bench.py freeze --manifest configs/local/robodojo-cases.json \
  --configs configs/local/pi05-bound/robodojo_pi05_review_every_chunk.json \
            configs/local/pi05-bound/robodojo_pi05_sparse.json \
  --output configs/local/freeze.json
```

A scored `run-case` requires `--freeze` and the corresponding `--qualification`, and does not use `--development`. Any source or resolved configuration edit requires a new experiment/freeze. `plan_matrix.py` writes deterministic jobs and maximum model-call/output-token reservations without executing them. Those reservations are **not a dollar budget**. Review total account/compute limits before handing a matrix to a scheduler.

## 12. Metrics and truthful comparisons

Record native success, separately available partial score, task-weighted and episode-weighted rates, missing/error/censored counts, native control steps and simulated seconds, wall time, model requests, cached/uncached input, output/reasoning tokens, policy calls, corrections, interruptions and invalidations.

Timings separate environment stepping, policy blocking calls, ACK transport, robot-FK preview and supervisor waiting. Warm episode elapsed time excludes initial model-server loading and initial server startup; those have separate records. Simulation is paused while the model is thinking in these interfaces. This is **not** evidence of real-time performance with moving real-world objects.

Cached tokens are not free computational work, but neither are they priced like uncached input. Reasoning tokens are a subset of output tokens and must not be added twice. Missing usage fields remain null. Unknown API responses retain output reservations and are not silently retried. Token caps and request-byte caps do not provide a complete dollar guarantee.

```bash
python run_bench.py report --manifest configs/local/robodojo-cases.json \
  --runs runs/eval --partition test --output reports/robodojo \
  --conditions robodojo_pi05_review_every_chunk robodojo_pi05_sparse \
  --baseline robodojo_pi05_review_every_chunk --candidate robodojo_pi05_sparse
```

Missing runs stay in the success denominator. Partial-score means show coverage instead of replacing unavailable scores with zero. Timing means disclose available-run coverage. Paired comparisons detect differing policy/model/environment identities and bootstrap by task group. Hardware/runtime and actual served-model records must be checked by the external agent as well; hashes cannot prove a methodology is fair.

Choose a success-vs-wall-time plot and a success-vs-model-calls plot from actual runs. A speed gain with many more failed or early-abandoned episodes is not automatically an improvement. Sparse execution may reduce calls but hurt recovery; negative results should remain visible.

## 13. Sources and pinned revisions

Full source pointers are also in `docs/multibench/SOURCES.md` and `upstream.lock.json`.

- [GPT-as-Policy](https://github.com/anonymous-report-421/GPT-as-Policy/tree/8f3d362b077d8efb77e2a7274d5b2c20e2243846): native RoboDojo server/session, robot FK/DLS, π0.5 client, paired case identity, outcome/intent gate.
- [XPolicyLab](https://github.com/XPolicyLab/XPolicyLab/tree/408b99d959a7b2207f5f785528fefcc019d7b131): `policy/G05`, `policy/Xiaomi_Robotics_1`, `policy/InternW0_delta` source contracts and model loaders.
- [Xiaomi R1](https://github.com/XiaomiRobotics/Xiaomi-Robotics-1/tree/0dd7aef8dc87296246aae812a1f59ccb708e5546): `eval_robocasa365/README.md`, `entry.py`, official client/server setup.
- [RoboCasa](https://github.com/robocasa/robocasa/tree/456174f62b89b8fca99eaaf33949c29fec9cfc2a): native registry, Gym wrapper and `convert_action`.
- [RoboDojo](https://github.com/RoboDojo-Benchmark/RoboDojo): donor records `ee67a1468510da7624a089164402359f2afc72c8`; assets/submodules must be obtained separately.
- [RoboDojo data/checkpoints](https://huggingface.co/datasets/RoboDojo-Benchmark/RoboDojo), [G0.5 RoboDojo](https://huggingface.co/OpenGalaxea/g05-robodojo), [InternW0-Delta RoboDojo](https://huggingface.co/InternRobotics/InternW0-Delta-RoboDojo), [XR1 RoboCasa365](https://huggingface.co/XiaomiRobotics/Xiaomi-Robotics-1-RoboCasa365).
- [K1](https://github.com/Robo-Harness/k1/tree/ee46363101fcf3ef87182fb2dbad99a92ce77fc0), [RPent](https://github.com/RLinf/RPent/tree/d2595ff270c7d66dbb2effb803f5e6d4d8e08f82): retained prior integration/reference.
- [GPT-6.1 Sol documentation](https://developers.openai.com/api/docs/models/gpt-6.1-sol), [Flex processing](https://developers.openai.com/api/docs/guides/flex-processing).
- [RoboCasa live rules/results](https://robocasa.ai/leaderboard.html), [RoboDojo](https://robodojo-benchmark.com/), [RoboICL](https://github.com/Mosi-AI/RoboICL), [RoboDawn](https://github.com/Hugo-AGI/RoboDawn): reference/discovery, not rerun results in this archive.

## 14. Build-host limits and next deliverable

Source interfaces were inspected through the GitHub connector; direct upstream clones/downloads were not possible on the build host. No GPU model or simulator was available. Unit tests use explicit doubles, not silently mocked native runs. The release includes code, source pins, configuration templates, CPU evidence and tests, but not external assets, weights, credentials or fonts.

The next deliverable should be **one auditable native pilot per viable interface**, a small speed screen, and then a frozen paired result. Do not write another broad platform before obtaining those physical observations. Preserve the original K1/BEHAVIOR work and unrelated remote processes.
