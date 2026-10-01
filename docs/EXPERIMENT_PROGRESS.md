# Experiment Progress

Updated 2026-10-02. This tracks the v0.4 handoff sequence, not synthetic success.
Use Sol 6.1 Flex for the eventual supervisor comparisons. No paid calls yet.

| Stage | Status | Actual evidence / remaining gate |
|---|---|---|
| Pre-GPU | Complete | CPU suite, synthetic audit, source inspection and config preparation |
| A: native qualification | Partial | Reset/render/FK/joint ACK passed; G0.5 motor-only completed and succeeded once. Other providers, RNG binding and timing variants remain |
| B: speed/quality screen | Partial | G0.5 bound 30-sample replay latency and one native case; optimized FLA raw probe. Need other candidates and 5–10 development cases per viable policy |
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

- [ ] Explicit policy RNG binding and raw clipping-range audit for future runs.
- [ ] Full native episode for optimized G0.5 before adopting that variant.
- [ ] Intern real inference, memory fit, native episode and temporal-ACK checks.
- [ ] Exact RoboDojo pi0.5 checkpoint access; currently unavailable.
- [ ] Xiaomi RoboDojo native EE versus donor DLS qualification.
- [ ] 5–10 development cases per viable candidate; retain all failures.
- [ ] Frozen matched hybrid and direct comparisons.
- [ ] Official XR1 RoboCasa365 baseline and matched supervision comparison.

See [the first pilot report](NATIVE_PILOT_20261002.md) for methods, limitations,
timing, exact identities and evidence pointers. Large native traces/video are
local under `runs/native-evidence/g05-native-002/`, not actor memory or Git weights.
