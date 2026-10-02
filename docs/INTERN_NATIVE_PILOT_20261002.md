# InternW0-Delta Native Two-GPU Pilot

## Result

Intern fits across two 24 GB RTX 4090s and completed one fresh motor-only
RoboDojo development episode successfully. This establishes feasibility, not
formal native qualification or a five-case quality ranking.

| Measurement | Result |
|---|---:|
| Case | build_tower__standard__g0__l0 |
| Native success / score | true / 1.0 |
| Actual native actions | 727 |
| Policy calls / GPT calls | 73 / 0 |
| Runner wall time | 489.11 s |
| Simulated time | 29.08 s |
| Policy inference, including first-call cold work | 91.00 s |
| Environment / ACK transport / setup | 283.77 / 79.75 / 25.98 s |
| Proposed / executed / discarded actions | 730 / 727 / 3 |
| Corrections / interruptions / unresolved actions | 0 / 0 / 0 |

The earlier pi0.5 motor-only tower0 episode succeeded in 714 actions, 48 calls,
410.64 s. Intern took about 19% longer on this nominal development case.
This is not exact physics replay, a matched multi-case comparison, or evidence
that either policy is generally better.

## Speed And Memory

The preceding same-input feasibility probe measured three warm proposals at
0.8218 / 0.8203 / 0.8179 seconds per 10 exposed actions, after a 35.09-second
first inference. The native pilot includes recurrent observation/ACK history;
its aggregate inference time is not a warm percentile measurement.

Observed simulator-plus-policy GPU usage during the pilot was approximately
22,245 MiB on GPU 0 and 14,198 MiB on GPU 1. These are sampled usage readings,
not allocator peak measurements. GPU 0 has limited headroom. Both GPUs returned
to zero reported memory usage after owned workers exited.

Keep the extra hardware explicit: Intern uses both GPUs, whereas G0.5/pi0.5
can each coexist with a simulator on one GPU. Do not assume two independent
Intern episodes fit simultaneously. No quantization or upstream source edit
was used. See [the placement probe](INTERN_TWO_GPU_PROBE_20261002.md).

## Protocol And Audit

Run: `runs/intern-two-gpu-native-001`; executed repository commit `a3d4421`.
Provider identity:
`394659607b7e3ac495709696825b1e7e27c5c05188bfa15aeceb1c395bbd86bf`.
The policy uses original BF16 weights, source preprocessing/normalization,
seed 0, H32/replan10 and ten denoising steps. Encoders reside on GPU 0;
the coupled video/action model and VAE reside on GPU 1. The simulator sees
only physical GPU 0. Source/model CPU threads were limited to four.

The fresh case was the first lexically sorted case in the existing fixed
development roster, selected before seeing the result. Original action limit
1050, wall limit 3600 seconds. No paid requests, privileged actor inputs,
task-specific scripts, demonstrations, or cross-episode solutions were added.
Native evaluator state was inspected only after terminal completion.

The offline audit verifies 876 journal events, 727 contiguous ACKs, 73
seed-tagged proposals, nonvacuous native evaluation, matching controller and
evaluator outcome, and complete proposal disposition. Additional wrapper
gripper clipping was zero. The upstream WAM adapter clips grippers internally
before returning actions; its pre-clip values were not retained by this probe.
Therefore zero wrapper clips does not prove zero upstream clipping.
This bookkeeping audit does not certify every sensor boundary, physical
safety, or production qualification. Original result is `native_unqualified`.

Small public evidence: `docs/evidence/intern-two-gpu-native-001/`.
Full local evidence: `runs/native-evidence/intern-two-gpu-native-001/`.
Its terminal remote per-file checksum list is retained alongside that directory.
All 1,848 original terminal payloads were verified locally with zero checksum
failures. The later qualification record/verification is retained separately
with the small public evidence.

## Prospective Motor Qualification

The exact resolved motor-only config
`67e2d947ff0497c0d33724ef9937bfe60949af59ad68a8c4f4324b78b18a687a`
now has an evidence-reviewed software-contract qualification record. Artifact
bytes were rehashed on the host; nine hashed pilot/source files verify. Reviewed
checks cover reset/render, native joint14 convention, nonvacuous completion,
legal sensor/instruction input, actual observation ACKs and 25 Hz native timing.
The upstream `_adapt_obs`/`_ingest` consumes current RGB/joints and acknowledges
pending actions; it does not ingest object transforms, rewards or other episodes.

This is prospective motor-only approval, not GPT correction qualification,
hardware safety certification, published-score reproduction or a completed
quality screen. The original pilot's `native_unqualified` label is unchanged.
A fresh current-source freeze remains required before scored runs.

## Next

Retain Intern as an active feasible candidate. Complete the current-source
freeze and the remaining four cases of the predefined five-case
development roster; retain all failures. Do not extend the roster to favor
Intern or reopen held-out tasks prematurely. The principal harness comparisons
remain unfinished; this successful motor-only pilot is not a supervision gain.
