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
