# InternW0-Delta Two-GPU Feasibility And Speed

Owner reopened Intern feasibility after the earlier single-4090 load failure.
This is a bounded, model-only probe on the existing two 24 GB 4090 host, not a
new native task experiment or a completed policy comparison.

## Result

**Intern loads and performs valid action-proposal inference across both GPUs.**
The stock single-GPU failure is not a general two-GPU impossibility.

| Measurement | Result |
|---|---|
| CPU construction/checkpoint load and two-GPU placement | 158.54 s |
| First inference | 35.09 s |
| Three warm inferences | 0.8218 / 0.8203 / 0.8179 s |
| Warm median | 0.8203 s |
| Exposed action proposals per call | 10; all four calls pass the action contract |
| GPU 0 peak allocated / reserved | 14.99 / 15.09 GiB |
| GPU 1 peak allocated / reserved | 13.12 / 13.39 GiB |
| Native actions / paid calls | 0 / 0 |

This is about 82 ms per exposed action in the small warm probe. Retained
same-input screens measured G0.5 p50 801 ms/16 exposed actions and pi0.5 p50
454 ms/15 executable actions. Intern's three repeats are **not** a 30-sample
percentile study, and its two-GPU placement is a different resource condition.
The result is comparable in chunk latency to G0.5 and slower than pi0.5 here;
it does not establish a task-quality ranking or intrinsic model speed.

## Placement And Unchanged Components

The source loader originally placed everything on one CUDA device. The isolated
probe constructs the released model on CPU, loads the original checkpoint, then
places UMT5 text and RynnBrain VLM modules on GPU 0 and the coupled video/action
model, VAE and remaining modules on GPU 1. Tensor transfers at encoder boundaries
return features to GPU 1. No action/video layers were split across devices.

Parameter bytes: main 13,832,481,112; text 11,361,820,672; VLM 4,426,483,328.
Weights, BF16 precision, source processor/normalizer, three-view canvas,
seed 0, ten denoising steps, H32/replan10, and the already-used source PyTorch
causal-conv fallback remain unchanged. No quantization, smaller checkpoint,
task-specific code, or new package/system installation was used.

Observation is the same retained legal `runs/capture-005/observation.wire.json`
used in prior policy timing. Each call resets the source session; repeated input
and prompt/module caches are warm. **No actual ACKs or temporal motion history
were fabricated.** This is independent-observation timing, not recurrent WAM
rollout timing. Native simulator coexistence has not been measured with this
placement. Bitwise equivalence to a sufficiently large single-GPU reference is
not established.

The original provider identity is provenance, not approval of this new placement:
bind a distinct placement/configuration identity before a native comparison.
The probe lives outside production scripts and leaves existing code freezes valid.

## Preserve Both Probe Errors

Attempt 001 stopped because the probe assigned `device` on a frozen runtime
dataclass. The new attempt uses a replacement dataclass; no upstream source was
edited, and no inference happened in attempt 001.

Attempt 002 loaded and completed **all four** inferences, then its report export
incorrectly called nonexistent `Proposal.json()`. Consequently its original
`result.json` reports an AttributeError and process exit 1. Keep that file
unchanged. This is an export error **after** successful inference, not a GPU OOM
or inference failure. Exact completed-inference stdout timings are retained in
`docs/evidence/intern-two-gpu-probe/captured-timings.json`, alongside original
attempt records and the exact tested probe. No additional GPU rerun was needed
to recover already-logged measurements.

## Decision And Next Gate

Intern is reopened as a **feasible candidate pending native qualification**.
Do not discard it solely for the earlier single-GPU OOM. Also do not pool this
probe into the completed G0.5/pi0.5 development screen or mark its phase complete.

Next: make the explicit placement variant usable by the owned native launcher,
fix report serialization, bind artifacts/config/source, verify simulator memory
headroom, then run one bounded motor-only development episode. Preserve source
ACK semantics and document interruption/history-reset limitations. If native
competence is useful, add the fixed development roster rather than selecting
only cases on which Intern happens to win. GPU workers exited after the probe;
no rental, unrelated CPU workload, credentials, or shared API ledger was changed.
