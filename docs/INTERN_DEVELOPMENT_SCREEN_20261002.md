# InternW0-Delta Fixed Development Screen

## Protocol

Same five source-seed-0 development cases as G0.5 and exact pi0.5: sorting
layouts 0/1/2 and tower layouts 0/1. The original tower0 pilot supplies that
roster entry; the four remaining cases are not replacement attempts. No paid
calls, task-specific scripts, privileged actor geometry, added demonstrations,
or cross-episode solutions. Native evaluator information is isolated from
control and inspected offline after terminal completion.

The original pilot executed `a3d4421`; the continuation executed `a1a73e9`.
Same unchanged BF16 checkpoint, source preprocessing, seed0, H32/replan10 and
ten denoising steps. Policy identity:
`394659607b7e3ac495709696825b1e7e27c5c05188bfa15aeceb1c395bbd86bf`.
Resolved motor config:
`67e2d947ff0497c0d33724ef9937bfe60949af59ad68a8c4f4324b78b18a687a`.
The continuation reuses one loaded policy server, resetting episode context,
with a fresh native simulator for each case. Source/model OMP/MKL threads: four.
All original results remain development / `native_unqualified`; later software
qualification does not rewrite their labels.

## Outcomes

Completed five-case screen: **3/5 success**, 4,470 actual actions and 448 policy
calls, zero GPT calls. Both sorting failures reached their full native horizons.

| Case | Success | Score | Actions | Policy calls | Runner wall s |
|---|---|---:|---:|---:|---:|
| Sorting 0 | Yes | 1.0 | 817 | 82 | 538.50 |
| Tower 0, retained pilot | Yes | 1.0 | 727 | 73 | 489.11 |
| Sorting 1 | No, full horizon | 0.15 | 1100 | 110 | 725.55 |
| Tower 1 | Yes | 1.0 | 726 | 73 | 478.47 |
| Sorting 2 | No, full horizon | 0.0 | 1100 | 110 | 717.19 |

No failed case is replaced. A partial score is not success. Extra pilots,
inference probes, and CPU tests do not enter the success denominator.

## Matched Inference Timing

Same retained RGB/proprio input corpus as G0.5/pi0.5:
`f3e1076981d294aa02fe75bdfbe361e087bc468b36dbede53594de4de2ccf461`.
Loopback transport, three warmups, thirty measurements, no simulator running;
backup I/O overlapped timing in these screens. Independent-observation timing
resets temporal memory and is not steady-state recurrent rollout throughput.

| Policy | p50 ms | p90 ms | p99 ms |
|---|---:|---:|---:|
| G0.5 | 801 | 841 | 889 |
| Exact pi0.5 | 454 | 488 | 523 |
| InternW0-Delta | 1114 | 1160 | 1188 |

Intern mean: 1113.52 ms, ten exposed actions/query, model load 156.53 s.
Median query latency is about 1.39x G0.5 and 2.45x pi0.5. Different exposed
horizons prevent treating those ratios as total task-throughput ratios. Earlier
approximately 820 ms direct-probe timing used a different measurement boundary;
it is not the matched loopback result. Pi0.5's 0.2134 s bridge-construction field
is not its model startup time.

## Resource Difference

Intern requires both 24 GB cards in this tested BF16 placement: UMT5/RynnBrain
encoders on GPU0, coupled video/action model and VAE on GPU1. The native simulator
also uses GPU0. Observed pilot coexistence was 22,245/14,198 MiB; GPU0 has limited
headroom. Timing-only allocator lifetime peak allocated/reserved bytes were
15,829,340,160 / 15,936,258,048 on GPU0 and
14,091,672,576 / 14,373,879,808 on GPU1, excluding simulator coexistence.
This is component placement, not a single pooled 48 GB device. No quantization
or upstream source edit was used.

G0.5/pi0.5 can each coexist with a simulator on one GPU and therefore support
two independent screening workers. Intern cannot be assumed to do so. Wall
time includes native stepping, observation transport, policy inference and
setup, but excludes initial model-service startup. Simulation is paused during
inference; this is not a moving-world real-time result.

## Evidence And Limits

Pilot backup: 1,848 original payloads verified. Continuation terminal backups:
sorting0 2,071, sorting1 2,777, tower1 1,844, sorting2 2,777 verified payloads.
All continuation payload hashes were independently reverified before publishing
the small evidence subset. Both owned screen/harvest processes exited normally;
both GPUs then reported zero memory usage. Contiguous
ACKs, seeded proposals, nonvacuous evaluation and controller/evaluator agreement
pass. This is bookkeeping/provenance, not automatic safety or independent
visual task scoring. Upstream Intern clips grippers internally; zero wrapper
clips does not establish zero upstream clipping.

Complete local traces: `runs/native-evidence/intern-fixed-screen-001/`, with
pilot separately under `runs/native-evidence/intern-two-gpu-native-001/`.
Remote native sensor NPZ copies are retired only after local checksums and remote
bytes verify; results, journals, action receipts and local originals remain.
Small public result/audit/timing evidence: `docs/evidence/intern-fixed-screen-001/`.

These related development layouts are not independent held-out tasks, and the
different historical host contention/source commits are not exact physics
replay. No broad leaderboard or generalization claim follows from this screen.
Do not add cases after inspecting failures to improve the headline rate.

## Next Gate

The same roster yields G0.5 3/5, pi0.5 4/5 and Intern 3/5. Retain pi0.5 as the
primary matched-supervision policy and G0.5 as a secondary comparison. Keep
Intern's implementation/evidence available, but do not expand its screen:
there is no demonstrated development success advantage to offset slower
matched inference and its two-GPU occupancy. This is a development resource
allocation choice, not a claim that Intern is universally worse.

Refresh exact motor qualifications and source/full-manifest freezes, then
return to matched semantic supervision and direct control, not more model
candidates or repeated tower attempts. A successful motor screen is not
evidence that GPT review improves behavior.
