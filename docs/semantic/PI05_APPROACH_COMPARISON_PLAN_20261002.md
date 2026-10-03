# Pi0.5-First Approach Comparison

## Scope And Status

### Fidelity Correction (2026-10-03)

The owner requested clarification against the published GPT-as-Policy gain.
Numeric005 is an adapted sparse condition, not its reference hybrid: released
code reviews every proposal, supports trajectory edits as well as EEF targets,
uses a persistent Astra/xhigh tool agent, and forbids model-directed early stops
on benchmark cases. Our five accepted stops and sparse cadence are material
differences. Read `GPT_AS_POLICY_FIDELITY_REVIEW_20261003.md` for pinned evidence
and the added reference-style control checklist. Finish semantic001 unchanged,
then obtain a same-host baseline. Preserve all ten distinct tasks concurrently
and the existing budgets.

### Owner Direction: Semantic First

The owner subsequently chose sparse high-level language supervision as the main
path, rather than spending on a faithful high-frequency numeric reproduction.
The fidelity review remains necessary to interpret numeric005, but its proposed
reference-style control is deferred, not the next mandatory paid experiment.

- [x] Finish semantic001 and audit prompt routing, normal motor cadence and all
  ten outcomes before changing its condition.
- [x] Inspect failures separately as wrong semantic goal, weak motor response,
  planner abstention, or infrastructure/contract error. A routed prompt does not
  prove subtask obedience, and a visual judgment is not hidden physical truth.
- [x] Select a fresh semantic condition from retained evidence, emphasizing
  coherent subtasks, meaningful completion checks and evidence-triggered
  replanning without motor-prefix interruption. Do not tune during semantic001.
- [x] Keep a matched same-host original-only full-ten control; retain baseline003.
- [ ] Defer reference-style numeric reproduction and further numeric cadence
  sweeps. Numeric corrections are a possible later narrowly scoped fallback,
  not the central architecture. No published gain is imported as our result.

### All-Ten Visual Review And Same-Host Control (2026-10-03)

Baseline004 completed with 2/10 native successes, mean score 0.345, 8,631
actions and zero API calls. Semantic001 also has two successes; classification
improves from 0.4 to 1, packing from 0.10 to 0.25, folding remains successful,
and bottles becomes an early planner abstention. Do not present the old-host
baseline003's 3/10 as a clean matched contrast. One attempt per task remains
insufficient for a reliable hierarchy benefit.

The owner-requested visual check is complete across all ten actual semantic
trajectories. Folding/pink-bottle pickup and parts of packing/classification
align with goals. Language sorting has a clear wrong-basket placement; imitation
handles a different rectangular device; tower/table continue other overall-task
operations while narrow goals remain active. Planner goals can be stale, and
hidden placement is not automatically physical failure. Prompt routing/tokenizer
retention and native cadence audits pass; obedience is a separate behavioral
question. See
`../evidence/pi05-semantic-visual-audit001-20261003/REPORT.md`.

- [x] Review all-ten prompt epochs with retained RGB and closer ambiguous sequences.
- [x] Publish same-host descriptive contrast without importing historical controls.
- [ ] Run a bounded matched-state original/task-plus-subtask/subtask-only response
  check with visible physical effects; prediction differences alone do not qualify.
- [ ] Complete and audit the separately frozen full-ten recovery-only run,
  currently active as `pi05-full-panel-semantic-recovery001`. It does not by
  itself fix exclusive motor steerability; issued and accepted recoveries differ.

No new episode, training or paid call was launched for the visual review.
The consolidated observational answer across both semantic formats is
`PI05_INSTRUCTION_FOLLOWING_REVIEW_20261003.md`. The separately launched recovery
condition retains the frozen source/config, all ten tasks and $3 cohort cap.

### Prompt-Format Continuation

- [x] Prepare and freeze the full-ten subtask-only condition with exactly one
  behavioral config change (`prompt_mode`); recovery stays disabled. Freeze:
  `da84e38f13000335dd30da9b410b87cbfa84413bc20be0ea4d22963de4585444`.
- [x] Pass retained native transfer and all-ten live reset admission on this host.
- [x] Complete `pi05-full-panel-subtask001`, audit its actual prompts/prefixes,
  preserve the evidence and visually inspect outcomes. One native success,
  five native failures, four planner abstentions; score coverage 6/10.
- [x] Compare its native outcomes, planner abstentions and response to active
  goals against baseline004 and semantic001. Configuration matching does not
  make planner decisions or rollout observations identical across conditions.

This continuation is a full-roster practical format ablation, not the separate
matched-state causal diagnostic above. It uses Sol6.1/medium/Flex, the authorized
same-model capacity fallback, the $3 cohort cap and $95 shared ceiling. No new
recovery or motor intervention is enabled. Initial imitation abstention at step
0 and subsequent stops are retained, not silently retried or scored as physical
failures. Recovery-only preparation remains unrun until separately selected.

The finished subtask-only cohort used 5,922 actions, 397 motor predictions,
21 prompt changes, 62 settled Flex calls/$0.36038075 and 19.15 minutes including
startup, with no new hold or API/controller error. Independent local/remote
audits match; full raw archive hashes match. All ten sheets were inspected,
with imitation correctly excluded from motor-following claims because it
stopped before any prediction. Classification succeeds again, table partial
score improves to 0.75, but folding loses its success and packing explicitly
handles a shoe under a car-only instruction. No reliable overall improvement
or exclusive goal control is established. Keep task-plus-subtask as the working
format; prioritize the prepared recovery-only ablation rather than more minor
format sweeps. See
`../evidence/pi05-full-panel-subtask001-20261003/REPORT.md`.

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

- [x] Enable concurrent distinct-task scenes with bounded simulator memory.
- [ ] Use a consistently defined batched pi0.5 executor across all motor-based
  conditions, retaining per-task prompts, RNG, ACKs and native scoring.
- [x] Bind the fixed screened runtime to retained native reset/config/layout,
  support/control and scoring evidence, with an all-ten live pre-action gate.
  This is scoped matched-screen admission, not singleton bitwise parity or full
  benchmark/hardware qualification.
- [x] Execute original-only across the full task set before the next method.
- [ ] Execute direct, numeric and semantic conditions, each across the same full
  set, after executor admission/binding.

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
- [x] Verify actual full-panel startup, support trajectories, native scoring,
  memory and actions on the GPU host.
- [x] Complete all ten original-only episodes and inspect their evidence.
- [ ] Admit the native-equivalent executor and bind all four matched conditions.

### Scoped Admission And Interrupted Direct Trial (2026-10-03 JST)

Shutdown continuation: numeric001 failed its disk preflight before simulator
startup or paid calls. Clearing about5.7GiB of old regenerable Omniverse texture
cache raised free space to8.7GiB without deleting records or weights. The fresh
numeric002 passed all-ten live admission and executed3,986 recorded actions
before the owner requested instance shutdown preparation. Retained native
outcomes: fold_clothes succeeded at297 actions/score1; make_kong failed at600/
score0; imitate_sorting_sequence failed at636/score0. organize_table issued an
incomplete model stop at158 actions. Six other episodes were owner-interrupted.
Do not convert these six into physical failures or quote a full-panel SR.
Numeric is partially executed, not complete; semantic remains unrun.
Settled cost$1.478102 plus retained Flex hold$0.053577. All owned GPU processes
and the short-lived token were removed. See
`../semantic/INSTANCE_SHUTDOWN_HANDOFF_20261003.md` for backup and restart notes.

Latest continuation: `pi05-full-panel-direct002` has ended and its evidence is
backed up and audited. Standard fallback worked, but all ten outcomes remain
censored/invalid: four translation-contract rejections, two action-shape
rejections, one model-issued incomplete stop, and three HTTP-error stops after
an OpenRouter admission-control429. No native terminal outcomes or task scores
exist. Do not report0/10 physical SR. See
`../evidence/pi05-full-panel-direct002-20261003/REPORT.md` for accounting,
interface diagnostics and the next full-panel conditions. Numeric and semantic
remain unrun. The unresolved standard429 hold is retained; it is not covered by
the narrow Flex-capacity fallback authorization. New executor source changes
require a fresh freeze before the next method.

`cohort_admission.py` verifies the completed baseline's retained integrity audit,
unchanged task/control/inference core,2,941 native source/config files from the
controller reference freeze, and all87 native interleaving-evidence files.
The paid launcher additionally requires each physical group to match its
baseline's resolved configuration, layout bindings, native horizon, reset
proprioception (maximum permitted difference1e-5) and original instruction.
Direct/numeric require both-arm robot-only FK validation on every row. All
three groups wait for the parent to admit all ten rows before paid decisions.
Rendering pixel equality is not claimed. The initial sensor read used for the
gate makes no physical action and sends no evaluator data to the actor.

`pi05-full-panel-direct001` passed all those gates and ran policy-free direct
with the original Flex-only condition. It made two settled provider calls
costing$0.007587, then a third provider request failed with explicit Flex
capacity unavailability. Its$0.042099 reservation remains held. The same paused
episodes were not retried and no model/tier fallback occurred in this trial.
All ten episodes were invalid/censored infrastructure outcomes: eight executed
zero actions, sorting executed one and Mahjong executed five. There are zero
native terminal outcomes and no available task scores, not0/10 physical SR.
Twelve client HTTP attempts include local relay rejections after the provider
lane stopped; there were only three actual provider reservations.
Total cohort wall time was111.83seconds, with zero motor policy runtimes.

The retained control audit passed for all ten journals and six ACKs. All161
remote files matched the local backup, aggregate SHA256
`88c4589582a833aa513973114c40be8a23cc1b9f3606c95c93b495d639acfc0f`.
The old raw parent report says `completed_full_approach_cohort`; that described
scheduler return, not valid task completion. Preserve it as raw evidence and
use the independent audit's censored accounting. The maintained launcher now
emits `incomplete_full_approach_cohort` unless all ten outcomes are native terminal.

The owner subsequently authorized regular/standard processing whenever Flex
is unavailable. New named paid conditions retain Sol6.1/medium, prefer Flex,
and allow one standard-tier substitution only after the exact structured,
no-output Flex capacity rejection. Unknown network effects, generic errors,
malformed responses and standard failures still do not retry. A recognized
Flex hold is acknowledged but never released; it counts against both the
local$3 cap and shared$85 ceiling. Subsequent requests in that trial stay on
standard, and actual tiers/costs are retained. Standard reservation/pricing
bounds are doubled; no automatic provider or model substitution is allowed.
This tier policy must be explicitly prepared and frozen, not silently applied
to the historical Flex-only condition. The interrupted trial is not replaced
or treated as evidence about direct-control quality.

Official transport guidance checked:
https://developers.openai.com/api/docs/guides/flex-processing
Public route listing checked2026-10-03 JST: Sol6.1 Flex prompt/completion
$1/$5 per million versus OpenAI standard$2/$10; cache-write rates$1.25/$2.50.
The conservative relay reserves at$1.50/$6 and$3/$12 respectively. A fresh
full-method condition with the authorized policy is next; numeric/semantic
still have no full-panel outcomes.

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
At that point the rebalanced cohort had not been verified. Its completed
outcome is recorded below, separately from the failed starts.

### Rebalanced Full Baseline Completed

`pi05-full-panel-baseline003` (executor commitd9299d0) completed all ten fixed
cases concurrently under original-only, with one fused pi0.5 runtime. It used
8,497 native actions, 569 per-episode policy predictions coalesced into87 fused
batches, zero GPT/API requests, and751.45s wall time including startup
(12.52minutes). Warm batches with all ten rows had median1.231s. Padding after
termination preserved the B10 compiled shape without issuing padded actions.
All three groups report native terminal outcomes, no controller/contract
errors, and no unstable samples. Both GPUs returned to zero usage afterward.

| Task | Native Success | Partial Score | ACKed Actions |
|---|---|---:|---:|
| arrange_largest_number | no |0.30|1050|
| build_tower | no |0.10|1050|
| classify_objects_by_language | no |0.00|1100|
| fold_clothes | yes |1.00|300|
| imitate_sorting_sequence | no |0.00|782|
| make_kong | no |0.00|600|
| classify_objects | yes |1.00|824|
| organize_table | no |0.50|1000|
| pack_objects_into_box | no |0.50|1300|
| put_bottles_into_dustbin | yes |1.00|491|

The descriptive outcome is3/10 for this fixed one-layout-per-task screen, not
full RoboDojo SR or a statistically reliable approach ranking. The earlier
five-case development result must not be substituted as its matched baseline.
The imitation task ended under a native failure rule before its1600 horizon,
not under a planner budget/controller stop; neither support task was flagged
unstable. Original-only used native instructions and no semantic/numeric review.

Full-cohort source hashes and per-case results are retained in
`../evidence/pi05-full-panel-baseline003-20261002/cohort-report.json`.
`audit_full_panel_baseline.py` checks retained request hashes, task routing,
source H50 predictions, exact15-action prefixes, contiguous ACKs and native
terminal/result agreement. The audit passed for all8,497 actions; its result is
`../evidence/pi05-full-panel-baseline003-20261002/integrity-audit.json`.
This audit is execution integrity, not an automatic
native-equivalence qualification. Results remain `native_unqualified` until
that admission is attached. Direct/numeric/semantic are not yet run on this
panel; the broader V5 hierarchy/recovery/generalization phases remain open.

Compare approaches first, motor models afterward. This is the next experiment
priority, not a completed comparison or a substitute for the wider V5 scope.
Roster selection below is fixed before new outcomes. Exact resolved treatment
configs, source freeze, executor admission and paid relay bindings are still
pending; this document alone is not an executable campaign freeze.

### Staged Replication And Metrics

The [GPT-as-Policy report](https://anonymous-report-421.github.io/public-website/?lang=en&view=1)
(sections2.2 and3, checked2026-10-02) evaluates direct and hybrid on five
matched episodes per task, fifty per method. Three generalization tasks use
two standard and three randomized episodes; other tasks use five standard
layouts. Official motor-policy columns are recomputed from public per-task
aggregates, not five matched reruns. Their decimal percentages therefore do
not establish the denominator of our planned matched comparison.

First complete all four methods on the fixed ten distinct cases above. Report
native binary success and native partial score together, plus per-task paired
differences, wall time and paid usage. The baseline currently has3/10 successes
and mean normalized score0.44 (44/100), descriptive one-layout evidence only.
Scores indicate partial progress, not probability of success; native binary-only
tasks remain binary. A single episode per task is a screening design, not a
reliable per-task success-rate estimate or faithful paper reproduction.

Then extend the promising methods, including their matched baseline, across
preselected additional layouts over the entire roster. Do not select only
successful tasks, or repeat identical deterministic conditions as independent
evidence. If claiming a paper-matched result, use its full five-episode scene
mix and matched seeds. Even five trials give only coarse per-task estimates.
The earlier two-task/five-layout run was capacity qualification, not a reporting
requirement or a preference over distinct-task coverage.

One full original-only wave took12.52minutes including startup, not per task.
Five waves cost roughly five times one method's runtime; GPT latency and cost
must be measured rather than assumed equal to original-only throughput.

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
held-out controls. The full-panel launcher now selects original-only, direct,
numeric or semantic via `--approach`, reusing the existing episode loops rather
than inventing task skills. All conditions preserve the same ten-case roster
and three native physical groups. Direct starts no motor worker and bypasses
worker readiness; numeric/semantic share the same B10 worker as original-only.
Paid conditions require explicit `--allow-api`, an inherited relay token and
`--freeze` binding the entire panel, treatment and reviewed execution sources.
Each group verifies that binding before startup and before entering its loop;
the parent watches source drift during execution. These guards bind bytes,
not native-equivalence admission. Do not launch paid held-out controls solely
because these orchestration fixtures pass. The three additional approaches
still have no completed full-panel outcomes.

The relay adds explicit `full_panel1800` capacity (ten episodes times180
maximum requests), retaining its local$3 cap, shared$85 ceiling, all unresolved
holds, serialized provider access and no automatic retries/fallback. The old
`comparison180` remains unchanged for single-episode work. Completing all native
horizons in direct mode would require at least254 decisions with40 actions
each, even without early arrival returns; a global180-call cap would truncate
that cohort. A larger call allowance does not guarantee affordable completion.
The existing paid-ledger window is still capped at2400seconds independently
of the simulator3600second wall bound; exhausted budget/time remains censored.
Fresh ledger inspection found4945 reserved requests,154 unresolved holds,
$78.958224994300 charged including holds, and$6.041775005700 remaining under85.
No paid calls were made for this launcher work.

Use shared pi0.5 inference and concurrent task-family waves where admitted and
memory-safe. No more maximum-batch search is required. With3.3GiB disk free,
plan sensor retention before launching a full campaign; do not download weights
to the Mac or delete unique evidence/unrelated workloads. The completed baseline's
full archive was backed up locally with matching SHA256
`aaf1d2d4a8821f9a6bbe90ebaf375b85d2db7b9a0b9eeffe4d58ea2782b448d2`;
only that duplicate remote archive was removed. Unique raw evidence remains.

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

## New Host And Authorized Budget (2026-10-03)

- [x] Owner authorized a $95 shared ceiling for the full-ten numeric and semantic
  comparisons. Launch with `--shared-cap-usd 95`; the default remains $85.
  The $3 per-cohort cap and every unresolved hold remain unchanged.
- [x] New Romania endpoint: port 53786 on 92.180.27.84, two 24 GB RTX 4090s.
  Pinned source revisions and the exact released pi0.5 checkpoint are restored.
  Model weights remain on the GPU host, not the Mac.
- [x] CPU suite: 451 passed after the budget-option change; all 1,380 release
  file hashes passed.
- [x] Complete pinned simulator asset transfer and verify retained layout bindings.
  Scoped transfer checks passed for 2,941 native source/config files and 87
  retained controller evidence files. The baseline integrity audit was regenerated
  from its archived 8,497 action records. This is not new physical qualification;
  live reset and installed-runtime behavior remain to be checked during startup.
- [x] Freeze updated source and run the fresh full-ten bounded numeric condition.
  Numeric005 finished all scheduled controllers: 3 native successes, 2 native
  failures and 5 model-directed early stops. Native score coverage is 5/10;
  full-panel scored comparison remains incomplete. See
  `../evidence/pi05-full-panel-numeric005-20261003/REPORT.md`.
- [x] Run the fresh full-ten semantic condition, separately from numeric.
  Semantic001 finished: two successes, five native failures, three planner
  abstentions; native score coverage 7/10. All 7,209 action/prefix/prompt-retention
  checks passed. Cost $0.44593025, 74 settled Flex calls, no new holds.
  See `../evidence/pi05-full-panel-semantic001-20261003/REPORT.md`.

`pi05-full-panel-semantic001` finished on the same post-reboot host with one
shared pi0.5 runtime and all ten distinct tasks. All-ten reset admission passed.
All three abstention explanations cite recovery being disabled; the bottle stop
was uncertainty about placement, not established failure. A fresh recovery-enabled
condition is next after the same-host original-only control. Preserve this trial;
it cannot be retroactively changed into a recovery-enabled or native-only run.

### Same-Host Control And Recovery Preparation

- [ ] `pi05-full-panel-baseline004`: separate same-host original-only repeat,
  live under freeze004, zero paid calls, all ten distinct tasks concurrently.
  Preserve baseline003 and do not choose cases from the repeat's outcomes.
- [x] Prepare the full-ten recovery ablation without executable changes:
  `runs/pi05-approach-semantic-recovery-preparation001/` on the GPU host and Mac.
  The only behavioral delta from semantic001 is
  `semantic_schedule.allow_semantic_recovery=false -> true`; condition name and
  sealed plan hashes change as metadata. Prompt mode, cadence, model/effort/tier,
  schemas, stopping behavior, sensors, budgets and tasks remain unchanged.
  Fresh freeze: `91f5bf8cac215e420986f77756e0c1c7787962786b6ac0fce5ca744bfea46548`.
  Preparation is not a native recovery result or phase completion.
- [ ] Audit baseline004, then run the separately named semantic recovery cohort
  with live matched-reset admission and the existing ledger limits. Do not
  assume enabling recovery will prevent uncertainty-based abstention; the stop
  option remains available and must be reported.

- [x] Download the complete numeric005 evidence archive and match its remote
  SHA-256; extract and independently re-audit all ten streams and 6,390 ACKs.
  See the numeric005 report's Independent Local Backup section. No model weights
  were downloaded to the Mac.

The new host has a 372 GiB root disk. Simulator dependencies outside the frozen
OpenPI environment were resolved during installation; exact transitive runtime
equivalence to the old host is not claimed. Prior numeric002 remains an
owner-interrupted trial, not a completed panel or a resumable live episode.

### New-Host Startup Failure

`pi05-full-panel-numeric003` stopped in simulator startup after 15.61 seconds,
before paid calls or native actions. Concurrent first-use Kit extension pulls
collided while extracting `omni.kit.pip_archive`. Its incomplete cached files
were quarantined, not treated as valid installed binaries. A single-simulator
cache warmup also exposed a conda ICU/system libstdc++ ABI mismatch.

The launcher now accepts an explicit `--simulator-libstdcxx` path and records
the resolved library path and SHA-256 in the cohort report. It affects simulator
children only, not the policy worker, paid relay or model configuration. This
host-runtime difference is explicit; it is not proof of old/new runtime parity.
Retain numeric003 as a startup failure, never a physical 0/10 result.

`pi05-full-panel-numeric004` constructed simulator scenes and loaded the policy
worker, but stopped before actor calls/actions when `nvidia-smi` failed with
driver/library mismatch (exit 18). Ubuntu unattended upgrades changed NVIDIA
libraries while the old kernel module was loaded. This is a host failure, not
evidence against the numeric controller. All 43 files from numeric003/004 were
copied locally and hash-matched. The owner approved a reboot after updates,
downloads and backup checks; no automatic-update settings will be changed.

Secondary model provisioning was overlapped with that work, without loading
either model on GPU. Both G0.5 archives match their retained publisher hashes;
all 16 Intern checkpoint/base-asset files match the retained manifest. Revisions
are those in `G05_BRINGUP_20261002.md` and `NATIVE_PILOT_20261002.md`.
G0.5 processor extraction and CPU inference export completed. The export hash
`3332c28a6feefbb8eec0309cda20b343e30566b40574fef5723f4351390ad799`
matches the previous host; 946 FP32 policy tensors are retained without weight
transformation. Download/export verification does not qualify either model's
runtime on this host. Launcher preload isolation/provenance tests also pass;
the complete CPU suite is 455 passed, not additional robotics phase completion.

### Approved Reboot And Resumption

- [x] Automatic updates exited; `dpkg --audit` returned clean. No update settings
  were changed and no benchmark workers remained live.
- [x] Approved reboot completed. Boot ID changed from
  `18415b34-a17f-4c48-8e46-faca217f1468` to
  `eb851cf8-e436-44f5-8d55-e32581ff77f8`; both 4090s report driver 580.178.04
  with working NVML and zero initial GPU allocation. Disk free: 121 GiB.
- [x] Restored G0.5 bundle matches all 13 retained artifact hashes. This does
  not replace model/runtime qualification on the rebuilt host.
- [x] `pi05-full-panel-numeric005`: finished after reboot with freeze004,
  explicit simulator C++ runtime, $95 shared ceiling and $3 cohort cap.
  All 6,390 actions/ACKs passed the retained integrity audit. Wall 35.29 minutes;
  settled cost $2.7378600 plus retained Flex hold $0.0538185. Five incomplete
  model stops are not native-scored failures. No demonstrated hierarchy benefit.
