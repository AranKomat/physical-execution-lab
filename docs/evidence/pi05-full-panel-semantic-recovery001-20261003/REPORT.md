# Full-Ten Semantic Recovery Screen

## Frozen Condition

Completed 2026-10-03 on the same two-4090 host and fixed ten-task roster as
baseline004, semantic001 and subtask001. All ten distinct tasks ran concurrently
under one shared pi0.5 fused-vmap service and three native simulator groups.
The only behavioral configuration change from task-plus-subtask semantic001 is
`allow_semantic_recovery=true`. Planner stops remain permitted. Native H50
predictions/H15 execution, task layouts/horizons, three legal RGB cameras,
Sol6.1/medium and the source-bound controller remain fixed. No numeric control,
privileged object/evaluator inputs, training or target-task recipes were added.

Freeze: `91f5bf8cac215e420986f77756e0c1c7787962786b6ac0fce5ca744bfea46548`.
The source/config remained unchanged throughout execution. This is a one-attempt
per-task descriptive screen, not an official RoboDojo success-rate estimate,
identical-state counterfactual or causal recovery qualification.

## Results

| Task | Outcome | Native Score | Actual Actions | Accepted Recovery Goal Changes |
|---|---|---:|---:|---:|
| arrange_largest_number | Native failure | 0.15 | 1050 | 2 |
| build_tower | Native failure | 0 | 1050 | 3 |
| classify_objects_by_language | Native failure | 0 | 1100 | 4 |
| fold_clothes | Native success | 1 | 300 | 0 |
| imitate_sorting_sequence | Native failure | 0 | 620 | 0 |
| make_kong | Native failure | 0 | 600 | 0 |
| classify_objects | Native success | 1 | 772 | 2 |
| organize_table | Native failure | 0.50 | 1000 | 1 |
| pack_objects_into_box | Planner stop | Unavailable | 1050 | 2 |
| put_bottles_into_dustbin | Recovery contract rejection | Unavailable | 105 | 0 |

**Two successes, six native failures, one planner abstention, one contract-censored
case.** Native score coverage is 8/10; full-panel mean bounds under [0,1] are
**[0.265, 0.465]**, not a point estimate. Neither missing score is a zero-valued
physical failure. The same-host original-only baseline has two successes and
all ten scores, mean 0.345. Task-plus-subtask semantic001 also has two successes,
with three planner stops and score bounds [0.275, 0.575]. Subtask-only001 has
one success, four stops and bounds [0.185, 0.585]. These screens do not establish
a reliable ranking or hierarchy benefit.

## Execution, Cost And Integrity

- 7,647 actual native actions, 512 motor predictions, 40 motor prompt changes.
- 15 issued recovery requests, 14 accepted recovery goal changes, one rejected
  recovery. Issued operations are counted from actual model responses, not just
  accepted semantic events; the rejected bottle operation is retained.
- All ten live reset admissions, model-boundary prompt text/token retention,
  retained source H50 predictions, native H15 cadence and actual ACKs passed
  the offline audit. All ten episodes have nonzero motor prompt evidence.
- Zero numeric corrections, GPT-induced motor resampling, history resets,
  prefix shortening or unresolved physical actions. Native terminal early
  prefixes remain distinct from GPT interventions.
- 1,429.0326 seconds (23.82 minutes) including startup. Simulation pauses during
  synchronous planner waits; this is not uninterrupted real-time execution.
- 78 provider reservations: 77 completed responses, 19 served Flex and 58
  served Standard on the same `openai/gpt-6.1-sol` model. The explicitly
  authorized Standard fallback followed a no-output Flex capacity rejection.
- Settled cost $0.85177500; the capacity reservation
  `pi05-full-panel-semantic-recovery001-19` retains its $0.06436800 hold.
  Total charged with this new hold is $0.91614300. All earlier shared holds
  remain; $3 cohort and $95 shared ceilings are unchanged. No generic retry,
  model substitution or retry of an uncertain physical write occurred.

Service tier is not identical to the earlier Flex-only completed screens:
the authorized same-model fallback is disclosed, not hidden as a matched
latency/cost factor. Record integrity is not full benchmark qualification or
bitwise source-singleton equivalence.

## Important Negative And Censored Evidence

The bottle model requested `recover` at step 105 with assessment `uncertain`:
redirect the right hand to yellow-bottle disposal after pink left view. The
existing contract only accepts recovery when assessment is `failed`. This
operation was rejected before changing the motor goal; zero bottle recoveries
were accepted. It is not a successful recovery, checkpoint refusal or physical
pickup failure. Honest uncertainty and the recovery/assessment dependency
need a clearer interface, not a fabricated failed assessment or a silent gate
relaxation during a frozen experiment.

Packing first failed to acquire the requested car, then accepted a replacement
shoe-grasp goal at step 315. A second recovery at 945 requested grasping a
toothbrush for reorientation. The planner ultimately stopped at 1050, before
the native 1300-action horizon. More execution than subtask-only's stop at 210
does not itself establish useful recovery, correct orientation or native success.

Classification succeeds with two accepted recoveries, but also succeeded in
both earlier semantic formats without recovery. Folding succeeds without
recoveries, as it did in the original-only control. Number arrangement remains
at baseline score 0.15 despite two recoveries; language sorting remains at 0
despite four; table remains at 0.50 despite one; tower reaches 0 despite three.
Accepted replanning is not proof that the motor followed it or that it helped.

## Preservation And Visual Review

Remote audit completed before archival; no audit-file creation overlapped the
archive operation. The raw archive is
`runs/pi05-full-panel-semantic-recovery001-evidence.tar.gz`; remote SHA-256:
`a3d42991da7f5b15095cde5d01a526d5b416a06213da774732774a7cc6977988`.
The downloaded local hash matches exactly. The extracted run independently
passed the revised audit; local and remote JSON receipts match exactly and are
published beside this report. No model weights were copied to the Mac. Owned
workers/relay/tunnel exited; both GPUs report zero allocated MiB. No reboot,
global package change or unrelated CPU-worker intervention was made.

All ten goal-epoch contact sheets were inspected. These are real retained head
and wrist observations, not world-model images or continuous physics video.
`visual-index.json` gives exact epochs and sampled steps; derived MP4s remain
local in `runs/pi05-semantic-recovery001-visual-audit001/`. The renderer is the
unchanged operator published with the subtask-only evidence.

| Task / Sheet | Visible response and limitation |
|---|---|
| [Number arrangement](arrange_largest_number.jpg) | Early 8/7 placements match. Wrong third/fourth ordering persists; after the step-735 goal to remove 0 from the third pad, late retained views show no correction. |
| [Tower](build_tower.jpg) | Some blocks reach a board, then both hands carry boards under block-placement goals. Crossed boards and loose blocks remain; late replacement grasp goals show no visible restoration. |
| [Language classification](classify_objects_by_language.jpg) | Yellow reaches white. Green is handled by both arms but ultimately reaches blue despite repeated white-basket goals. The final request to move green from blue to white shows no verified correction before native failure. |
| [Folding](fold_clothes.jpg) | Left/right/bottom goals broadly match the successful folding sequence. Original-only also succeeds; no recovery was used. |
| [Imitation](imitate_sorting_sequence.jpg) | Native demonstration proceeds under original text. The later blue-remote grasp goal arrives while a different black device is already being handled and placed. Demonstration-order interpretation is not certified by these sheets. |
| [Kong](make_kong.jpg) | Own front-row tiles are manipulated under the central-discard acquisition goal; central acquisition is not verified. |
| [Classification](classify_objects.jpg) | Category placement is correct. The remaining doll transfers from right to left before its replacement left-placement goal; pens enter red after goals update. Broad alignment, but planner tracking of an ongoing routine and causal language benefit remain distinct. |
| [Table organization](organize_table.jpg) | Clock/cactus move under mouse goal; keyboard subsequently moves. The late cactus placement/regrasp goals show no visible response. The added front-stand location is not established by these views. |
| [Packing](pack_objects_into_box.jpg) | Initial car goal yields shoe acquisition. Shoe, car and other objects later reach the box; some actions precede corresponding goal updates. Late toothbrush reorientation/regrasp views show no verified change. Physical packing progress is not native success or proved recovery benefit. |
| [Bottles](put_bottles_into_dustbin.jpg) | Pink pickup/transport matches, then yellow is handled while the pink goal remains active. Hidden disposal is uncertain; the rejected recovery is not present as a motor goal epoch. |

Late no-response observations are a recurring practical steerability limit,
not proof that every action or every language instruction is ignored. Strong
matching sequences often align with the original policy's routine; clear
object/destination contradictions are more diagnostic of weak exclusive control.

The published offline operator is a provenance copy of
`runs/operator_audit_full_panel_recovery001.py`, where it was executed. Its
repository-root assumption reflects that execution location; copying it under
`docs/evidence/` does not make that directory the repository root.

## Next Boundary

Keep the all-ten negative and censored evidence. This recovery toggle did not
resolve external semantic steerability. The owner's visual instruction-following
check is summarized in
[the consolidated review](../../semantic/PI05_INSTRUCTION_FOLLOWING_REVIEW_20261003.md).
Do not repeat old scoped shadow/tokenizer tests or launch minor prompt sweeps.
Before a larger hierarchy claim, the outstanding discriminating question is
whether useful contrasting goals cause corresponding physical effects from
matched states; checkpoint sensitivity and matching routine actions alone
cannot answer that. Layout replication and untouched/second-backend work
remain separate unfinished phases.
