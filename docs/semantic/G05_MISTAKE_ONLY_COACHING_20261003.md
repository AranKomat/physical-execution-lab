# G0.5 Mistake-Only Coaching

## Frozen Question

Can sparse observed-error feedback rescue baseline failures without disrupting
G0.5's own stage selection? Original-only baseline002 is 5/10 successes, mean
native score0.62. Subtask-only/recovery001 is 3/10, mean0.38, with four accepted
recovery goal changes but no recovered task success. Neither is official SR.

The next condition keeps the exact original task and appends a short temporary
`Correction:` note only after an observed original-task violation, lost grasp,
repeated failed placement or sustained stall. `recover` requires `failed`;
uncertain future mistakes and another valid stage do not qualify. Ordinary
`set_subtask` is forbidden. `clear_feedback` requires active feedback, observed
completion and an empty goal; it restores the original instruction byte-for-byte.
Stop remains incomplete abstention, not success. Evidence gates validate the
interface; whether the claimed error/completion is visible requires visual review.

The motor core, source G05 BF16/FM artifact, cameras, cases/layouts/horizons,
H32 prediction/H16 executed prefix, ACK history and shared B10 seed0 RNG remain
unchanged. Review target100 is checked at the next drained H16 boundary,
normally112. Same GPT-6.1 Sol/medium/Flex-preferred route and authorized capacity
fallback; $3 cohort/$95 shared cap, retaining unresolved holds. Simulation still
pauses for inference. No claim of fewer GPT checks or asynchronous execution.

Preemptive feedback is a separate future condition, not included here. No
task-specific examples, recipes, previous-run solutions, extra crops, boxes,
hidden state or evaluator scores are supplied to the actor.

## Checklist

- [x] Implement explicit correction prompt mode and observed-failure/clear gates.
- [x] Preserve legacy planner schema and default state behavior.
- [x] CPU verification:477 passed, including no-error action-stream parity and
  correction/clear cycles with unchanged ACK history. Not native phase completion.
- [x] Review baseline transfer: no file in cohort-admission CORE was edited;
  contracts/state/planner add opt-in language behavior only. Default original
  prompt remains exact and native motor wrapper/control/batching are unchanged.
- [x] Deploy reviewed sources while GPUs idle; create a separate preparation
  and new source freeze before outcomes. Preserve all historical freezes.
- [x] Launch all ten distinct tasks concurrently; scored003 was transport-censored,
  not restarted or replayed.
- [ ] Complete the full-ten coaching comparison; four native scores are missing.
- [x] Audit retained model prompts, decision gates, prediction prefixes and ACKs;
  partial-trace integrity is not proof of a completed comparison.
- [x] Hash-verify a complete local evidence backup and independently rerun audit.
- [x] Review all task/feedback epochs; distinguish issued instructions, followed
  corrections, rescued successes and harm to baseline-successful tasks.
- [x] Publish partial results and stopping decision; do not expand language sweeps if
  corrective execution remains unreliable.

Untouched-task Phase E, supported target/native-AR conditioning, motor
post-training, second backend and asynchronous native planning remain unfinished.

## Preparation And Admission

Implementation commit `94478ea` is pushed. Remote pre-edit hashes matched that
commit's parent for all five deployed files; no unrelated changes were replaced.
New preparation `runs/g05-mistake-only-preparation001` was frozen before the
coaching run, SHA256
`b7f2cd0fa98a50c4a56dd9aa836250e087ddc53e868ce824840d25a28ea1030f`.
The retained baseline source/config/controller transfer check passed, including
all eight unchanged motor CORE files and87 controller evidence files. Live reset
admission passed before actions. Host was idle with99GB free.

Bounded run `g05-full-panel-mistake-coaching001` was interrupted by loss of the
SSH/reverse tunnel during startup. Reconnection verified all three native
admissions, zero action-journal rows and zero provider reservations. Only its
owned parent was interrupted; its finally block retired the owned worker/sims.
Terminal parent status is `error_stop_no_retry`/KeyboardInterrupt,774.84 seconds;
the underlying transport failure is recorded separately from that cleanup code.
All five PIDs were absent and GPUs0MiB before launching separately named002.
No physical write or paid request was replayed;001 is not ten motor failures.
Startup002 failed before remote cohort launch because the orphaned001 reverse
tunnel still bound19861. Its remote owner43139 was identified by listener and
09:42:18 start time, then retired without touching other SSH sessions. Startup002
also made zero provider reservations or robot actions. Separately named003 ran
under the unchanged condition/pre-outcome freeze; its censored result is below.
Startup001/preparation archive is hash-verified locally:
`ab774ba571878216f854442e79c2806c2915687dbccee8e299f7c28d64a408f4`.
Prelaunch ledger:5578 reservations, $87.094163494300 charged including holds,
$7.905836505700 remaining under95. All prior unresolved holds are retained.

## Scored003: Transport-Censored, Not A Full Comparison

All ten reset bindings passed. The SSH/reverse tunnel dropped during execution;
the local relay then retired. Reconnection verified the original remote parent
was still alive. Only that owned parent was interrupted, invoking its cleanup;
the owned orphan tunnel was subsequently retired. No uncertain physical write,
failed paid request or scored episode was retried. Both GPUs0MiB, no owned worker
or tunnel remained. Unrelated CPU work and instance lifecycle were untouched.

macOS records clamshell sleep at19:24:13 JST and full wake at19:30:11, aligned
with this transport interruption. The relay and budget ledger live on the Mac;
it must remain awake/lid-open during future remote paid cohorts. A temporary
idle-sleep guard was used during backup only; it cannot defeat lid closure and
no persistent power/network/security setting was changed. Do not mistake the
2172.81-second interrupted parent wall time for an efficiency comparison.

| Task | Baseline Score | Coaching Native Result | Actions | Correction Changes |
|---|---:|---|---:|---:|
| Arrange largest number | .15 | Missing/censored | 1008 | 1 |
| Build tower | 1 | Missing/censored | 1008 | 0 |
| Language sorting | 0 | Missing/censored | 1008 | 4 |
| Fold clothes | 1 | Success, score1 | 299 | 0 |
| Imitate sequence | .05 | Failure, score0 | 637 | 0 |
| Make Kong | 1 | Success, score1 | 388 | 0 |
| Classify objects | 1 | Success, score1 | 845 | 0 |
| Organize table | .75 | Failure, score0 | 1000 | 1 |
| Pack objects | .25 | Missing/censored | 1008 | 0 |
| Bottles into dustbin | 1 | Failure, score.4 | 700 | 0 |

7,901 actual actions,496 exposed motor proposals and six accepted correction
changes. No feedback clears; all retained prefixes are drained. Score coverage
is6/10, three known successes and three known failures, four unknown outcomes.
Success fraction bounds on the planned ten are[.30,.70]; mean-score bounds are
[.34,.74], assuming missing scores in[0,1]. There is no observed full-ten mean
or valid 3/10 success rate, and no ranking against the baseline can be inferred.

74 provider reservations:73 settled Flex calls/$0.41987675, one unresolved
`g05-full-panel-mistake-coaching003-73`/$0.072471 retained in full. No tier
fallback occurred. The relay's73-attempt summary precedes the uncompleted74th
reservation; the shared ledger is authoritative. Charged cohort total including
hold$0.49234775. Shared5652 reservations/$87.586511244300 charged with all holds,
$7.413488755700 remaining under95. No hold was released or acknowledged for a
new paid run. Parent `paid_calls=0` is a stale startup field, not actual usage.

## Visual Findings And Limits

All ten retained-camera sheets were inspected, including all correction epochs:

- Language sorting: toy-to-blue error at336 is visible. After feedback, the
  robot handles the green car rather than moving the toy, and puts the car in
  blue. Later watch goes to white and another toy to blue. By992 the requested
  corrective transfers remain undone and red is empty. GPT identifies visible
  errors, but corrective execution is not demonstrated. Later notes accumulate
  several misplaced objects, adding complexity; this is not a single-target
  causal ablation. The native terminal score remains unknown.
- Arrangement: the2 is on/near the second pad at448. After correction the
  robot handles7/0 while2 remains there; the requested relocation is not visibly
  achieved by992. Another valid stage is not itself a mistake, and the final
  score is unknown; do not equate a still-needed correction with task failure.
- Table: the cactus/pot stays tipped through the correction period. The clock
  receives later handling, but the drawer is closed and keyboard remains outside
  its outline in late views; native score0. Correcting a claimed stall did not
  produce verified task completion. Native0 does not mean no object was handled.
- Folding, Kong and ordinary classification retain native success without any
  correction; these are not coaching gains. Folding is evaluator success, not
  a claim of human-quality folding from the bunched-garment image.
- Bottles loses baseline success without any correction; the table looks mostly
  clear, but that does not establish all bottles reached the correct dustbin.
  Imitation also fails without coaching. These demonstrate uncoached trajectory
  variation, not proof that corrective language caused those regressions.
- Tower and packing show substantial uncoached handling; packing shows a shoe
  in the box late. Both are censored, not scored failures or successes.

No gained success or completed correction is observed, but the incomplete trial
does not establish a negative full-panel effect. RGB reset equality and
independent per-environment RNG remain unproved; this is not a matched-state
causal feedback experiment. Do not respond with more prompt wording sweeps or
more frequent GPT calls. Stabilize the local relay's awake-host requirement
before another paid condition. Supported learned conditioning/target context,
native reasoning or post-training remain distinct future factors, not fixes
silently imported into this frozen-policy comparison. Preventive coaching has
not been implemented or tested.

## Backup And Audit

Archive `runs/g05-mistake-coaching003-evidence.tar.gz`, remote/local SHA256:
`2785d3fc39d54dedf4c2704b5d2e185d9fee97eb9aea6d753e9b341454c19b35`.
The full local extracted backup includes all ten actual actor inputs, source
predictions, journals/ACKs, available terminal records and preparation/freeze;
no model weights were downloaded. Independent local partial audit equals the
remote JSON byte-for-byte. It checks retained evidence only, preserving four
missing result files instead of fabricating terminal results. Renderer now labels
those cases `missing_result_interrupted` and still shows their legal frames.
Source audit/renderer additions occurred only after the cohort was stopped;
they do not rewrite the original pre-outcome source freeze.

Published compact evidence:
`docs/evidence/g05-mistake-coaching003-20261003/`.
Local visual index: `runs/g05-coaching003-visual-review001/index.json`.
