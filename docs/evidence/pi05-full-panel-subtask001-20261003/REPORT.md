# Full-Ten Subtask-Only Prompt Ablation

## Condition

Completed 2026-10-03 on the same two-4090 host as baseline004 and semantic001.
All ten distinct fixed standard-layout tasks ran concurrently with the shared
pi0.5 fused-vmap motor runtime and three native simulator groups. The only
behavioral configuration change from semantic001 is `prompt_mode`:
`task_plus_subtask` to `subtask_only`. Recovery remains disabled; planner
abstention remains available. Sol6.1/medium/Flex, legal observations, native
H50/H15 cadence, task horizons and layouts remain fixed. Before an active goal
exists the motor falls back to the original instruction, as defined by V5.

Freeze: `da84e38f13000335dd30da9b410b87cbfa84413bc20be0ea4d22963de4585444`.
Semantic config: `edc85abd6ed94126ac981ae845a456701d36ca693125646adfde76c230e10d6c`.
Retained native transfer and all-ten live reset admission passed before actions.
No weights, task recipes or privileged object/evaluator signals were added.

This is a practical full-roster format comparison, **not an identical-state
counterfactual or official RoboDojo success-rate estimate**. Changing only the
configuration does not make the sampled planner decisions, observations or
motor RNG-stream consumption identical between runs.

## Outcomes And Same-Host Contrast

| Task | Original-Only Baseline004 | Task-Plus-Subtask Semantic001 | Subtask-Only001 | Subtask-Only Actions |
|---|---|---|---|---:|
| arrange_largest_number | Failure, 0.15 | Planner stop, no score | Planner stop, no score | 630 |
| build_tower | Failure, 0.30 | Planner stop, no score | Failure, 0.10 | 1050 |
| classify_objects_by_language | Failure, 0 | Failure, 0 | Failure, 0 | 1100 |
| fold_clothes | Success, 1 | Success, 1 | Failure, 0 | 500 |
| imitate_sorting_sequence | Failure, 0 | Failure, 0 | Planner stop, no score | 0 |
| make_kong | Failure, 0 | Failure, 0 | Failure, 0 | 600 |
| classify_objects | Failure, 0.40 | Success, 1 | Success, 1 | 727 |
| organize_table | Failure, 0.50 | Failure, 0.50 | Failure, 0.75 | 1000 |
| pack_objects_into_box | Failure, 0.10 | Failure, 0.25 | Planner stop, no score | 210 |
| put_bottles_into_dustbin | Success, 1 | Planner stop, no score | Planner stop, no score | 105 |

**One verified success, five native failures, four planner abstentions.** No
API, contract or controller errors. Native score coverage is 6/10; full-panel
mean bounds under [0,1] are [0.185, 0.585], not a point estimate. Unavailable
scores are not zero-valued physical failures. Do not report 1/6 as full-panel
success rate or compare scored-subset means as matched full-panel results.

Classification remains successful under both semantic formats, a useful
candidate for benefit but not a causal proof from one layout. Table gains
partial score, while folding loses an established success. This screen does
not support replacing task-plus-subtask with subtask-only by default.

## Execution And Integrity

- 5,922 actual actions; 397 motor predictions; 21 motor prompt changes.
- 62 provider reservations, 62 settled Flex calls, $0.36038075 total.
  No standard fallback or new unresolved hold; prior holds remain retained.
  The $3 cohort limit and authorized $95 shared ceiling are unchanged.
- 1,148.7722 s (19.15 minutes) including startup. Synchronous planner waits
  pause simulation; timing is not uninterrupted real-time robot performance.
- Zero numeric corrections, semantic recoveries, GPT-induced motor resamples,
  history resets or prefix shortening.
- All ten journals/results pass the source-prediction/native-ACK integrity audit.
  Actual subtask-only request text and full-token retention are checked on all
  **nine episodes with motor predictions**, not claimed on the zero-action
  imitation case. The audit proves routing and cadence, not goal obedience.

The revised audit explicitly counts `motor_predictions_checked` and reports
`episodes_with_motor_prompt_evidence=9`. The first audit is preserved inside
the raw archive; its universally true empty-stream prompt flag is not used as
evidence that the imitation task ever received motor inference.

## Planner Stops

- Imitation, step 0: the planner saw no demonstrated order yet and stopped rather
  than letting the native support demonstration proceed. No motor prediction
  or action occurred. This is planner behavior, not checkpoint noncompliance.
- Packing, step 210: the requested car remained on the table while the policy
  lifted the shoe. GPT cited failed car acquisition and disabled recovery.
  Unlike semantic001, this run initially selected the car, not the shoe.
- Bottles, step 105: the pink bottle left view and the gripper appeared empty;
  the planner could not verify pickup/disposal and cited disabled recovery.
  Hidden disposal is not automatically physical failure.
- Number arrangement, step 630: retained evidence records an incomplete planner
  stop; its precise visible sequence is assessed in the visual section below.

## Visual Assessment

All ten epoch sheets were inspected against the actual goals. These are real
retained head/wrist RGB, not generated images or continuous physics video.
Normal sampling is one policy input per H15 prefix; the last input generally
precedes the terminal action. The imitation sheet repeats only its reset actor
view and is explicitly labeled zero actions, not a trajectory.

| Task / Evidence | Visible response to active goal |
|---|---|
| [Number arrangement](arrange_largest_number.jpg) | 8 and 7 reach their first two pads. Under a third-pad 2 goal, final arrangement instead resembles 8702. Early alignment followed by incorrect ordering; native score unavailable because of stop. |
| [Tower](build_tower.jpg) | Left white block is handled and placed on a board. The policy then handles more blocks/boards before goal updates; final structure is disturbed. Mixed goal alignment and stability failure, not universal instruction rejection. |
| [Language sorting](classify_objects_by_language.jpg) | Yellow car reaches white basket. Under green-car-to-white goal, the arm instead handles a wooden toy near blue basket; at 1095 green is still being handled near the right edge. Requested green placement is not verified. |
| [Folding](fold_clothes.jpg) | Left sleeve is folded and the right arm has started handling the other side by 315, when the planner finally switches goals. Late cloth is compact but native score is 0. The views do not identify the exact failed scoring criterion. Broad folding behavior is not proof that isolated subtask control succeeded. |
| [Imitation](imitate_sorting_sequence.jpg) | No active subtask, motor prediction or action; only initial view. Planner refused to wait for the demonstration. Motor following cannot be evaluated here. |
| [Kong](make_kong.jpg) | Central discard remains separate while hands manipulate the robot's front-row tiles under a central-discard grasp goal. Target acquisition is not verified. |
| [Classification](classify_objects.jpg) | Toys go to white, watch objects to blue, pens to red; overall category alignment is strong. More objects are handled than the active narrow goal names, and arm/phase constraints are not exclusive. Native success. |
| [Table organization](organize_table.jpg) | While mouse goal is active, left arm moves clock/cactus. Under keyboard goal the cactus is still handled, then keyboard shifts. At final figurine goal it is already at the stand and robot remains largely still. Clear overall-task continuation and stale planner phase tracking. |
| [Packing](pack_objects_into_box.jpg) | Explicit car-grasp-only prompt, but right arm instead acquires and lifts the shoe while the car remains on the table. Strong object-choice mismatch even without overall-task text. |
| [Bottles](put_bottles_into_dustbin.jpg) | Pink bottle is acquired/carried toward the bin by 45; it later leaves view and right arm handles yellow. Initial pickup aligns, but hidden disposal remains unverified. Planner stops at 105 rather than allowing continuation. |

Derived MP4s, every sampled step and full goal epochs are retained locally in
`runs/pi05-subtask001-visual-audit001/`; `visual-index.json` records provenance.
The public operator copies preserve the exact rendering/audit/preparation
sources; they were executed as `runs/operator_*.py` in the repository, not as
native control code. No visual match is counted as causal language obedience.

## Preservation

Remote raw evidence is retained at `runs/pi05-full-panel-subtask001/`.
Clean completed archive: `runs/pi05-full-panel-subtask001-evidence.tar.gz`.
Remote and downloaded local SHA-256 matched:
`cfcb2b253912da6c1b60dc8e2fba6496c84bbf3134dd8b60a72997be31d3fa39`.
The extracted local run independently passed the revised audit, receipt
`runs/pi05-full-panel-subtask001-local-audit002.json`, exactly matching the
remote `runs/pi05-full-panel-subtask001-remote-audit002.json`. Both revised
audit receipts are published beside this report. No model weights were copied
to the Mac. Owned relay, tunnel and workers have exited; both GPUs report zero
allocated MiB and the local short-lived token is removed.

The initial archival attempt overlapped audit-file creation and returned a
changed-directory warning. It was not accepted as a completed backup. The
clean archive above was produced only after the first audit had finished.

## Next Work

Keep task-plus-subtask as the working semantic format. Do not spend on further
minor prompt sweeps or conclude the model needs training from this screen.
The already-prepared recovery-only ablation remains source-bound and unrun;
it changes `allow_semantic_recovery` to true, retaining task-plus-subtask and
the same ten-task roster. It is the next meaningful check of premature stopping
and useful semantic replanning, not a proven fix for motor steerability.

Multiple preselected layouts, reliable language causality, generalization and
second-motor/backend hierarchy comparisons remain unfinished. The earlier
synchronous stateless pi0.5 shadow cadence/prompt qualification passed on the
scoped development case; a fresh full-ten fused-runtime shadow was not run.
Do not describe that earlier qualification as unfinished or as bitwise parity.
This negative full-roster result is substantive experiment progress, not
completion of the V5 objective.
