# Implementation status — v0.4

## Live bring-up update — 2026-10-02

The build-host statements below describe the original release, not the current
GPU-host state. Native RoboDojo capture, robot FK and one actual joint-action ACK
now pass; see `docs/NATIVE_BRINGUP_20261002.md`. G0.5's fixed development
screen completed with 3/5 successes; official XR1's balanced RoboCasa365
screen completed with 2/6 successes. These are development results, not held-out
scores or cross-benchmark policy comparisons. One sparse XR1 episode completed
one paid Flex review and 50 native actions, then stopped on capacity failure.
No complete held-out three-condition comparison exists yet. One complete pi0.5
sparse development episode now fails at its full 1050-action horizon, score 0.0,
27 settled Flex reviews/$0.258, versus the nominal motor-only case's success.
See `docs/PI05_SPARSE_SUPERVISION_20261002.md` and
`docs/EXPERIMENT_PROGRESS.md` and `docs/XR1_DEVELOPMENT_SCREEN_20261002.md`.
The exact RoboDojo pi0.5 checkpoint is now provisioned and publisher-hash verified;
its isolated OpenPI/JAX runtime and native sorting pilot now pass (score 1.0,
994 actions). Its fixed five-case screen is now complete: 4/5 success, zero
GPT calls, matched saved-input warm p50 454 ms versus G0.5's 801 ms. See
`docs/PI05_DEVELOPMENT_SCREEN_20261002.md`.
Intern was reopened by the owner: explicit two-GPU BF16 placement now loads and
infers at about 820 ms per 10-action chunk; the first native tower0 episode
succeeded at 727 actions/73 calls in 489.11 s. Formal qualification and the
remaining fixed development roster are pending; see `docs/INTERN_NATIVE_PILOT_20261002.md`.
Xiaomi RoboDojo remains outside active scope; XR1 RoboCasa365 remains active.

Exact motor-only G0.5/pi0.5 native qualifications are now evidence-reviewed;
fresh G0.5/pi0.5/XR1 motor freezes verify against current source and full grouped
manifests. See `docs/NATIVE_FREEZE_UPDATE_20261002.md`. These records do not
qualify GPT corrections/contact or relabel historical development results.

## Implemented and exercised on CPU

- Original K1/LIBERO implementation retained, with original127 tests.
- New multi-benchmark runner, five condition modes, action/observation/policy
  contracts, periodic and event-triggered review, bounded correction and ACK loop.
- Source-backed RoboDojo RPC client and pure robot-FK H50 compatibility shim.
- Source-interface adapters for π0.5, Xiaomi R1, G0.5 and InternW0-Δ.
- Official Xiaomi RoboCasa365 preprocessing/client wrapper and native Gym adapter.
- Separate loopback policy service, ownership/sequence validation, no retries,
  stateful policy ACK handling and explicit interruption reset.
- Sol Responses configuration, Flex as the active default plus a separate
  Standard comparison profile, compact
  within-episode state, current/previous execution images, usage/tier archives.
-17 experiment configs, five provider templates, provider/artifact identity
  binding, grouped dev/test manifests, freeze and manual qualification records.
- Policy-only latency tool, native single-case launch/capture planning,
  lossless observation export, matrix planning, runtime fingerprints, reports/plots.
- Full-denominator and paired reporting; native scores distinct from success.

## Validation on build host

The final validation report under `docs/multibench/` records the exact test count,
synthetic journal verification and fresh-archive check. The final source and a fresh extracted archive both passed
234 CPU tests. None of those tests is a GPU policy or real simulator test.
The example matrix has15 authored synthetic episodes across five conditions.
Its success labels are fixture behavior, not evidence of a harness gain.

## Source-inspected and mock-tested, but NOT native-qualified

All new RoboDojo, XPolicyLab and RoboCasa native adapters. No native reset,
render, action, inference or completion result was obtained on this build host.
The external agent must prove action conventions, timing, state-history updates,
calibration where applicable, nonvacuous completion and representative task
behavior before a scored experiment. Source pins are not full binary dependency
locks. Software tests cannot certify contact dynamics or hardware safety.

## Important incomplete items

1. **Native comparisons:** development motor-only screens exist, but complete
   matched supervision and robot-policy-free dense/sparse comparisons remain
   pending. No harness gain or leaderboard result is established.
2. **Xiaomi RoboDojo original controller parity:** its EEF actions currently go
   through donor DLS. That is a labeled variant requiring a source-path comparison.
3. **K1 depth tools on RoboDojo/RoboCasa:** not ported. RoboDojo source RPC is RGB
   only. New signals/geometry must have a real sensor source and matched ablation.
4. **Intern cancellation without memory loss:** source reset currently discards
   temporal context on interventions. A future safe cancel hook requires source
   investigation and explicit policy-history tests; no fake ACK workaround.
5. **General semantic monitors:** local stagnation/validity is not enough. Periodic
   model review stays enabled. Sensor flags are not fabricated by the runner.
6. **Learned failure/grasp classifiers, universal grasp macros, active external
   cameras, arbitrary task skill synthesis, post-training and distillation:** not
   added to these new benchmark lanes.
7. **Additional policies:** DM0.5/OpenWAM/RoboDawn/RoboICL remain references, not
   silently substituted backends. FLUX DROID remains a separate unretargeted path.
8. **Cluster execution/global paid budget enforcement:** launcher owns one case;
   matrix script produces a plan. No remote job submission, purchased compute,
   account management or automatic long-running fleet scheduler is included.
9. **Leaderboard submission:** official split/asset/rule compliance must be
   independently checked; a report generated by this package is not a submission.

## Primary next milestone

Retained motor-only bindings are now qualified/frozen. Finish native supervision
integration and matched comparisons under the explicitly selected Flex tier when
capacity is available. Retain capacity failures without automatic retry or tier
fallback. The fixed pi0.5 development screen and matched warm timing are complete;
robot-policy-free dense/sparse experiments remain pending. Do not expand
baseline screens or redesign the architecture to sidestep these milestones.
