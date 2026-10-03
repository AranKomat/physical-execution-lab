# All-Ten Semantic Instruction-Following Visual Review

## Question And Evidence

Does the RoboDojo-tuned pi0.5 checkpoint visibly follow GPT's current subtasks,
and do those instructions help? This review covers all ten tasks from the
completed `pi05-full-panel-semantic001` condition, not a new robot trial.
It used retained actor RGB from the head and both wrists, the actual prompt
epochs, and the recorded native outcomes. No paid calls or robot actions were
made for this review. No model weights were downloaded to the Mac.

The ten epoch contact sheets linked below were inspected. Closer H15 sequences
were also inspected for tower steps 435-555, imitation 450-615, Kong 90-210,
classification 210-330, language sorting 1005-1095, packing 840-960, table
organization 0-120, and bottles 0-90. These are **real retained simulator
observations, not generated images**. Each request is sampled once per normal
15-action prefix; the last retained policy-input frame usually precedes the
native terminal action. Neither the sheets nor their derived MP4s are continuous
physics recordings. Brief contacts, stable grasps, hidden bin placement and
exact geometric tolerances cannot always be established visually.

The raw images and every derived task MP4 remain locally in
`runs/pi05-semantic001-visual-audit001/`. `index.json` records exact prompt
epochs and sampled steps. `render_epochs.py` and `render_dense.py` preserve the
rendering code; they were run as operators in the repo's `runs/` directory.

## Summary

**Visible compliance is mixed, not absent, and not reliable enough for arbitrary
subtask control.** Folding, pink-bottle pickup and several packing/sorting
operations match their goals. There are also clear destination/object mismatches
and continued execution of other overall-task operations under a narrow goal.

This is not a clean test of language causality: most subtasks describe behavior
the policy already performs for the original task. A matching trajectory may
reflect a learned routine or a planner naming an action already underway. A
contradictory trajectory is stronger evidence that the current goal is not
reliably controlling behavior in this condition.

Prompt delivery is verified independently: full per-task text survives
tokenization, and actions/ACKs match the retained H50 predictions and native
H15 prefixes. No lost prompt, truncated subtask, cross-task routing error or
GPT-induced prefix interruption was found. This does not prove the model
understands the `Overall task` / `Current subtask` format as intended.

## Per-Task Review

| Task / Visual Evidence | Actual goal and visible behavior | Instruction following | Usefulness / limitation |
|---|---|---|---|
| [Arrange largest number](arrange_largest_number.jpg) | Goal: place 8 leftmost, then 7 second. Left arm handles 8 and it reaches the left pad by 210. During the 7 goal, the right arm handles 2; by 825 the visible order resembles 8702, with imperfect placement. | Early match; current 7 goal does not constrain subsequent actions or correct the ordering. | Sensible high-level goals, but the prolonged 7 instruction does not produce the requested correction. Planner stops at 840; no native score. |
| [Build tower](build_tower.jpg) | Initial left-block grasp/placement partly matches. Right-block goal begins at 420; a block is visible on the board by 450, but at 465-555 both arms carry and place another long board while the same block goal remains active. | Partial placement alignment, then clear continuation beyond the active subtask. | Goals lag the current physical phase. A planner's inability to verify the old goal need not mean no tower progress. Stops at 630; no native score. Upright stability is not certified by these views. |
| [Language classification](classify_objects_by_language.jpg) | Yellow car reaches the left white basket. Next goal explicitly requests green car in that basket using the left arm. Late frames show the green car in the middle blue basket and the right arm proceeding with other objects. | Clear destination mismatch after an initial correct placement. | The requested destination agrees with the original task, so this is a useful correction in principle, but it is not reliably obeyed. Native failure, score 0. |
| [Fold clothes](fold_clothes.jpg) | Left sleeve, right sleeve, then bottom-half folding goals match the visible folding sequence. | Strong visible sequence alignment. | No demonstrated gain: original-only also succeeds at 300 actions versus 298 semantic actions. Could be narration of an existing routine. Native success, score 1. |
| [Imitate sorting sequence](imitate_sorting_sequence.jpg) | Original-only until 525; then goal is blue remote first into foreground basket. The right arm was already acquiring a black rectangular device before 525; subsequent left-arm handling deposits a black rectangular device by 615 while the blue/gray buttoned remote remains on the table. | Apparent object mismatch; the issued goal arrives after acquisition has begun. | Planner's object/sequence interpretation may itself be wrong. This review does not certify the required demonstration order. Native failure at 622, score 0. |
| [Make Kong](make_kong.jpg) | After waiting, goal at 105 is grasp opponent's central face-up two-circle discard. At 105-210 hands manipulate the robot's own front row; the separate central discard remains visible. | Clear target-location mismatch in the inspected interval; no verified central acquisition. | Goal specifies a distinct useful target, but selecting the central tile is not demonstrated. Some matching-tile handling could still be part of the overall task. Native failure, score 0. |
| [Classify objects](classify_objects.jpg) | Toys reach white, watch blue, pens red. The policy exceeds grasp-only goals: first toys are already deposited by 210. During a right-arm toy goal, the last toy is transferred to the left arm by 285-300, then correctly placed under the updated goal. Both pens end up in red. | Strong category-level alignment, but not exclusive subtask or arm-level obedience. | Best candidate for benefit: native score 1 versus same-host original-only 0.4. One run cannot attribute this improvement to language; planner tracks and revises an ongoing multi-object routine. |
| [Organize table](organize_table.jpg) | Mouse-only goal remains active at 0-315, but left arm first moves the alarm clock and cactus; mouse eventually reaches its pad. Keyboard shifts toward its frame. From 525-990 a cactus-on-front-stand goal yields little visible movement; cactus was already near the rear stand by 315. | Eventual mouse alignment, clear execution of other tasks first, and no evident response to the final goal. | Likely stale/poorly grounded goal and weak exclusive control. The added `front` stand location is not established by the views. Native score 0.5, same as control. |
| [Pack box](pack_objects_into_box.jpg) | Right-hand shoe pickup and placement, car handling into box, then left-hand toothbrush pickup broadly match. Under toothbrush placement, 840-960 shows transport to the box edge, but the toothbrush remains outside; late frames show displaced box and toothbrush on table. | Good object/action alignment; physical placement/recovery failure rather than blanket instruction rejection. | Native score 0.25 versus same-host control 0.10: possible partial benefit, not established causally. Exact requested object orientations are not verified. Recovery was disabled. |
| [Bottles](put_bottles_into_dustbin.jpg) | Goal: pick up pink bottle with left hand. At 15-45 it is acquired and carried toward the left bin; by 60 pink is out of view. Right arm then handles yellow while pink-pickup goal remains active. | Clear initial pickup alignment; policy advances beyond active goal. Hidden disposal remains unverified. | Planner stops at 105 because it cannot verify placement and recovery is disabled. This is not evidence that pickup instruction failed. Original-only succeeds at 493 actions. |

These judgments are qualitative per-task assessments, not a calibrated numerical
instruction-following metric. Overall success and instruction compliance are
different: classification succeeds despite arm/phase deviations, while packing
can pursue the requested object yet fail physically.

## Same-Host Outcome Correction

The fresh original-only `baseline004` completed on the same rebuilt host with
the same screened runtime/layout roster: **2/10 success, mean native score 0.345**,
8,631 actions, 578 policy calls, 757.95 s including startup, zero paid calls.
All ten native terminal outcomes passed the retained routing/prefix/ACK audit.
The archive and independent local audit are documented in the baseline report.

Semantic001 has **2/10 success**, 7/10 native scores and three planner stops,
7,209 actions, 483 policy calls, 1,322.78 s, 74 settled Flex calls costing
$0.44593025. Its score bounds are [0.275, 0.575], not a full-panel point estimate.

Relative to this control, classification changes from score 0.4 to success,
packing from 0.10 to 0.25, folding stays successful, table stays at 0.5, and
bottles changes from success to a planner abstention. Thus **semantic is not
simply lower in success count on the same host**. Baseline003's earlier 3/10 and
0.44 remain valid historical results from a different installed host runtime;
they must not be presented as a clean matched contrast to semantic001.
Even the same-host runs are not action-by-action counterfactuals: inference RNG
stream consumption, concurrency and numerical/runtime variation can differ.
One layout and attempt per task cannot establish a hierarchy gain or loss.

## Diagnosis And Next Experiment

1. The current motor interface does not reliably prioritize a subtask over the
   overall task. There are visible contradictions, but not proof the checkpoint
   ignores language generally. The original pi0.5 paper includes semantic-subtask
   training; the RoboDojo-tuned checkpoint's external steerability is the question.
2. The planner sometimes names a grasp already in progress, remains on a goal
   after the policy has advanced, or adds uncertain arm/position constraints.
   Better goal selection and phase tracking are separate from motor compliance.
3. Planner abstention is a substantial confound, especially bottles. Lack of a
   visible deposit should not be described as verified physical failure.
4. Packing provides a genuine execution/recovery failure despite broad goal
   alignment. Better prompt delivery alone would not establish recovery.

Before attributing failure to lack of subtask training or funding training,
use a bounded counterfactual prompt test across the same ten-task roster:
original-only vs task-plus-subtask vs subtask-only from matched states, with
goals that distinguish object/destination choice where possible, identical
observation/RNG inputs, and short native rollouts to check visible effects.
Prediction differences alone are not obedience; different finite action arrays
are insufficient. Avoid contradictory instructions to the overall objective
unless explicitly labeled as a diagnostic rather than benchmark treatment.

The prepared recovery-only toggle remains **unrun**. It tests premature stops
and recovery, not exclusive motor steerability, and should not be described as
fixing all mismatches found here. No new run was launched during this review.
