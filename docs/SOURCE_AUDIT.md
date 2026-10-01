# Source audit — 2026-10-01

This audit distinguishes inspected source from assumptions. Source was read through the GitHub connector. Direct GitHub cloning failed on the build host because network name resolution was unavailable. No upstream repository is vendored or claimed to have run here.

## K1: primary runtime and perception substrate

Repository: https://github.com/Robo-Harness/k1

Pinned revision: `ee46363101fcf3ef87182fb2dbad99a92ce77fc0`

Inspected sources at that revision:

- https://github.com/Robo-Harness/k1/blob/ee46363101fcf3ef87182fb2dbad99a92ce77fc0/src/robo_harness/runtime.py
- https://github.com/Robo-Harness/k1/blob/ee46363101fcf3ef87182fb2dbad99a92ce77fc0/src/robo_harness/position_reach.py
- https://github.com/Robo-Harness/k1/blob/ee46363101fcf3ef87182fb2dbad99a92ce77fc0/src/robo_harness/libero_adapter.py
- https://github.com/Robo-Harness/k1/blob/ee46363101fcf3ef87182fb2dbad99a92ce77fc0/src/robo_harness/pose_targets.py
- https://github.com/Robo-Harness/k1/blob/ee46363101fcf3ef87182fb2dbad99a92ce77fc0/src/robo_harness/grasp_geometry.py
- https://github.com/Robo-Harness/k1/blob/ee46363101fcf3ef87182fb2dbad99a92ce77fc0/src/robo_harness/grasp_presentation.py
- https://github.com/Robo-Harness/k1/blob/ee46363101fcf3ef87182fb2dbad99a92ce77fc0/src/robo_harness/tracked_points.py
- https://github.com/Robo-Harness/k1/blob/ee46363101fcf3ef87182fb2dbad99a92ce77fc0/docs/environments.md
- https://github.com/Robo-Harness/k1/blob/ee46363101fcf3ef87182fb2dbad99a92ce77fc0/docs/architecture.md

### Consequences for implementation

`run_agent` already accepts `registry_class`, `client_factory`, and `request_options`. The new code uses the first two, preserving K1's full prompt, original tool definitions, RGB-D tools, episode history, tracked points and archives. The original registry is used for `k1_baseline`.

`move_toward` already performs multi-tick absolute-position servoing with a 120-step budget, 24-step non-progress limit, approximately 3 mm position tolerance and 2-degree orientation tolerance. `move_to_pose` is different: a bounded incremental step toward a persistent SE(3) target. Neither is a general collision-free planner. The extension therefore does not claim that local control, stale-frame checks or task-success stopping were absent from K1.

K1's LIBERO adapter provides metric depth, intrinsics/extrinsics, proprioception and **robot-only** geometry. RGB-D actor images are vertically flipped from the raw renderer. Scene object poses, hidden collision fixtures, object instance masks and benchmark target geometry must not be exposed.

Grasp output has `candidate_id`, `pregrasp_tcp_world_m`, `candidate_tcp_world_m` and `target_quaternion_xyzw`. The extension caches those exact sensor-derived outputs. It does not introduce a simulator grasp oracle. K1's geometric candidate generator targets a currently visible region with a reliable long axis; it is not an arbitrary-object grasp solution. The learned GraspGen service is optional and requires its own calibration.

Tracked-point evidence contains a current frame and may become `lost_remeasure`. An old XYZ is not current just because it is still stored. Co-motion must account for hand rotation; even good co-motion does not establish semantic identity or certify attachment.

### Dependency split

K1's documented LIBERO backend expects Zxy-MLlab/LIBERO-PRO revision `eafdb809426b13153aa1e4c42d6601844217dfec`, using the single-controller RoboSuite 1.4 API. Its RoboSuite transfer backend instead refers to RATs/CaP-X and RoboSuite 1.5.1. These are not one interchangeable environment.

## RPent: optional policy-serving donor, not task memory

Pin: `d2595ff270c7d66dbb2effb803f5e6d4d8e08f82`

- https://github.com/RLinf/RPent/blob/d2595ff270c7d66dbb2effb803f5e6d4d8e08f82/rpent/robots/components/pi05_vla_server.py
- https://github.com/RLinf/RPent/blob/d2595ff270c7d66dbb2effb803f5e6d4d8e08f82/rpent/robots/components/pi05_vla_client.py
- https://github.com/RLinf/RPent/blob/d2595ff270c7d66dbb2effb803f5e6d4d8e08f82/rpent/utils/rpc/client_utils.py
- RLinf image conventions: https://github.com/RLinf/RLinf/blob/88f9867ff5b3004b482d6788a871081a43098620/rlinf/envs/sim/libero/utils.py

`Pi05VLAFacade(model_path=..., embodiment='libero')` loads the actual model and predicts batched actions. The inspected LIBERO preset selects **five** action chunks, not DynaHarness's ten. This experiment is not claiming DynaHarness protocol reproduction.

The RPent policy observation uses RGB rotated 180 degrees, state `[EEF position, axis-angle orientation, two gripper joints]`, and 7D normalized Cartesian OSC actions. The bridge resizes the same raw camera views to 256 pixels; the actor sees K1's 384-pixel frames by default. This resize path is explicit but **not native-qualified** and is not claimed identical to a separately rendered policy camera.

The policy server runs separately from the K1 simulator environment. No RPent memory loader, published exploration corpus, per-task audit or recipe is invoked. Checkpoint training provenance must still be documented: no inference-time memory does not mean the VLA never saw related tasks during training.

Related pins inherited from the previous source audit, to be checked during GPU setup: RLinf `88f9867ff5b3004b482d6788a871081a43098620`; RLinf/openpi `a560f4dd8205b8423ecd4c8a0fabb5f54140b8a0`.

## FLUX: a real compatibility gap, not a placeholder detail

Official sources inspected:

- https://github.com/black-forest-labs/flux-action
- https://github.com/black-forest-labs/flux-action/blob/main/docs/setup.md
- https://huggingface.co/black-forest-labs/flux-3-action-droid

The released DROID policy consumes synchronized wrist/left/right RGB frames and an eight-dimensional joint/gripper state. It predicts 32 absolute joint/gripper targets with eight values per action. The LIBERO integration here is two cameras, EEF proprioception and seven normalized OSC commands. The fact that both use a Franka-family arm does not align cameras, action spaces, rates or normalization.

Therefore `droid_joint8` is deliberately refused by the executable LIBERO policy contract. The offline probe invokes the real documented `flux-action infer` CLI only with a valid recorded DROID observation. It never fabricates a third view or converts joint targets into fake OSC predictions. A future FLUX bridge needs a separately validated embodiment adapter/checkpoint or a different environment.

## Model service

- Responses API: https://developers.openai.com/api/reference/resources/responses/methods/create
- Vision: https://developers.openai.com/api/docs/guides/images-vision
- Flex: https://developers.openai.com/api/docs/guides/flex-processing

The model name is an explicit user parameter. No access to a particular model is assumed. Flex is a price/availability/latency tradeoff, **not a low-latency serving mode**. Our transport records the requested tier and does not silently fall back to another tier or model. There is no special “Decision API” dependency.

## Research references and what they do NOT establish here

- K1: https://arxiv.org/abs/2609.29389
- Harness VLA: https://arxiv.org/abs/2607.08448v5
- DynaHarness: https://arxiv.org/abs/2609.40306v1
- DynaHarness project: https://denghaoyuan123.github.io/Dynaharness_page/
- RPent memory documentation: https://rpent.readthedocs.io/en/latest/rst_source/guides/memory.html
- RPent results/protocol notes: https://rpent.readthedocs.io/en/latest/rst_source/leaderboard/performance.html

Those results use different models, capability libraries, state access, memory and episode sets. They justify questions, not expected scores. We are not reporting their numbers as measurements of this code.

DynaHarness's simulator-state grounding and benchmark-developed contact library are deliberately outside this implementation. We borrow the general discipline of bounded execution, explicit failure evidence and gated experiments. Earlier EmbodiedSWE work motivates sensing/freshness/local-execution ideas, but its assisted grasp/carry branch did not establish a matched Direct-A/Direct-B/FLUX success comparison. Do not present that history as proof that hybrid control won.
