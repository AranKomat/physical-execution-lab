# External Codex takeover — K1 Execution Lab

You are continuing an implementation, not starting a new architecture discussion.

## Objective

Demonstrate a general, memory-free robotics harness improvement: same strong VLM, current RGB-D/proprioception, generic tools, no prior solution for the evaluation task. Improve success and/or reduce model calls and completion time using bounded sparse execution. No training or task-specific skill engineering today.

## First reads

Read `HANDOFF.md`, `IMPLEMENTATION_STATUS.md`, `docs/SOURCE_AUDIT.md`, `docs/EXPERIMENT_PROTOCOL.md`, and `AGENTS.md`. The implementation is in `k1lab/`; the live integration uses K1's actual `registry_class` and `client_factory` extension points.

## What has been done

The CPU implementation includes generic pose/gripper execution, candidate-grasp/probe receipts, a K1 registry extension, native LIBERO source adapter, model transports, explicit policy wire protocol and RPent policy server, hashed state manifests, task-heldout freezing, and full-denominator reporting. Tests and a synthetic run are bundled. No native/GPU/API result was produced on the build host.

## Work in this order

1. Run `python -m pytest -q`, `python run.py doctor`, and a new synthetic run.
2. Fetch the pinned K1 and Zxy-MLlab LIBERO-PRO sources. Use K1's RoboSuite 1.4 environment, not RPent's 1.5 environment. Install benchmark data and optional SAM3 weights under their licenses.
3. Configure local LIBERO paths. Build a state manifest without inspecting test outcomes. Pick a **development** case, run `native_smoke.py`, inspect actual camera orientation/depth/controller units.
4. Connect one explicitly selected model through Responses/chat, or use file decisions restricted to the exported actor bundle. Run original K1 first. Do not claim an improvement yet.
5. Run `k1_stepwise` and `k1_sparse` on the same development cases. Fix generic failures (frames, arrival, stale evidence, budgets), not task-index-specific failures. Validate at least one real bounded pose sequence and one honest grasp-evidence outcome.
6. Freeze the source and concrete model/configuration with `scripts/freeze.py`. Run the **test** partition, alternating conditions as the supplied runner does. No refinement on those cases after seeing results.
7. Report success, paired uncertainty, model calls/tokens, physical steps, wall time and failure types. An accuracy tie with a cost reduction is meaningful; do not force the expected result.
8. Only then add the optional frozen-policy lane. Use an explicitly qualified checkpoint. The supplied RPent bridge is source-inspected but unqualified; FLUX DROID is NOT a compatible drop-in. See the policy qualification template.
9. Future work: a second environment/embodiment using only a documented adapter, or measured active perception under the same physical sensor limits. Neither is implemented/validated now.

## Do not

Do not spend the next session rewriting the framework, adding benchmark-specific drawer/knob skills, training a new VLA, importing exploration memory, polishing a factory animation, or treating synthetic receipts as native evidence.

The nearest useful deliverable is a small **real, auditable, paired K1 baseline/sparse experiment**, not a claimed reproduction of a paper headline from a different protocol.
