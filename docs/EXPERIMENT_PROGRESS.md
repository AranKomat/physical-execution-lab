# Experiment Progress

Updated 2026-10-02. This tracks the v0.4 handoff sequence, not synthetic success.
Use Sol 6.1 Flex for the eventual supervisor comparisons. No paid calls yet.
Owner scope update: RoboDojo candidates are **G0.5 and exact pi0.5 only**.
Xiaomi R1 and Intern are removed from the active RoboDojo screen; their prior
code/evidence remain archived. Xiaomi's separate RoboCasa365 track is unchanged.

| Stage | Status | Actual evidence / remaining gate |
|---|---|---|
| Pre-GPU | Complete | CPU suite, synthetic audit, source inspection and config preparation |
| A: native qualification | Partial | Reset/render/FK/joint ACK passed; PyTorch and seeded FLA G0.5 succeeded on the same sorting layout. Other interfaces remain unqualified |
| B: speed/quality screen | Partial | G0.5 replay latency and two same-layout runtime pilots; Intern stock BF16 loading exceeds 24 GB. Need 5–10 development cases per viable policy and isolated timing |
| C: matched harness comparison | Not started | No paid review runs, direct comparison or held-out freeze |
| D: RoboCasa365 | Not started | Official XR1 checkpoint/environment/native baseline still needed |
| E: sensing/transfer | Deferred as specified | Only after useful matched physical results; no RGB-D port claimed |

## Completed Milestones

- [x] Legal observation capture and bounded actual native joint step.
- [x] G0.5 artifacts/processor provisioned; unchanged inference export prepared.
- [x] Explicit BF16/PyTorch/clip provider bound to artifacts and settings.
- [x] One complete native development episode: success, score 1.0, 919 actions,
  58 policy calls, zero supervisor/API calls.
- [x] 30-sample bound replay microbenchmark, with warmup separated.
- [x] G0.5 FLA compatibility resolved in a separate runtime by dependency update.
- [x] Intern checkpoint/base assets acquired and major publisher hashes matched.

## Remaining Milestones

- [x] Explicit policy RNG binding and raw clipping-range diagnostics for future runs.
- [x] Optimized seeded G0.5 full native episode: success, score 1.0, 812 actions,
  51 policy calls, zero paid calls/corrections; provisional development runtime.
- [ ] Exact RoboDojo pi0.5 checkpoint access; currently unavailable.
- [ ] 5–10 development cases per viable candidate; retain all failures.
- [ ] Frozen matched hybrid and direct comparisons.
- [ ] Official XR1 RoboCasa365 baseline and matched supervision comparison.

Removed from active scope: Intern inference/native qualification (stock BF16
loader exceeded 24 GB), and Xiaomi RoboDojo native EE versus donor DLS checks.
No further provisioning or experiments for these RoboDojo candidates are planned.

See [the first pilot report](NATIVE_PILOT_20261002.md) for methods, limitations,
timing, exact identities and evidence pointers. Large native traces/video are
local under `runs/native-evidence/g05-native-002/`, not actor memory or Git weights.

See [the seeded development update](DEVELOPMENT_UPDATE_20261002.md) for the Intern
memory failure and [parallel execution rules](PARALLEL_EXECUTION.md) for scheduling.
The next five-case motor development roster is fixed as sorting layout 0,
tower-building layout 0, sorting layout 1, tower-building layout 1, sorting
layout 2 (all source seed 0, all development partition). Retain failures; do not
replace cases after observing their outcomes. Expand to the remaining five
development entries if needed before freezing matched supervision comparisons.
