# Physical Execution Lab: Research Progress Handoff

Snapshot: 2026-10-02 Japan time, updated after the every-chunk trial stopped. This is a
self-contained account of the current project, not the earlier BEHAVIOR,
EmbodiedSWE assembly, or FLUX branches. The every-chunk trial is now terminal
with a correction-contract error, not native task completion.

## Objective And Scope

Measure whether a generic execution harness improves physical task completion,
model-call count, cost, and wall time without task-specific scripts, new training,
or cross-episode solution memory. Compare frozen motor-only execution with
every-chunk semantic review and sparse semantic review. Separately compare
robot-policy-free direct dense versus direct sparse control.

Active RoboDojo policies are **G0.5 and the exact released pi0.5 checkpoint**.
Xiaomi RoboDojo is deferred. Intern was subsequently reopened for feasibility:
the two-GPU probe now loads and infers at about 820 ms/10-action chunk, with
native qualification pending (see `docs/INTERN_TWO_GPU_PROBE_20261002.md`).
The first fresh Intern tower0 motor-only episode completed successfully as
`runs/intern-two-gpu-native-001`: score 1.0, 727 actions, 73 policy calls,
489.11 s, zero paid calls. Executed code was commit `a3d4421`; its terminal
audit verifies all ACKs and native outcome. Both owned GPU workers exited.
Formal qualification and four remaining fixed-roster cases are pending.
See `docs/INTERN_NATIVE_PILOT_20261002.md`. The separate
official Xiaomi Robotics-1 RoboCasa365 track remains active.
Supervisor: **GPT-6.1 Sol, medium reasoning, Flex-only**. No automatic request
retry, provider/model fallback, or Standard-tier substitution.

## Locations And Reproducibility

- Public repository: https://github.com/AranKomat/physical-execution-lab
- Local checkout: `/Users/macbookpro/Developer/random/gpu/physical-execution-lab`.
- GPU host: `ssh -p 53210 root@92.180.27.84`; two 24 GB RTX 4090s.
- Remote checkout: `/root/physical-execution-lab`.
- Motor qualification/sparse evidence commit: `8ba161d`; this handoff was first
  published in `6196940`, with terminal every-chunk evidence added afterward.
- Historical motor-screen code fingerprint (not current HEAD):
  `8304dc48a8d6d1ddc46983de0c9aa107a09420e556a8b0362d01b9decdaeb233`.
- Experiment sequence/checklist:
  `/Users/macbookpro/Developer/random/gpu/PHYSICAL_EXECUTION_LAB_V4_HANDOFF.md`.
- Large verified backups: local `runs/native-evidence/`, not Git or actor memory.
- Small public evidence: `docs/evidence/`; detailed reports are linked below.

CPU verification now passes 295 tests, including two-GPU placement and bounded
EEF quaternion representation normalization. The latter fixes small quaternion
scale errors without changing translation/rotation/takeover gates; the original
every-chunk abort remains preserved and no corrected episode has been run.
See `docs/CORRECTION_QUATERNION_FIX_20261002.md`.
Release verification at `8ba161d` checked 880 files with no missing/changed bytes.
These checks do not establish robot competence or phase completion. Source
changes since the retained motor freezes require a fresh freeze before scored
comparisons; old records remain historical evidence, not current-source approval.

## Scientific Contract

Actor inputs are original instructions/public requirements, current RGB,
robot proprioception, robot-only FK, actual control receipts, and current-episode
history. Do not provide hidden object transforms, evaluator scores/success
geometry, future contact simulations, previous episodes, or task recipes.
Native evaluation is used separately for stopping/scoring, not as actor guidance.

RoboDojo uses the pinned GPT-as-Policy native server, original task assets,
dual ARX-X5 joint convention, and native DLS for EEF corrections. Three legal
RGB cameras are available; **no calibrated RGB-D interface has been ported**.
This is not a reproduction of the paper's Astra/Codex score, nor a real-world
safety claim. Simulation pauses during language-model inference.

Motor checkpoints have benchmark-specific post-training; report that separately
from the robot-policy-free conditions. Related development layouts are not
independent held-out tasks.

## Completed Motor-Policy Results

The fixed five-case RoboDojo development roster is sorting layouts 0/1/2 and
tower-building layouts 0/1, all source seed 0. Cases were not replaced after
observing outcomes.

| Policy | Sorting 0 | Tower 0 | Sorting 1 | Tower 1 | Sorting 2 | Success |
|---|---|---|---|---|---|---|
| G0.5 | Pass | Pass | Fail, score 0.4 | Pass | Fail, score 0.0 | 3/5 |
| Exact pi0.5 | Pass | Pass | Pass | Pass | Fail, score 0.0 | 4/5 |

Pi0.5 case details:

| Case | Native actions | Policy calls | Runner wall seconds |
|---|---:|---:|---:|
| Sorting 0 | 994 | 67 | 546.40 |
| Tower 0 | 714 | 48 | 410.64 |
| Sorting 1 | 755 | 51 | 419.40 |
| Tower 1 | 729 | 49 | 412.50 |
| Sorting 2, full-limit failure | 1100 | 74 | 599.14 |

All five pi0.5 episodes total 4,292 actions/289 policy calls with zero GPT calls.
The earlier seeded G0.5 pilot succeeded with 812 actions/51 policy calls;
an earlier unseeded pilot succeeded with 919 actions/58 calls. Do not pool
these extra pilots into the fixed screen's success denominator.

Matched independent-observation latency used the same retained RGB/proprio input,
three warmups and 30 measured samples, with no simulator running:

| Policy | p50 ms | p90 ms | p99 ms |
|---|---:|---:|---:|
| G0.5 | 801 | 841 | 889 |
| Pi0.5 | 454 | 488 | 523 |

These are blocking replay-inference measurements, not steady-state trajectory
timings. Pi0.5's reported 0.2134-second client construction is **not** model
startup time. Pi0.5/model and simulator colocated screening workers used about
15-16 GB per GPU. The screen supports retaining both policies, not a broad
claim that one is universally superior.

Reports: `docs/G05_DEVELOPMENT_SCREEN_20261002.md` and
`docs/PI05_DEVELOPMENT_SCREEN_20261002.md`.

## First Complete Supervised Episode: Negative Result

Run `runs/pi05-sparse-sol-flex-dev-001`, tower layout 0, same nominal development
case as the successful motor-only baseline:

| Condition | Success / score | Actions | Policy calls | GPT reviews | Wall s |
|---|---|---:|---:|---:|---:|
| Earlier motor-only | Yes / 1.0 | 714 | 48 | 0 | 410.64 |
| Sparse Sol Flex | No / 0.0 | 1050 | 93 | 27 | 807.82 |

Sparse reached the full native horizon with **no API or infrastructure error**.
It executed 1,045 motor actions and five one-action corrections, at steps
926/939/985/1004/1038. Reviews: one accept, 21 shorten, five correct.
There were 14 local-monitor interruptions; no unresolved policy actions.

All 27 API requests settled, actually serving Sol 6.1/Flex, costing **$0.25800075**.
Input/output tokens: 177,477 / 7,401; output includes 1,511 reasoning tokens;
cached input zero. Runner time included review waiting 229.35 s, environment
384.52 s, ACK transport 105.77 s, policy inference 51.72 s, and setup 24.90 s.

Audits verified nonvacuous evaluation, evaluator/controller agreement, all 1,050
contiguous ACKs, inference indices 0..92, and all source NPZ actions matching
the journal. Proposal accounting: 4,650 proposed = 1,045 executed motor actions
+ 3,605 discarded. The 88 shortened-chunk metric includes normal H50/15 prefix
discards; it is not 88 GPT interventions.

The case/environment/policy/runtime identities match the earlier motor run;
initial robot state matches exactly. Initial RGB is not byte-identical, with
per-camera mean absolute differences 0.384/0.293/0.307 out of 255. The earlier
baseline shared the host with another worker; sparse ran alone. Wall limits
were 3600 versus 2400 seconds, neither binding. This is a nominal development
comparison, **not exact physics replay or strong causal proof**.

Frequent shortening changes resampling times and policy RNG progression. That
is a plausible disruption mechanism, not a proven explanation. Corrections
executed but did not establish successful recovery. Do not optimize a tower
recipe or repeat the episode until it wins.

Full local archive verified 2,812 payloads with no mismatches. Tar's directory
mtime warning is recorded, not concealed. Report:
`docs/PI05_SPARSE_SUPERVISION_20261002.md`.

## Every-Chunk Review: Incomplete Contract-Error Result

Run `runs/pi05-every-chunk-sol-flex-dev-001` on the same tower development case,
using the same prepared pi0.5 provider, sensors, native controller, and action
bounds. Native horizon 1,050; at most 75 reviews; $3 local cap under $85 shared.
Model GPU 1, simulator GPU 0. Source, bridge and simulator are owned processes;
account credentials remain on the Mac behind the budget-enforced relay.

The trial stopped after **626 actual actions**, 625 motor actions and one
correction action, with 69 policy proposals. All **69 API requests settled**,
actually serving Sol 6.1/Flex, for **$0.65624150**. The journal contains 68 valid
reviews; the final response was rejected before a review could be accepted.
Valid decisions: three accept, 64 shorten, one one-action correction at step 625.
Error: **`EEF quaternions are unit wxyz`**. No malformed final action was
executed. There are 50 unresolved policy actions recorded at abort; do not
fabricate ACKs or relabel them as executed/discarded.
The rejected correction's left/right quaternion norms were 1.000056 and
1.013110. This is a specific normalization/validation failure, not a demonstrated
physical impossibility. No threshold was relaxed and no corrected response retried.

Runner wall time: **909.28 s**, including review waiting 532.92 s, environment
238.11 s, ACK transport 62.37 s, policy inference 40.53 s, setup 24.52 s.
Input/output tokens: 458,956 / 16,944, including 2,129 reasoning tokens;
cached input zero. No paid request remains unresolved from this trial.
Result status is `infrastructure_or_contract_error`, native score is null.
This is **not** a full-horizon failure, a native success, or a completed
three-condition physical comparison. It did not exhaust the 75-call limit.
Inspect the rejected correction and validation ordering before a new named
trial; never retry the uncertain episode or relax invalid-action checks merely
to finish it. All owned simulator/model/relay/tunnel processes are stopped;
both GPUs report zero memory usage. The terminal journal audit verifies all
626 contiguous ACKs, and all 69 source NPZ action arrays match their proposals.
Small terminal evidence is under `docs/evidence/pi05-every-chunk-sol-flex-dev-001/`;
the full local archive is `runs/native-evidence/pi05-every-chunk-sol-flex-dev-001-backup.tar.gz`.
All **1,975 archived payloads** match the terminal remote manifest; no missing
or changed files. This verifies evidence retention, not task completion.

Shortening can exhaust 75 calls before the native horizon. If so, report a
resource-limited result separately from full-horizon failure. Do not silently
raise limits, retry, substitute tiers, or feed the earlier episode to the actor.

Three-condition configuration freeze was generated and matches the unchanged
code fingerprint/full grouped manifest. This is preregistration/integrity,
not supervision/contact qualification or a held-out result.

## RoboCasa365 Results

Official `XiaomiRobotics/Xiaomi-Robotics-1-RoboCasa365` checkpoint/client, original
crop/history/action conversion; not the RoboDojo checkpoint. First full
CloseBlenderLid pilot succeeded at 286 actions. A fixed six-case development
screen yielded **2/6 success**, 7,845 native actions, 494 policy queries,
zero GPT calls, and no infrastructure errors. All four full-limit failures remain.
The first official-client chunk's 16 actions matched exactly in the parity check.

The first sparse kettle pilot executed one successful review and 50 actions,
then failed on Flex capacity at request two. It is incomplete, not a physical
task failure or a supervision benefit. Report:
`docs/XR1_DEVELOPMENT_SCREEN_20261002.md`.

## What Was Fixed Or Verified

- Native completion conditions are registered and nonvacuous; one ACK per
  actual action, correct camera/joint/quaternion/gripper conventions, robot FK.
- Generic EEF translation/hold/return probe passed 80 sequential actions;
  this is not contact or grasp qualification.
- G0.5 inference export preserves model tensors while avoiding training optimizer
  memory; BF16 fallback and isolated FLA-compatible runtime verified. Gripper
  clipping is explicit, measured and bound to the configuration.
- Exact pi0.5 checkpoint/normalizer access resolved; 18 inference files matched
  publisher hashes. Isolated OpenPI/JAX runtime loads and executes real episodes.
- Reviewed **motor-only** qualification records and full-manifest freezes exist
  for G0.5/pi0.5; XR1 motor freeze refreshed. Historical development labels remain.
- Intern stock BF16 startup exceeded an idle 24 GB GPU at 22.95 GiB allocated
  before model load completed. A subsequent explicit two-GPU component-placement
  probe now loads and completes inference; warm median 820 ms in three repeats,
  peak reserved 15.09/13.39 GiB. Intern's native competence remains untested.
  The successful inference probe's report export failed afterward; original
  error and exact completed-inference timings are preserved, not rerun/hidden.

Qualification reports: `docs/ROBODOJO_MOTOR_QUALIFICATION_20261002.md`,
`docs/NATIVE_FREEZE_UPDATE_20261002.md`, `docs/XR1_NATIVE_QUALIFICATION_20261002.md`.

## Phase Status And Next Work

| Stage | Status |
|---|---|
| Pre-GPU | Complete; CPU evidence only |
| A, native execution | Active RoboDojo motor-only interfaces qualified; supervision/contact remains separate |
| B, speed/quality screen | Complete for G0.5/pi0.5 on the fixed five-case development roster |
| C, matched harness | Partial: complete negative sparse result; every-chunk stopped on correction-contract error; broader matched and robot-policy-free direct comparisons unfinished |
| D, RoboCasa365 | Motor-only qualification/six-case screen complete; matched supervision unfinished |
| E, sensing/transfer | Deferred until useful matched physical results |

No held-out task episode has been opened. Eight untouched RoboDojo task groups
remain test; sorting and tower families are development. Next audit/back up
every-chunk and address its correction-contract issue, then use predefined matched conditions/subsets rather than more
baseline screens, component tests, new models, or task-specific fixes. Complete
robot-policy-free direct dense/sparse and XR1 matched supervision separately.

Direct-budget caveat: current dense template permits 180 decisions x five actions
= at most 900 actions, below tower/sorting horizons 1050/1100. Sparse permits
40 actions per decision. Equal calls are not equal attainable native horizons.
Select resource-limited versus full-horizon evaluation explicitly before executing
and interpreting that comparison; do not silently alter budgets.

## Operational Boundaries

Shared ceiling is **$85**. Before the every-chunk trial: 4,564 reservations,
$76.192461494300 spent plus holds, $8.807538505700 remaining. Every-chunk added
69 settled requests/$0.65624150. Authoritative post-trial ledger: **4,633
reservations, $76.848702994300 spent plus holds, $8.151297005700 remaining**,
154 unsettled reservations. Query the ledger before new work. Three prior Sol holds remain charged:
`g05-sparse-sol-flex-dev-001-0`, `g05-sparse-sol-flex-dev-002-0`, and
`xr1-supervision-kettle-001-1`. Acknowledgement enabled a new named trial, not a
retry or release of those holds.

Host storage was 7.3 GB free before this episode, 6.6 GB at an earlier live check.
Only two redundant remote backup archives were deleted after matching local
SHA-256s; raw episodes remain. Check disk before additional episodes/backups.
Preserve unrelated CPU workload and remote untracked `reports/` and
`launch_robodojo_case.py`. Do not reboot, stop the rental, alter system packages,
or terminate unrelated processes. Stop only owned workers after termination;
back up native traces, configs and source proposals locally, verify payloads,
and commit/push sanitized evidence. Do not publish credentials or raw API audits.

## Research Interpretation

There is real motor competence: multiple complete native successes, correct
provenance/control accounting, and a workable exact pi0.5 runtime. The first
complete supervision result is **negative**: more reviews and corrections did
not improve the tested task and increased wall time. It remains unknown whether
the generic harness helps weaker-policy cases, unseen tasks, or genuine recovery.
The core question is now an empirical matched comparison, not another model
download or architecture expansion. No real-world transfer, RGB-D benefit,
successful recovery, general safety, or broad leaderboard improvement is proven.
