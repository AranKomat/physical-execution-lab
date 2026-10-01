# G0.5 Five-Case Development Screen

## Scope

RoboDojo now uses G0.5 and the exact pi0.5 checkpoint only. Xiaomi RoboDojo and
Intern are out of active scope; Xiaomi RoboCasa365 remains a separate track.

The five-case roster was fixed in `b5a0cf2:docs/EXPERIMENT_PROGRESS.md`, before
the four new runs. Sorting layout 0 is the previously completed seeded FLA
pilot. The older unseeded PyTorch pilot is **not** another row in this screen.
All five are development cases from two related task families, not held-out
tasks or an estimate of general RoboDojo performance.

## Complete Native Results

| Case | Success | Native score | Actions / limit | Policy calls | Runner wall s |
|---|---|---|---|---|---|
| Sorting layout 0 | Yes | 1.0 | 812 / 1100 | 51 | 475.09 |
| Tower layout 0 | Yes | 1.0 | 718 / 1050 | 45 | 432.75 |
| Sorting layout 1 | No | 0.4 | 1100 / 1100 | 69 | 653.75 |
| Tower layout 1 | Yes | 1.0 | 729 / 1050 | 46 | 420.37 |
| Sorting layout 2 | No | 0.0 | 1100 / 1100 | 69 | 630.36 |

**3/5 successes**, no missing outcomes or infrastructure errors. Task-weighted
success is 66.7% (sorting 1/3; tower 2/2). Mean available native score is 0.68.
These are descriptive numbers; related layouts are not independent tasks.
The generic report's Wilson interval does not establish task-level generalization.

Totals: **4,459 actual actions**, **280 policy calls**, **zero GPT/API calls**,
**zero corrections**, and 178.36 simulated seconds. Mean runner wall time was
522.47 s. Runner time includes reset and execution, not the full model-service
and simulator launch overhead. Summed episode time is not concurrent batch time.

Both failures reached the original native limit and were retained without
automatic retry, a replacement layout, or task-specific repair code. The final
sorting-layout-1 image visibly retains a tool outside the bins. This supports an
incomplete physical outcome, but does not by itself explain every scoring rule
or prove a purely perceptual, control, or semantic cause.

## Runtime And Timing

All rows use the BF16/FLA 0.5.1/FM/explicit-gripper-clip variant, policy seed 0,
source joint control, 16-action exposure, legal three-camera RGB and proprioception.
The policy's frequency setting remains 30 while native control is 25 Hz. This
is an explicitly labeled runtime condition, not silent retiming or source-score
reproduction. Clipping magnitudes and exact ACKs are in the per-case audits.

Four new cases ran on two isolated mutable policy sessions: GPU 0 handled the
two tower layouts; GPU 1 handled sorting layouts 1 and 2. Each had its own
simulator, RPC ports and output directory. The worker's full GPU usage observed
during execution was approximately 18-19 GiB, not a continuously measured peak.
CPU, disk and backup activity were shared. Do not rank runtimes using these
concurrent episode times as though they were isolated measurements.

Thirty independent-observation replay samples after three warmups measured
p50/p90/p99 **800.99 / 841.25 / 888.68 ms**, mean **803.90 ms** per exposed
16-action proposal. Replay used `capture-005`; temporal state was reset between
samples. Both native simulators had finished; backup I/O overlapped the replay.
Reported allocated/reserved peaks were about 11.00 / 11.75 GiB over the policy
service's lifetime, not newly isolated replay-only memory peaks. Reported cold
model load was 55.11 s from initial server startup, which overlapped peer setup.

An earlier replay invocation referenced absent `capture-001/observation.wire.json`
and failed before inference. Its log is retained as an input/setup failure, not
a policy or native task attempt. The corrected invocation used a fresh output.

Simulator/observation work remains the largest measured episode component.
The successful physical behavior is more informative than a kernel-only timing
win: the policy solves both tested tower layouts but fails two sorting layouts.

## Verification And Binding

Per-case audits check controller/evaluator agreement, nonvacuous native completion
registration, journal hash chains, sequential ACKs, seed provenance, and proposal
disposition counts. These are offline checks; evaluator scores do not enter control.
They are not automatic proof of sensor legality, safety, or physical grasp quality.

Full native traces/video are local under `runs/native-evidence/`; original remote
episodes are retained. Each backup is checked against the remote per-file hashes.
Only small results, audits, the fixed roster and a generated report are public:
[evidence and aggregates](evidence/g05-development-screen/report/aggregates.json).

Before future formal comparisons, the provider preparation now binds ancillary
embodiment files by hash and the wrapper rejects changed/missing files before
model loading. Linking the source embodiment config during earlier provisioning
changed lookup from the built-in fallback to the source file. Both resolve exactly
`arm_dim=[6,6]`, `ee_dim=[1,1]`; the source config's nominal batch size is 10, but
single-observation `get_action()` does not use that batch fallback, and inference
batch size was explicitly 1. This equivalence was source-inspected. The new
binding changes identity metadata, not weights or control parameters; future
matched conditions must all use the same newly bound provider identity.

## Next Experiments

- Retain G0.5 for matched motor-only / every-chunk / sparse comparisons. The
  minimum five-case development screen is complete; do not repeat wording sweeps
  or add task-specific repair recipes in response to these failures.
- Bind qualification evidence and freeze the matched conditions. Verify the
  shared correction interface before treating hybrid/direct control as qualified.
- Confirm the authorized GPT-6.1 Sol Flex route and bounded paid-call accounting;
  unresolved prior reservations must not be silently discarded. No paid trial
  has occurred in this project yet.
- Begin a bounded development supervision pilot, then use a predefined held-out
  subset for the actual matched result. Development failures are not held-out wins.
- Exact RoboDojo pi0.5 remains unavailable; do not substitute a generic checkpoint.
- Official Xiaomi RoboCasa365 native baseline and supervision remain unstarted.

The G0.5 part of Stage B now has actual five-case quality evidence and warm timing.
Stage C is next; the overall research goal is not complete.
