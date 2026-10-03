# G0.5 Ten-Task Semantic Steering Screen

## Question And Scope

Does sparse GPT-6 semantic steering improve the released G0.5 RoboDojo
motor policy over its original task instruction? The owner selected a separate
original-only versus subtask-only/recovery comparison, without increasing GPT
frequency, adding task recipes, training, boxes or visual target crops.
GPT-6.1 Sol/medium keeps the full original task; the motor receives only the
current subtask, or the original instruction before a subtask is set.

Each condition runs ten distinct tasks concurrently with shared source-fused
B10 inference. This is one layout/attempt per previously opened task. It is not
an official whole-benchmark success rate, causal matched-state intervention
test, or untouched-task Phase E result. Do not merge it with the earlier
pi0.5 approach screen or five-case model screen.

## Original-Only Baseline

`g05-full-panel-baseline002` completed all ten native episodes, with no
controller/contract errors, unstable environments or censored scores.

| Task | Success | Native Score | Actual Actions |
|---|---|---:|---:|
| Arrange largest number | No | 0.15 | 1050 |
| Build tower | Yes | 1.00 | 744 |
| Classify objects by language | No | 0.00 | 1100 |
| Fold clothes | Yes | 1.00 | 301 |
| Imitate sorting sequence | No | 0.05 | 737 |
| Make Kong | Yes | 1.00 | 388 |
| Classify objects | Yes | 1.00 | 908 |
| Organize table | No | 0.75 | 1000 |
| Pack objects into box | No | 0.25 | 1300 |
| Put bottles into dustbin | Yes | 1.00 | 654 |

Five successes, mean native score0.62, 8,182 actions,516 motor predictions,
82 fused batches, zero paid calls,790.30 seconds including startup. Full-B10
warm inference median2.086 seconds. The source-native H32 prediction exposes
and executes16 actions at25 Hz; model configuration frequency30 is disclosed,
not silently substituted for the simulator rate.

The remote action/prompt/prefix audit passed. Independently rerunning it on the
local extracted evidence produced an identical audit, checking all8,182 ACKs
against source predictions. Native admission remains narrowly scoped to this
fixed simulator panel, not benchmark-wide qualification or real-world safety.

All ten baseline camera sheets were inspected. Failed arrangement still moves
digits to the pads, but the arrangement is wrong/incomplete. Language sorting
handles objects but misses the required assignments. Packing puts the shoe in
the box but leaves other objects outside. These are not evidence that the
policy cannot manipulate anything. The sparse three-frame sheets do not
establish the full contact sequence or every causal failure. Folding's native
success is an evaluator result, not a claim of human-quality folding.

### How The Five Baseline Tasks Failed

These observations were checked against denser retained-input montages as well
as the three-frame overview. They are visual descriptions, not privileged
state supplied to an actor or a complete causal diagnosis.

- Arrangement0.15: digits are grasped and transported, but7/2 crowd the area
  around the second pad and the third pad remains empty. This is incorrect
  final placement/order, not inability to reach or pick up the digits.
- Language sorting0.00: the yellow car goes into white, but wooden toys go
  into blue, the green car into red, and a watch into red. The task explicitly
  requires cars left/white, watches middle/blue, toys right/red. Handling works;
  object-to-destination assignment is wrong and remains uncorrected.
- Imitation0.05: the robot waits through the rear demonstrator and then picks
  and places objects, but does not successfully reproduce the demonstrated
  sequence. The sampled review does not establish every exact ordering error;
  temporal memory/selection and motor handling should not be conflated.
- Table0.75: the mouse, figurine and clock receive substantial correct handling.
  The keyboard remains outside the outlined target frame and the drawer stays
  closed in the late views. The full multi-stage task is incomplete; do not
  interpret0.75 as an exact count of completed human-defined subtasks.
- Packing0.25: the robot attempts the shoe, car and hammer, but placements are
  not all retained/completed in the required box orientation. The shoe is in
  the final box view while other objects remain outside. This includes handling/
  placement problems, not merely a missing high-level list of objects to pack.

## Completed Candidate

`g05-full-panel-subtask-recovery001` completed all ten native episodes:
three successes, seven failures, no planner stops, contract rejections, missing
scores or unstable environments. Mean native score0.38, 8,315 actions,
524 motor predictions,82 fused batches and1488.71 seconds including startup.

| Task | Original-Only Score | Subtask/Recovery Score |
|---|---:|---:|
| Arrange largest number | 0.15 | 0.15 |
| Build tower | 1.00 | 1.00 |
| Classify objects by language | 0.00 | 0.00 |
| Fold clothes | 1.00 | 1.00 |
| Imitate sorting sequence | 0.05 | 0.00 |
| Make Kong | 1.00 | 1.00 |
| Classify objects | 1.00 | 0.15 |
| Organize table | 0.75 | 0.25 |
| Pack objects into box | 0.25 | 0.00 |
| Put bottles into dustbin | 1.00 | 0.25 |

No new success or improved task score; tower, folding and Kong successes are
retained, classification and bottles successes are lost. This condition takes
about1.88 times baseline wall time without benefit on this opened panel.
Unlike several pi0.5 trials, the negative result is not explained by premature
planner abandonment or missing scores. Both score bounds equal the observed
mean because all ten terminal scores are present.

78 settled GPT-6.1 Sol Flex calls cost$0.47742675; no Standard fallback or
new unresolved hold occurred. Four recoveries were issued/accepted, each
changed the motor goal, and none produced task success. All ten actual motor
prompt streams, retained token boundaries, source predictions and native ACKs
passed the integrity audit. This rules out the audited routing/cadence faults,
not every software bug or ineffective learned conditioning.

Native prefix lengths, motor sampling and history remain unchanged. Review
target100 is checked at the next drained H16 boundary, normally112 actions.
Recover requires a failed assessment; uncertain ordinary replanning remains
allowed subject to minimum goal dwell. GPT's stage-completion claims are not
independent physical verification.

The paid relay uses Flex preferred, with the approved same-model Standard
fallback only after explicit no-output Flex capacity rejection. Existing holds
remain charged; $3 cohort/$95 shared reservation ceilings remain in force.
No generic provider retry or uncertain physical-write retry is allowed.

Initial retained predictions differ between baseline and candidate for all
ten rows; nine initial motor prompts differ (imitation initially continues on
the original instruction). Reset proprioception matches exactly, but rendered
RGB does not match bitwise. Those differences and the shared RNG prevent
interpreting this as a same-state causal language intervention or proving that
each changed trajectory follows its subtask.

### Visual Candidate Review

All ten candidate goal-epoch sheets were inspected. Some initial actions align
with the requested goal, but important later corrections do not:

- Language sorting: a watch-to-blue instruction is followed by handling a
  wooden toy and putting it in blue. Later car-to-white corrections leave the
  car in blue. Different output vectors are not evidence of correct obedience.
- Ordinary classification: the requested watch-to-blue placement instead puts
  the watch among the toys in white. The recovery asks to remove it, but the
  robot proceeds to handle pens in red while the watch remains in white.
- Packing: after a shoe-placement attempt leaves the shoe outside, the accepted
  re-grasp instruction persists from336 through1296, without recovered success.
- Table: the planner keeps requesting mouse placement while the robot works on
  the figurine/clock, then repeatedly handles the figurine after mouse corrections.
  Working on a different valid stage is not inherently a global-task mistake;
  imposing a planner's stage order can add unnecessary interference.
- Bottles: early disposal/handover behavior occurs, but later requested white
  bottle pickup does not complete; the robot handles the green-labeled bottle
  instead. Instructions prescribing a particular arm may also conflict with
  the motor's normal handover routine. That factor is not isolated here.
- Arrangement: the recovery correctly identifies the2 outside its third pad,
  but repeated placement/re-grasp requests are followed by little useful motion.
- Tower/folding/Kong: successes are retained, often with similar native action
  counts to baseline. Their success does not establish a new hierarchy gain.
- Imitation: GPT initially continues on the original task because the sequence
  is not yet established, then supplies an object goal; the native result fails.

The observed limitation is unreliable steering under this external-language
condition, not a proof that all language is ignored, G0.5 cannot manipulate, or
every mistake originates in the motor. Planner staging, grounding, incomplete
temporal evidence and the checkpoint's conditioning distribution remain factors.

## Completed Mistake-Only Coaching

The owner proposed letting G0.5 perform its own task and supplying feedback only
when a visible mistake occurs. This is a useful separate condition, not another
name for continuous subtask-only steering. Fresh006 completed all ten native
episodes:5/10 successes, mean0.605 versus baseline5/10,0.620. All five baseline
successes were retained without coaching; no failed task was rescued and no
task score improved. Three correction goal changes, no feedback clears or
verified completed correction. Native prompt/token/prefix/ACK audit and local
hash-verified backup/independent audit passed. All ten retained-input task sheets
were inspected.61 successful GPT-6.1 Sol/medium/Flex calls plus17 authorized
same-model Standard calls after capacity rejection cost$0.57825750, with the
$0.0701385 capacity hold retained. Opened single-attempt screen, not official SR,
untouched-task generalization or a causal language test.

Coaching003 remains transport-censored (six scores/four unknown), and005 remains
credit-censored (two scores/eight unknown); do not merge either into006's result.
See [the completed fresh-run report](G05_COACHING_FRESH_RUN_20261003.md) and
[the implementation checklist](G05_MISTAKE_ONLY_COACHING_20261003.md).

The tested condition keeps the original instruction and adds a short temporary corrective note
only for an original-task violation, lost grasp, repeated failed placement or
clear stall. Do not call another valid stage a mistake merely because GPT
preferred a different stage order. Avoid unnecessary arm/trajectory prescriptions.
Use within-episode observations/error notes, not another episode's solution memory.

Example: retain the sorting task and append "The watch is in the red basket;
watches belong in the middle blue basket. Move that watch to blue." Then return
to the original task after the correction is visibly completed. Compare with
the same original-only panel; score recovered effect and disturbance to already
successful tasks separately. Do not use evaluator scores to trigger coaching.

Fewer interventions do not automatically mean fewer GPT observation calls:
someone still needs to notice the error. Use sparse visual checks/available
honest event signals, not a claimed zero-cost semantic detector. This may reduce
distribution shift and disruption, but current ignored recovery goals warn that
reliable corrective-language execution is not guaranteed. If it fails, stop
language sweeps and investigate a supported learned conditioning interface,
target context, native reasoning checkpoint or post-training as separate factors.

## Paper And Interface Boundaries

See [the paper review](G05_PAPER_AND_COMPARISON_20261003.md) for
[arXiv:2608.11739](https://arxiv.org/pdf/2608.11739). The foundation starts
from Qwen3.5-2B, not GPT-5. Native AR reasoning, externally supplied stage
instructions and target visual context are distinct factors.

The saved specialist configuration explicitly has `discrete_action=false`,
`continuous_action=true`, `action_attend_cot=false` and `predict_cot=false`.
The deployed adapter supplies task text and the three ordinary camera images.
This screen does not qualify an internal subtask/box generator, an AR action
head, or visual-target-crop conditioning. Source support for other modes is
not proof that this checkpoint can use them reliably. A negative external
language result would not refute the paper's R1-Lite AR+reasoning results.

## Evidence And Provenance

Local root: `/Users/macbookpro/Developer/random/gpu/physical-execution-lab`.
Remote root: `/root/physical-execution-lab` on the authorized Romania host.
Published compact audits, decisions and API receipt:
[`../evidence/g05-full-ten-comparison001-20261003/`](../evidence/g05-full-ten-comparison001-20261003/).
Evidence lives under `runs/g05-full-panel-baseline002/`; reviewed sheets/videos
under `runs/g05-baseline002-visual-review001/`. Those videos are sampled real
camera inputs per H16 prefix, not continuous physics capture or generated views.

Full baseline archive, including the setup-only baseline001 failure, original
preparation and environment receipt: `runs/g05-full-panel-baseline002-evidence.tar.gz`.
Remote/local SHA256 matches:
`d78a06d1f21d94853db8aefc16b6d1cc432cddf37fc89fcf9bf544dfb250bc34`.
No model weights were downloaded to the Mac.

Candidate full evidence is locally hash-verified/extracted, and independent
local integrity audit matches the remote audit exactly. Archive:
`runs/g05-full-panel-subtask-recovery001-evidence.tar.gz`, SHA256
`154779c6ea317bd5318bc899b737ce2cf3a7eb98b1fe562f9595db5378f3bb77`.
Candidate goal sheets/videos: `runs/g05-subtask-recovery001-visual-review001/`.
All owned experiment processes exited and both GPUs reported0 MiB used; the
host was not rebooted/stopped and unrelated CPU work was not touched.
Shared ledger after this cohort:5578 reservations, $87.094163494300 charged
including all holds, $7.905836505700 remaining under95. No new cohort hold.

Baseline001 failed before policy predictions/actions because an ancillary
`external/env_cfg` alias was absent. Restoring the alias verified all three
retained ancillary hashes; no checkpoint/config was changed. Baseline002 uses
the previously successful simulator-only libstdc++ preload. Keep baseline001
as an infrastructure attempt, not ten robot failures.

Both conditions were frozen before baseline outcomes:
`9d67c5d2bf3ac3f468386245383224c860b1ffe6ff80492d4592221e0b554c30`.
After baseline completion, adding only the offline semantic audit and renderer
required snapshot
`7c4f42c2344fca33f8ed5be4166e5c570b972a6dd909d2803b2f173f08d3f468`.
A file-by-file comparison found no changed/removed bound files, only those
two additions. Frozen conditions and admission core are unchanged.

Fused inference uses one seed0 RNG stream, with inference-only padding as
tasks retire. It does not establish independent per-environment streams or
singleton numerical parity. History is restricted to one source observation;
arbitrary recurrent checkpoints are not qualified. The restored environment
uses Python3.10.18 versus the earlier3.10.19; package versions were retained.

## Remaining Work

- [x] Complete, audit, independently back up and inspect original-only baseline.
- [x] Complete and audit the subtask/recovery candidate; retain stops/errors.
- [x] Back up candidate evidence and inspect all actual goal epochs.
- [x] Report paired task scores, coverage/bounds, latency, calls/cost and failures.
- [x] Complete, audit, back up and inspect independently frozen mistake-only
  coaching006; preserve the earlier censored attempts and their holds separately.
- [ ] Untouched tasks, replication, second backend, causal matched-state
  steering and asynchronous execution remain unfinished.
