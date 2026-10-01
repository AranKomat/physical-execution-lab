# Implementation status — K1 Execution Lab v0.3.0

## Delivery summary

This is a **new K1-based extension repository**, not an update that silently reuses privileged DynaHarness grounding. The old repositories and packages were left untouched.

The runnable code and CPU tests are included. Upstream sources were inspected through GitHub, but cloning was blocked by the build environment's network. No upstream repositories, simulator assets, model weights or task-memory files are vendored.

## Implemented and CPU-tested

| Area | Implementation and test boundary |
|---|---|
| Generic execution | Closed pose/gripper schema; persistent absolute pose/orientation; one-native-tick executor; bounded speed, horizon, lease, stagnation and workspace checks; no full collision planner. |
| Sparse commands | Up to six generic segments; minimum budget refusal; per-command idempotency and actual partial receipts. |
| Candidate grasp | Actual K1 candidate field contract; fresh frame/arm binding; pregrasp/approach/closure/probe; strict lost/contradictory co-motion handling. Tested with sensor/interface doubles, not native grasps. |
| Evidence | Current tracked points only; rigid hand-motion compensation; explicit supported/contradicted/unknown; no automatic identity/attachment certificate. |
| K1 extension | Uses inspected `registry_class` and `client_factory` seams. Tests inject a contract-compatible base class; actual K1 was not imported on this host. |
| Model transports | Responses and compatible chat translation mock-tested; file queue exercised; trusted subprocess exercised. Actual live API calls: **zero**. |
| Native adapter | Written against pinned K1 LIBERO 1.4 API. Source-inspected, not native-executed. Native reset/render/physics/action tests still required. |
| Policy protocol | Exact checkpoint/action/camera/state contract, loopback HTTP, request binding, no retry, per-action execution and queue discard. CPU HTTP/interface doubles tested. |
| RPent bridge | Calls real inspected `Pi05VLAFacade`; checkpoint-byte manifest and observation encoding implemented. CUDA import/inference and native action alignment **not tested**. |
| FLUX | Recorded DROID observation validator/official CLI probe. **No LIBERO-compatible FLUX execution adapter.** Unsupported joint8 is rejected. |
| Evaluation | Grouped base-task holdout across Task/Swap, BDDL/state hashes, concrete-model freeze, matched signatures, alternating order, full denominator, paired statistics, reporting and optional plot script. |
| Synthetic example | Eight script/kinematic case-condition runs; no K1/VLM/VLA/physics. Deliberately no artificial accuracy improvement. |

## Not implemented or not established

- No native K1, LIBERO, RoboSuite or RoboTwin benchmark result.
- No actual success, latency or generalization improvement over K1.
- No live model, SAM3, GraspGen or VLA inference on this host.
- No training, distillation, learned policy routing or autonomous skill evolution.
- No task-specific exploration memory, oracle scene grounding or per-task skill generation.
- No physical-force sensor, collision-free planning or real-robot safety certification.
- No free-floating inspection camera, new active-perception subsystem or second-environment runner.
- No fully pinned transitive GPU/rendering environment. Upstream commit pins identify expected interfaces, not universal binary compatibility.

## Verification artifacts

`docs/CPU_TESTS.txt` records the complete local test run. `docs/BUILD_HOST.json` records the build environment and absent native/GPU/API qualifications. `runs/cpu-example/` contains synthetic outcomes, receipts, hash-linked journals and the offline report. `RELEASE_MANIFEST.json` lists packaged file hashes; run `python scripts/verify_release.py` after transfer.

A test count proves the tested software invariants only. The external agent must additionally qualify reset, images/depth, controller signs/scales, actual grasps, the policy observation/action bridge, and the selected VLM/provider.

## Recommended next milestone

Run the unmodified K1 registry on **two development cases** with real sensors and the chosen model; then run stepwise and sparse extensions on those same cases. Fix generic integration errors, freeze, and evaluate held-out base tasks. Do not start with a large benchmark sweep, new model training, an industry animation, or another framework rewrite.
