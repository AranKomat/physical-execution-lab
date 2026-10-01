# Source audit — October 1, 2026

## What was actually accessed

The implementation environment could read GitHub text through the connected
GitHub tool. Direct container DNS/downloads failed. ArXiv/project PDF fetches did
not supply a usable full text. The DynaHarness website's actual HTML and result
JavaScript were read through GitHub instead. No upstream repository was cloned
locally, no native package installed, and no GPU/model run executed.

This matters: the earlier conversation contained stronger assumptions than the
primary sources justify. The notes below supersede those assumptions.

## DynaHarness

Paper: https://arxiv.org/pdf/2609.40306
Project: https://denghaoyuan123.github.io/Dynaharness_page/
Alternate PDF: https://denghaoyuan123.github.io/Dynaharness_page/assets/paper_arxiv.pdf
Project source: https://github.com/Denghaoyuan123/Dynaharness_page
Results: https://github.com/Denghaoyuan123/Dynaharness_page/blob/main/assets/js/data.js
Architecture/conditions: https://github.com/Denghaoyuan123/Dynaharness_page/blob/main/index.html
Linked implementation: https://github.com/Denghaoyuan123/DynaHarness

The last implementation URL returned **404** at this check. This does not prove
it will remain unavailable. The project page is not the implementation repository.
Its inspected index.html blob was `7d2f25df583ead7fc8d591a647ac98755890a1e9`.

### Confirmed from project-owned source

- Slow semantic model: Qwen3-VL-4B. Motor family: frozen π0.5. They are not the
  same model. The primary fast-brain implementation is a deterministic rule;
  a learned fast-brain variant is a separate experiment.
- Four evaluation suite groups: Goal-Task, Goal-Swap, 10-Task, 10-Swap; 200 cases
  each in the 800-case aggregates. This is not RPent's eight-suite leaderboard.
- Development block labels 21–40. Its archived bare-policy row is 130/800, and
  the final reported development aggregate is 594/800.
- Fixed-library comparison: A2ctrl 592/800; A2static 511/800. Thus 74.0% versus
  63.9% is a **development-block runtime ablation**, not the new-state test.
- Removing analytic contact skills gives 133/800. Removing the VLA gives
  564/800. The large system improvement is not simply adding a monitor.
- The post-freeze new-state headline is 75.2% versus 17.5%. Its actual new-state
  files and generator were not obtained. Do not relabel stored states 0–19 or
  40–59 as those new states.
- Advertised rates are 20 Hz native controller, 2 Hz fast decisions, 50 Hz safety
  checks, with semantic calls on demand. This repo's per-action checks at 20 Hz
  do not reproduce a separate 50 Hz loop or certified safety behavior.
- The project distinguishes real UR7e/camera experiments from simulator-state
  conditions. The full simulator information contract remains to be audited.
- Their self-evolution uses a 13-layer attribution taxonomy and paired admission
  checks. Our simplified diagnostic taxonomy is NOT its transcription.

### Unknown, not filled in by guesswork

Exact π0.5 checkpoint/revision, exact prompts/decoding, environment/controller
pins, complete analytic/recovery skill implementations, precise observation
privileges, per-task budgets, the new-state sampling protocol, the complete
self-evolution development history, and policy RNG control.

`configs/paper_protocol.json` records these as null until independently checked.
The local native 520-step default is a declared research profile, not a claim of
matching every DynaHarness task budget. The website's examples include multiple
budgets, including 300, 310 and 520.

## RPent / Harness VLA

Repository: https://github.com/RLinf/RPent
Paper: https://arxiv.org/abs/2607.08448
Docs: https://rpent.readthedocs.io/en/latest/
Reviewed commit: `d2595ff270c7d66dbb2effb803f5e6d4d8e08f82`

Key inspected files:
- `robots/libero/robot_spec.py`: simulator/VLA process ownership and connection.
- `robots/libero/env_client.py`, `env_server.py`: reset/step/chunk/RGB-D interface.
- `robots/libero/tools.py`: actual analytic and VLA primitive implementations.
- `rpent/dashboard/events.py`: no-op dashboard event sink.
- `rpent/utils/daemon.py`: owned-process stop behavior.
- `pyproject.toml`: Python/version constraints and native source dependencies.

Specific implementation consequences:
1. The environment maps `--seed` through `% number_of_stored_states`. Our adapter
   validates index bounds and exact state hashes before startup, refusing aliases.
2. Policy-oriented images are not calibration-frame images. We vertically flip
   raw RGB and raw depth together and use matching optical camera metadata.
3. Wrist extrinsics are captured afresh. Never reuse them after arm movement.
4. Upstream primitive heuristics about jaw gap/lift do not prove grasp success.
5. Large single XY transits are warned against upstream; our compositions split
   them in BOTH conditions, which is not a collision-free planner.
6. MuJoCo 3.3.0 is pinned in RPent; the upstream source warns about later versions
   changing settling and success. This repo refuses a silently different version.
7. RPent's benchmark memory and high-performing leaderboard settings are separate
   experimental conditions. Our native adapter bypasses task-specific memory.
8. RPent's default public SFT checkpoint is a candidate, NOT confirmed as the
   DynaHarness baseline checkpoint:
   https://huggingface.co/RLinf/RLinf-Pi05-LIBERO-130-fullshot-SFT

## K1

Repository: https://github.com/Robo-Harness/k1
Paper: https://arxiv.org/abs/2609.29389
Reviewed commit: `ee46363101fcf3ef87182fb2dbad99a92ce77fc0`

Key interfaces actually inspected:
- `src/robo_harness/geometry.py`: calibration(camera), unproject(camera, uv).
- `src/robo_harness/perception.py`: fit_geometry(camera, roi, kind, threshold_m).
- `docs/architecture.md`, `docs/environments.md`, `docs/results.md` (earlier review).
- `pyproject.toml`: core geometry and separate training dependencies.

We call K1's actual unproject/fit_geometry implementations when enabled. We do not
bundle or reproduce its SAM3, TAPNext++, grasp hypotheses, history mechanism,
student training, full actor interface, or published success rates.

K1's documented native LIBERO-Pro source is Zxy-MLlab/LIBERO-PRO at
`eafdb809426b13153aa1e4c42d6601844217dfec`, not the RPent simulator fork used here.
Its matched 18-case frontier comparison and 180-case sweep use different task
coverage from DynaHarness. Their percentages do not belong in a locally matched
comparison table unless each condition is independently rerun under one protocol.

## Attribution and licensing

Our runtime, protocol wrappers, evaluation and tests are independently authored.
Upstream code is imported after a user-controlled bootstrap, not redistributed in
this ZIP. RPent is Apache-2.0; K1 is MIT. Other dependencies, assets and weights
retain their own terms. Review upstream licenses before redistributing assets or
publishing derived software; a source pin is not a licensing conclusion.
