# Implementation agent contract

Read HANDOFF.md, IMPLEMENTATION_STATUS.md, docs/SOURCE_AUDIT.md, then docs/EXPERIMENT_PROTOCOL.md.

1. Preserve the current K1-based direction. Do not silently resurrect DynaHarness's oracle-state skill library, per-task exploration recipes, or the old factory animation branch.
2. Get actual K1 baseline reset/render/one native move working before extending the architecture. Native results, not test count, are the next milestone.
3. Do not use hidden object transforms, instance masks, target regions, joint axes of scene objects, BDDL success geometry, or native success as a reasoning oracle. Native success is a shared termination/evaluation signal only.
4. Within-episode history is allowed. Previous-task solutions, benchmark memory downloads, cross-episode retrieval and target-task exploration are not allowed in the main experiment.
5. Keep commands generic to the robot/sensors. Do not add methods keyed by task IDs, object names, benchmark scenes or individually tuned evaluation seeds.
6. Do not claim a harness-only gain by giving the treatment a VLA that the baseline lacks. Keep primary no-VLA, controlled stepwise/sparse, and policy-availability experiments separate.
7. FLUX DROID is joint8/three-camera, not LIBERO OSC7/two-camera. No fabricated camera, silent unit conversion, or fake policy fallback.
8. Every baseline retains valid native controller behavior. K1 already has absolute target servoing, stagnation checks, history and per-step success checks.
9. Freeze source, prompts/config, concrete model identity, tool set, budgets, benchmark files and states before opening test results. Both perturbations of one base task stay on the same side of the split.
10. Log all attempts and infrastructure failures. No best-seed selection, failure-only reruns, resetting inside scored episodes, or disappearance of missing results.
11. Report synthetic tests, native experiments, API mocks, recorded-observation inference and hardware results as different evidence categories.
12. Use new output directories. Never overwrite evidence. No paid calls, deployments, downloads or host changes beyond the user's authorized scope. No hardware dispatch is supported.
13. Run pytest and the synthetic check after edits. Native qualification must additionally test frames, gripper signs, controller units, contact behavior and queue reset.
14. On failure, inspect source and actual evidence; do not replace unavailable native backends with authored success stories.

Do not access test simulator state files from an actor/coding-agent session. Use a fresh actor session per episode. File/subprocess transports are trusted research interfaces, not a security sandbox; restrict the actor to its exported request bundle when measuring performance.
