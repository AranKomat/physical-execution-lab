# First Native Motor-Policy Pilot

## Result

**G0.5 motor-only succeeded on one RoboDojo development case.** The native
evaluator and runner agree on success, score `1.0`, and termination at 919
actual control steps. This completes the first full motor-policy episode
milestone; it does not complete the multi-policy qualification or speed/quality
screen, establish general success rate, or demonstrate a supervision benefit.

| Measurement | Observed |
|---|---:|
| Case | `classify_objects__standard__g0__l0` |
| Native success / score | true / 1.0 |
| Native actions / limit | 919 / 1100 |
| Simulated time at 25 Hz | 36.76 s |
| Runner wall time | 536.02 s |
| Policy calls | 58 |
| GPT/API calls | 0 |
| Teacher corrections | 0 |
| Native stepping + observation time | 349.29 s |
| Policy observation ACK delivery | 90.02 s |
| Blocking policy proposals | 67.57 s |
| Native reset/setup within runner | 22.45 s |
| Gripper values explicitly clipped in proposals | 722 |
| Terminal unused actions discarded | 9 |

The 536 s runner measurement excludes initial simulator process startup and
policy process loading. Simulation pauses while inference runs. It is not a
real-time moving-world test. Timed components leave about 6.7 s of other runner
overhead; no unaccounted time is claimed to be inference.

## What Ran

- Pinned RoboDojo and GPT-as-Policy native simulator, joint controller, original
  task instruction and three RGB cameras. No depth, hidden object coordinates,
  evaluator feedback during execution, task-specific scripts or demonstrations
  were added to the policy input.
- Public RoboDojo-trained G0.5 FM checkpoint, unchanged model tensors in a
  model-only inference container, original normalizer and Qwen3.5 processor.
  Exact provisioning provenance is in `G05_BRINGUP_20261002.md`.
- Explicit variant: BF16 conversion, documented PyTorch linear attention,
  16-action prefix from horizon 32, ten denoising steps, source frequency setting
  30 with native donor execution at 25 Hz. This is not a source-controller or
  published-score reproduction claim.
- Explicit `gripper_clip=true` at the provider boundary; valid native actions
  still require openings in `[0,1]`. Counts cover predicted command scalars,
  including any unused terminal suffix, not necessarily executed clipped steps.
- Policy identity:
  `30369a9df2f8b20592fbb01a1bf20ffb632956c5c248bbda4042cfa2e0f01698`.
- GPU 0 ran the simulator; GPU 1 ran policy inference. Each actual native ACK
  produced one policy observation update. No queued or hypothetical ACK was used.

## Audit And Limits

The native task registered one nonempty completion condition before acting.
Source evaluator, terminal ACK and runner result all report native completion,
not vacuous capture-only success. The retained images show object sorting, not
just free-space arm movement. Small public result artifacts are in
[`evidence/g05-native-002/`](evidence/g05-native-002/).

The full 1.5 GiB native/controller trace and video are backed up locally under
`runs/native-evidence/g05-native-002/`: all 2,153 regular-file hashes match the
remote originals. The controller's 1,038-event hash-chain journal verifies, with
exactly 919 sequential control ACKs and 58 policy proposals. Both GPUs were idle
after the pilot, latency tests and owned policy process finished.

The case is in the development partition. Qualification is still marked
`native_unqualified`: one successful case does not qualify every policy, native
timing variant or held-out comparison. The source panel declares policy RNG seed
0, but the policy service did not explicitly seed Torch; that metadata is not
proof of its actual RNG state. Fix and bind RNG provenance before frozen pairs.

The initial replay probe found gripper values up to 1.001740. The full successful
pilot counted clipping but did not retain pre-clip ranges for every proposal, so
the maximum overshoot across its 722 clipped values is unknown. Future proposals
now record raw min/max and maximum clip magnitude as well as counts. Do not
describe all 722 as proven tiny overshoots.

An earlier launch (`g05-native-001`) exited before starting a controller because
the Isaac EULA environment flag was missing. It remains a startup failure, not
an additional task attempt or a policy failure. `g05-native-002` is the first
full native policy episode. The launcher also now preserves virtualenv Python
symlinks instead of accidentally invoking the system interpreter.

## Speed Evidence

The successful bound PyTorch provider completed a separate replay microbenchmark:
3 warmup calls, 30 timed calls on the same saved initial legal observation,
resetting policy memory per sample. Blocking end-to-end p50 / p90 / p99 were
**970 / 1412 / 1451 ms**, mean 1043 ms. Peak allocated/reserved memory was
11.00 / 11.75 GiB. These are proposal latencies, not native rollout throughput.
Some profiling overlapped separate-runtime preparation/JIT work on the other
GPU; do not interpret this as an isolated cross-policy latency ranking.

In a separate environment, updating FLA from 0.2.2 to 0.5.1 plus fla-core 0.5.1
resolved the `chunk_size` API error without changing source. A bounded raw replay
probe returned four 16-action chunks: cold inference 37.00 s (JIT included),
three warm calls 0.731 / 0.604 / 0.595 s. It used no clipping and therefore exited
2 after saving the out-of-range gripper diagnostics. This optimized variant has
not yet run a full native episode; it cannot inherit the PyTorch success result.

The main measured wall bottleneck in the successful pilot is native stepping and
observation transport (349 s), followed by policy ACK transport (90 s), not GPT
waiting (zero) or policy inference alone (68 s). Optimizing policy kernels helps
but cannot by itself eliminate the approximately 14.6x wall/simulation ratio.

## Parallel Preparation

InternW0-Delta's Apache-2.0 public checkpoint, selected Wan VAE/UMT5 assets, and
RynnBrain snapshot were downloaded while this pilot ran. All four major weight
files matched the pinned XPolicyLab artifact-lock SHA-256s. Revisions:

- Intern checkpoint: `4e705865a063ecc47a614c8810a3b2c65f16accb`.
- Wan assets: `921dbaf3f1674a56f47e83fb80a34bac8a8f203e`.
- RynnBrain: `36069aa841fc58f500d307316cbfdf379777ce8a`.

Its isolated Python 3.11.16 / Torch 2.10.0+cu128 / Transformers 5.13.0 environment
imports the source adapter. Model loading, inference, causal-conv dependency
readiness, memory fit and native competence remain untested. Downloads/imports
are not Phase A completion for Intern.

## Next Experiments

1. Bind explicit RNG provenance and raw clip-magnitude diagnostics; preserve
   the successful pilot as its own original variant, not a silently updated run.
2. Run Intern's bounded real inference and one complete native development
   episode. Stop genuine interface failures rather than compensate with GPT.
3. Run the prescribed 5–10 development cases for viable candidates, including
   a complete episode for any optimized G0.5 variant before selecting it.
4. Acquire the exact RoboDojo pi0.5 artifact through a legitimate source;
   do not substitute a generic checkpoint. Xiaomi controller parity and
   RoboCasa365 baseline qualification remain pending.
5. Then freeze and run matched motor-only/every-chunk/sparse comparisons plus
   direct dense/sparse. Sensing extensions remain downstream.

This sequence is also tracked in `EXPERIMENT_PROGRESS.md` and the owner's
`PHYSICAL_EXECUTION_LAB_V4_HANDOFF.md` appendix. Current CPU suite: 239 passed;
component tests are not counted as completed experiment stages.
