# Pi0.5-First Approach Comparison

## Scope And Status

### Owner Scheduling Correction

The owner requires method-major execution over the entire fixed task set:
run original-only on all ten distinct tasks concurrently, then direct on the
same ten, then numeric hybrid, then semantic hybrid. Do not substitute a
two-task pilot or serial task-by-task execution as the initial comparison.
All tasks should share batched inference within each motor-based method.

The previously launched tower/sorting baseline pair was stopped at the owner's
direction. Retain its partial records as owner-interrupted, not task failures
or completed comparison slots. No paid calls were made. It must not be imported
into the planned 40-slot comparison.

The missing prerequisite is now explicitly full-task concurrent execution,
not more standalone controller tests. Current native vector scenes instantiate
one task class per scene; previous ten-environment capacity evidence used two
task types with several layouts each. It does not prove ten distinct task
scenes share simulator memory. Independent single-environment processes used
about 6.7GiB each in the prior capacity check; ten such processes cannot simply
be placed on the existing two 24GiB GPUs alongside the motor runtime.
The historical shared pi0.5 worker performed isolated singleton inference.
The new cohort service uses fused vmap inference. Earlier fused predictions differed from source singleton
predictions, as recorded in `../SIMULATOR_BATCH_CAPACITY_20261002.md`.

- [ ] Enable concurrent distinct-task scenes with bounded simulator memory.
- [ ] Use a consistently defined batched pi0.5 executor across all motor-based
  conditions, retaining per-task prompts, RNG, ACKs and native scoring.
- [ ] Combine exact-task native reset/support/scoring admission with that runner,
  rather than another serial preflight sequence.
- [ ] Execute one complete method across the full task set before the next.

Do not claim full-task batching is already implemented or silently replace it
with two-family singleton dispatch. The 40-slot roster remains unchanged.

### True Batched Inference Implemented

`semantic_lab/pi05_batch.py` now vectorizes the released source sampler with
one independent seed0 RNG stream per stable episode ID and source inner
batch-of-one shapes. It applies the source input/output transforms and native
continuous-gripper clipping. Weights are shared dynamic JAX arguments rather
than embedded constants. The first outer-JIT implementation accidentally
closed over weights, inflated host compiler memory and was stopped before any
robot action or paid call; that implementation is retained in commit6106cc7.
The corrected implementation is commit713f139.

A bounded retained-input GPU check completed at B1/B2/B10. B10 returned a finite
10x50x14 tensor, took 17.12s including initial compilation and 0.699s warm, with
7.45GiB peak active JAX bytes and 16.06GiB allocator pool. These are distinct
memory measurements, not interchangeable VRAM figures. B1/B2 warm times were
0.104s/0.176s. Inputs were repeated from the two-row retained sorting request;
this check is not ten distinct tasks or completed robot throughput.

The new executor is not bitwise source singleton parity: maximum raw action
differences were 0.00794 at B1, up to0.01350 at B2 and up to0.00953 at B10.
These cover full H50 raw joint/gripper predictions. Do not silently reuse
historical singleton baseline scores as batched controls. All motor-based
comparison conditions must use the same explicitly bound executor. Actual
worker/full-task scene integration and native reset/support/scoring routing
remain pending. Do not repeat maximum-batch searches before that integration.
Evidence: `../evidence/reference-execution-binding001-20261002/pi05-vmap-batch-probe002.json`.

### Full Distinct-Task Integration

The new `run_full_panel_baseline.py` owns the complete ten-task original-only
cohort, not a two-task pilot. It launches one fused pi0.5 service and three
concurrent native simulator groups (four default datagen tasks, two support-arm
tasks, four teleop tasks). Source teleop tasks enable global PhysX stabilization;
support-arm tasks also use a different robot configuration. Keeping those
groups separate preserves native physical settings instead of flattening them
into a single modified benchmark scene. Actual group configuration equality is
checked after native resolution, not assumed from these labels.

`semantic_lab/task_rows.py` delegates unchanged task constructors, resets,
instructions, rewards and support demonstrations through singleton-index views
of shared managers. Native per-task horizons terminate independently; terminal
scores are frozen. `native_execution.py` promotes the previously tested
callbacks and applies row-specific horizons. `serve_pi05_batch.py` coalesces all
active group requests, preserves independent episode RNG streams and returns
indexed predictions/ACKs. Inference-only padding keeps the compiled B10 shape
after tasks terminate; padded rows never receive simulator actions or scores.

- [x] Implement task-row routing, compatible-scene factory, fused cohort worker,
  and full-panel baseline launcher.
- [ ] Verify actual full-panel startup, support trajectories, native scoring,
  memory and actions on the GPU host.
- [ ] Complete all ten original-only episodes and inspect their evidence.
- [ ] Admit the native-equivalent executor and bind all four matched conditions.

429 CPU tests pass, including index isolation, cooperative native lifecycle,
independent final checks and terminal-score freezing. These are plumbing checks,
not completed phase/task results. No paid calls are used by this initial run.
The native-equivalence admission remains pending; do not claim the 40-slot
approach comparison complete merely because this launcher exists.

First full-cohort startup (`pi05-full-panel-baseline001`) loaded all ten scenes
and passed physical-config equality and fixed-layout/horizon checks for the
four-row datagen and four-row teleop groups. All three simulators occupied about
17.6GiB on GPU0 while model loading occupied about8.5GiB on GPU1. The support
group then exposed an adapter bug: native `make_kong` has no partial-score
registration method, unlike the other selected tasks. Its binary native reward
must be retained, not replaced with an invented partial score. The cohort was
stopped, owned processes cleaned up, and both GPUs returned to zero usage.
This is failed startup evidence, not a completed baseline or task failure.

The router now registers partial scores only where native tasks supply them.
The parent and fused service also reject an explicit group failure regardless
of its process exit code: Isaac application shutdown can mask a Python error
with exit0. No automatic retry or smaller-task substitution is permitted.

The corrected full cohort (`pi05-full-panel-baseline002`) reached real fused
B10 inference and native controls on all ten tasks. All initial head-camera
views were visually inspected and showed the expected distinct scenes; retained
requests also preserve task-specific native prompts. The support group then
hit a real PhysX GPU-memory allocation failure at action62 (61 ACKed actions per
support environment). The other groups had75 ACKed actions per environment.
PhysX logged `Scene state is corrupted` and stopped simulation; its Python
process remained live. The entire cohort was explicitly stopped and excluded
from performance scoring. This is not evidence of a policy/task failure.

The next full attempt moves the two support tasks to GPU1 alongside the policy,
keeps the other eight tasks on GPU0, and caps the JAX allocator fraction at0.5.
The previous all-simulation-on-GPU0 allocation reached roughly22.4GiB with only
1.1GiB spare, while GPU1 retained roughly7.1GiB spare. GPU affinity changes are
resource routing, not changed task physics, sensing or horizons. Native PhysX
monitoring is now enabled, and the parent also watches fatal simulation logs
so a live process can no longer masquerade as a progressing simulator.
The rebalanced full cohort has not yet been verified; do not mark batching or
the baseline complete from the earlier nonblank captures and component tests.

Compare approaches first, motor models afterward. This is the next experiment
priority, not a completed comparison or a substitute for the wider V5 scope.
Roster selection below is fixed before new outcomes. Exact resolved treatment
configs, source freeze, executor admission and paid relay bindings are still
pending; this document alone is not an executable campaign freeze.

## Fixed Diverse Roster

Take group0/layout0 of the standard variant in each of the ten selected
GPT-as-Policy reference groups. Do not choose replacements based on outcomes.
Verify actual layout hashes against `configs/local/robodojo-cases.json`.

| Task Group | Case ID | Horizon | Existing Partition |
|---|---|---:|---|
| arrange_largest_number | arrange_largest_number__standard__g0__l0 |1050|test, already opened|
| build_tower | build_tower__standard__g0__l0 |1050|dev|
| classify_objects | classify_objects__standard__g0__l0 |1100|dev|
| classify_objects_by_language | classify_objects_by_language__standard__g0__l0 |1100|test|
| fold_clothes | fold_clothes__standard__g0__l0 |500|test|
| imitate_sorting_sequence | imitate_sorting_sequence__standard__g0__l0 |1600|test|
| make_kong | make_kong__standard__g0__l0 |600|test|
| organize_table | organize_table__standard__g0__l0 |1000|test|
| pack_objects_into_box | pack_objects_into_box__standard__g0__l0 |1300|test|
| put_bottles_into_dustbin | put_bottles_into_dustbin__standard__g0__l0 |700|test|

Ten cases mean ten distinct task groups, not ten independent replications per
task. This first approach screen is not the full50-case reference denominator
or full RoboDojo SR. Preserve dev, opened-test and unopened-test reporting.
Expand fixed layouts afterward rather than choosing only successful groups.
The imitation task keeps its original native demonstration/support stream;
no added cross-episode demonstration or recipe is supplied to the actor.

## Four Primary Conditions

1. Original-policy-only: exact pi0.5 checkpoint, original instruction,
   source H50 predictions and normal15-action execution prefixes; no GPT calls.
2. Direct GPT: robot-policy-free sparse direct profile, bounded EEF targets
   executed by the qualified local controller. Not one GPT call per control
   tick. Keep the40-action maximum and report actual early returns.
3. Numeric hybrid: pi0.5 plus sparse numeric accept/shorten/correct/stop review.
   Label it an adapted GPT-as-Policy-style method, not faithful paper reproduction.
   Preserve actual interruption/reset/suffix-discard accounting.
4. Semantic hybrid: original task plus current semantic subtask at normal
   policy boundaries; no numeric correction or prefix shortening. Recovery is
   disabled for this primary comparison, retained as a later separate condition.

Align numeric/semantic periodic review targets at100 native steps, admitted at
the next normal motor boundary; retain method-specific action authority and
event-triggered reviews explicitly. Other scheduling choices require a named
ablation, not an unnoticed fairness difference. Use Sol6.1/medium/Flex and
matched legal RGB/proprio/FK, reset/layout/seed, native horizon and termination
rules. Native rewards/scores/object state never enter the actor.

Dense direct's five-action/180-call template cannot cover1050/1100 horizons.
Do not use it as the primary full-horizon baseline. Sparse40x180 has sufficient
upper-bound capacity for this roster, but shorter decisions/early local returns
can still exhaust requests. Budget/wall/contract stops stay censored or invalid,
not scored physical failures or replacements. All requests remain behind the
existing$85 shared reservation ledger; unresolved holds remain charged.

## Execution And Reporting

Finish scoped executor qualification and native variant admission before new
held-out controls. The vector semantic runner does not currently implement a
matched numeric/direct wave: integrate those existing controller/actor paths
without inventing task skills, or explicitly document identical contracts
across the separate execution paths before freezing their comparison.

Use shared pi0.5 inference and concurrent task-family waves where admitted and
memory-safe. No more maximum-batch search is required. With5.5GiB disk free,
plan sensor retention before launching a full campaign; do not download weights
to the Mac or delete unique evidence/unrelated workloads.

Report all40 planned condition/case slots, including missing entries, actual
controls/ACKs, success, partial score, wall time including startup separately,
planner wait, GPT/policy calls and settled/reserved cost. Do not import old
screen outcomes as fresh matched controls. Publish differences descriptively;
one run per task cannot establish a reliable hierarchy advantage.

## Execution Integration Progress

The old vector coordinator required all active episodes to request the same
operation at every barrier. Numeric shortening makes one episode request a new
prediction while another still requests a native action, so that restriction
would stop valid numeric/direct experiments rather than batch them.

- [x] Extract the existing coordinator to `semantic_lab/vector.py`, preserving
  strict semantic barriers by default and adding explicit mixed-operation mode.
- [x] Route the existing numeric/direct episode loop through per-episode facades
  in CPU fixtures, without duplicating its actor/governor/controller logic.
- [x] Resolve read-only preview/inference subsets before native action dispatch;
  retain separate per-episode inference cadence and contiguous ACK streams.
- [x] Prepare a robot-only environment-index view for the pinned source DLS.
- [x] Wire native indexed source DLS/previews and audit emitted joint commands.
- [ ] Qualify the native correction path and task variants before paid trials.
- [ ] Bind `robot_decision` paid review separately from `semantic_goal`, preserving
  the shared ledger, reservations and no-retry contract.
- [ ] Freeze resolved conditions/source/cases, then run the matched task waves.

Native wiring now uses the pinned source DLS through the indexed robot view.
Direct mode skips policy-worker launch/registration and reports a null motor
policy. Paid-call accounting reads client attempts, not validated decisions.
The prepared `reference-controller-probe001.json` is a separate no-API,
30-action calibration: 15 actions toward a 5mm left-EEF offset then 15 toward
the initial robot pose, with unchanged orientation/grippers. It has no task
recipe and explicitly records unknown external clearance. Native execution
completed on the two opened sorting layouts: ten actual actions per environment,
two five-action segments stopped by the existing arrival check, zero motor
predictions and zero paid calls. Initial robot-only FK error was approximately
0.000064mm; measured left-arm endpoint error was 0.043mm outbound and 0.048mm
on return. Both journals and emitted joint commands passed the retained audit;
all 45 backup files matched remote hashes. This is bounded calibration, not
task performance or full executor qualification. Both initial robot postures
were identical, so native isolation under divergent robot states is unproven.
Preview/correction interleaving and task-variant admission remain pending.
See `../evidence/reference-execution-binding001-20261002/controller-probe-audit001.json`.

The separate `reference-interleaving-probe001.json` check then completed on
the same two opened layouts: 45 native actions each (40 exact source-policy
actions plus five forced calibration corrections), four H50 predictions and
four native source FK previews each. Environment0 corrected its left arm;
environment1 corrected its right arm. Both resumed fresh policy predictions
after correction, without controller errors, unstable flags or paid calls.
Rollout wall time was 28.39s, excluding startup. Contiguous journals, source
proposal equality, motor command equality and bounded DLS updates passed the
retained audit; all 87 backup files matched the host. This calibration fixture
does not establish learned recovery, task success or unseen-variant admission.
No more native controller/capacity sweep is planned before the approach screen.
See `../evidence/reference-execution-binding001-20261002/interleaving-audit001.json`.

The fixed panel and all four complete native-runner condition configs are now
prepared in `../evidence/pi05-approach-preparation001-20261002/`. The preparer
uses the existing sealed reference manifest and bound pi0.5 provider identity,
selects standard group0/layout0 in the ten fixed groups, and retains all 40
condition/case slots as missing. No task outcome was consulted. Numeric periodic
leases are 105 steps (seven H15 prefixes); semantic review remains target100
at the next prefix boundary. Event-triggered scheduling differences are explicit.
Fresh executor source binding, scoped native admission and actual paid relay
reservation remain required before those prepared configs can be launched.

The source `DualKinematics` reads robot queries and limits at local index0.
Native robot queries return dictionaries keyed by global environment index.
`SingleEnvironmentRobotManager` requests only its selected native index,
rekeys that robot-only reply to0, and slices that environment's joint limits.
It exposes no generic scene/object forwarding. Missing robot values fail rather
than falling back to environment0. General native FK/DLS qualification remains pending.

CPU integration uses authored synthetic controls, not policies/LLMs or collision
physics. It demonstrates differing inference/action barriers, policy-free direct
dispatch, strict-default rejection, uncertain-write no-retry handling, and
retirement on runner errors. These tests are not approach performance or phase
completion. No new paid requests or simulator actions were issued for this work.
