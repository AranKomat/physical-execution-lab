# Pi0.5 Instruction Following Across Ten Tasks

## Answer

The RoboDojo-tuned pi0.5 checkpoint shows **mixed, nonexclusive subtask
following**, not dependable control by arbitrary language goals. The existing
all-ten recordings answer the owner's requested observational check without
another prompt sweep, model download or paid review. Actual prompt delivery,
full tokenizer retention and native action acknowledgements passed independent
audits. A delivered prompt is not necessarily an obeyed prompt.

This review combines the retained task-plus-subtask (`semantic001`) and
subtask-only (`subtask001`) screens. Each has one attempt per fixed task/layout;
these are not repeated success-rate measurements or identical-state
counterfactuals. All ten epoch sheets were inspected, alongside the closer H15
sequences documented in the task-plus-subtask visual report. Real head/left
wrist/right wrist observations are sampled at motor input boundaries, not
continuous physics video; hidden deposits and brief contacts remain uncertain.

## All-Ten Findings

| Task | Does the visible behavior match? | Is the instruction useful? |
|---|---|---|
| Arrange largest number | 8 and 7 reach the first two pads. Under the subsequent 2-on-third-pad goal, the subtask-only final arrangement resembles 8702. Early match, later ordering mismatch. | The desired order is useful, but the current goal does not reliably correct the ordering. Both semantic formats stop before native scoring. |
| Build tower | Initial block operations partly match; the robot handles other blocks/boards before the narrow grasp/place goal changes. Subtask-only ends with a disturbed structure. | Broadly reasonable steps, but late phase updates and nonexclusive execution make their benefit unclear. |
| Classify by language | Yellow car reaches white. Task-plus-subtask puts green in blue despite a white-basket goal; subtask-only handles a wooden toy under the green-car goal and never verifies the requested placement. | Correct object/destination instructions are useful in principle, but the observed corrections are not reliably followed. Both native scores are 0. |
| Fold clothes | Broad left/right/bottom folding sequence matches in task-plus-subtask. Subtask-only also folds, with the right side already underway when its goal changes. | Could be narration of a learned routine. Baseline and task-plus-subtask succeed; subtask-only fails. Views do not establish the precise failed criterion. |
| Imitate sorting sequence | Task-plus-subtask handles a different rectangular device after the requested blue-remote goal arrives during acquisition. Subtask-only stops at reset, before any motor prediction. | Planner timing/interpretation are confounds. The zero-action case is not evidence of checkpoint noncompliance; the demonstration should not be skipped. |
| Make Kong | Hands manipulate the robot's front-row tiles under the goal to acquire the separate central discard; central target acquisition is not verified. | A distinct target is identified, but it does not visibly steer acquisition in the inspected sequence. Both native scores are 0. |
| Classify objects | Categories broadly align: toys white, watches blue, pens red. The robot exceeds narrow goals and changes arms. Both semantic formats succeed. | Best candidate for benefit: baseline score 0.4 versus semantic scores 1. Still not causal proof from one attempt. |
| Organize table | Clock/cactus are handled under mouse/keyboard goals; a final figurine goal remains active after the figurine is already near a stand. | Stale goals and uncertain added location details reduce usefulness. Scores: baseline 0.5, task-plus-subtask 0.5, subtask-only 0.75. |
| Pack box | Task-plus-subtask broadly matches shoe/car/toothbrush operations but fails toothbrush placement. Subtask-only explicitly requests the silver car, yet the right arm lifts the shoe while the car remains on the table. | Clear evidence against reliable object-level steering even without overall-task text. A placement/recovery failure is separate from wrong-object execution. |
| Bottles into dustbin | Pink pickup and transport toward the bin align; the robot then handles yellow while the pink goal remains active. Hidden disposal is not verified. | Initial instruction is reasonable, but disabling recovery leads to a premature planner stop. Baseline succeeds; neither stop proves physical pickup failure. |

## What This Establishes

- **Strongest negative evidence:** car versus shoe, white versus blue basket,
  central discard versus front-row tiles, and unrelated table operations under
  a narrow active goal. These are behavioral mismatches, not missing prompt bytes.
- **Positive evidence is weaker:** many matching subtasks name operations that
  the original policy already performs, sometimes after acquisition begins.
  Matching behavior alone does not establish language causality.
- **Not all failures are instruction rejection:** grasp/placement mechanics,
  stale or wrongly grounded planner goals, hidden outcomes and premature stops
  are distinct explanations. Imitation's zero-action case is not a motor test.
- **Subtask-only is not a demonstrated remedy:** one success versus two for
  task-plus-subtask and the same-host original-only control. Do not claim that
  removing original-task text fixes competing learned routines.
- **Do not conclude pi0.5 lacks subtask training:** the original model includes
  semantic-subtask training. External steerability of this RoboDojo checkpoint
  under this interface is what remains unestablished.

Usefulness cannot be decided solely by watching one successful trajectory.
The observations support possible classification benefit and clear limits on
exclusive goal control; they do not support a reliable hierarchy gain or a
blanket claim that language is ignored.

For a closer same-host visual contrast, the original-only baseline was also
rendered from its retained inputs. Its classification end view shows a doll in
red and pens in blue, whereas both semantic conditions place these categories
correctly. In packing, baseline starts with the shoe too: subtask-only's
car-request/shoe-action mismatch is consistent with continuation of that
learned task routine, but does not establish the checkpoint's internal cause.
Those baseline sheets/videos and step index are retained in
`runs/pi05-baseline004-visual-audit001/`. Their frames, like the other renderings,
are observations rather than complete physical-state checkpoints.

## Evidence And Next Boundary

- [Task-plus-subtask all-ten visual review](../evidence/pi05-semantic-visual-audit001-20261003/REPORT.md): actual goal epochs, dense sequences and linked sheets.
- [Subtask-only all-ten screen](../evidence/pi05-full-panel-subtask001-20261003/REPORT.md): outcomes, linked sheets and independent prompt/ACK audits.
- [Same-host original-only control](../evidence/pi05-full-panel-baseline004-20261003/REPORT.md): two successes, all ten native scores, mean 0.345.

Derived sampled-frame MP4s and their epoch/step indices are retained locally in
`runs/pi05-semantic001-visual-audit001/` and
`runs/pi05-subtask001-visual-audit001/`. No generated world-model images are used.

The separately frozen recovery-only full-ten run is in progress at the time of
this review. It tests evidence-triggered replanning and premature stopping,
not causal instruction following. In its bottle episode, the planner emitted
`recover` with assessment `uncertain`; the existing contract requires `failed`,
so the goal was rejected at step 105. This is a contract-censored outcome,
not an accepted recovery or physical failure. Other tasks have accepted recovery
goal changes; their physical effect must be assessed after completion.

A same-state contrasting-goal diagnostic would be required for a stronger
causal steerability claim. It is not a prerequisite to reporting the clear
contradictions already observed, and no such additional trial was launched here.
