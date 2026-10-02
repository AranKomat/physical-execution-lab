# Pi0.5-First Approach Comparison

## Scope And Status

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
