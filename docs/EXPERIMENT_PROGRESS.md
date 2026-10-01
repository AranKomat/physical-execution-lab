# Experiment Progress

Updated 2026-10-02. This tracks the v0.4 handoff sequence, not synthetic success.
Use Sol 6.1 Flex for supervisor comparisons. One paid route check succeeded;
two G0.5 attempts stopped before motion. XR1's first sparse attempt completed
one review and 50 steps, then stopped on Flex capacity at request two.
Owner scope update: RoboDojo candidates are **G0.5 and exact pi0.5 only**.
Xiaomi R1 and Intern are removed from the active RoboDojo screen; their prior
code/evidence remain archived. Xiaomi's separate RoboCasa365 track is unchanged.

| Stage | Status | Actual evidence / remaining gate |
|---|---|---|
| Pre-GPU | Complete | CPU suite, synthetic audit, source inspection and config preparation |
| A: native qualification | Partial | Reset/render/FK/joint ACK passed; PyTorch and seeded FLA G0.5 succeeded on the same sorting layout. Other interfaces remain unqualified |
| B: speed/quality screen | G0.5 screen complete; exact pi0.5 provisioned | Fixed five-case G0.5 screen: 3 successes, 2 native-limit failures; 30-sample seeded FLA timing. Exact seed-0 pi0.5 files verified; runtime/inference/native screen pending |
| C: matched harness comparison | Started, incomplete | Flex route verified; two zero-motion native attempts failed on routing/capacity. No matched physical result or held-out freeze |
| D: RoboCasa365 | Motor-only bridge qualified; comparison pending | Fixed six-case harness screen: 2/6 success, no infrastructure errors. Initial official-client chunk matches exactly. Evidence-reviewed motor-only qualification recorded; supervision/corrections remain unqualified. Sparse kettle pilot reached 50 steps then Flex capacity failed |
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
- [x] Exact RoboDojo pi0.5 checkpoint access: 18 inference files verified against
  publisher hashes and donor previous-load identity; runtime/inference still pending.
- [x] Minimum five-case G0.5 development screen: 3/5 success, native scores
  1.0 / 1.0 / 0.4 / 1.0 / 0.0; all failures retained, zero paid calls.
- [ ] Frozen matched hybrid and direct comparisons.
- [x] Official XR1 RoboCasa365 full native development pilot: CloseBlenderLid,
  seed 7, success at 286 steps; smoke/reset/render/inference also completed.
- [x] Fixed balanced XR1 subset: 2/6 successful, 7845 native actions, 494 policy
  queries, zero GPT calls. All four native-limit failures retained.
- [x] Initial legal-observation official-client parity: all 16 actions match exactly.
- [ ] Matched XR1 supervision comparison: one sparse pilot executed 50 steps after
  a successful Flex review, then stopped on capacity failure at request two.

Removed from active scope: Intern inference/native qualification (stock BF16
loader exceeded 24 GB), and Xiaomi RoboDojo native EE versus donor DLS checks.
No further provisioning or experiments for these RoboDojo candidates are planned.

See [the first pilot report](NATIVE_PILOT_20261002.md) for methods, limitations,
timing, exact identities and evidence pointers. Large native traces/video are
local under `runs/native-evidence/g05-native-002/`, not actor memory or Git weights.

See [the seeded development update](DEVELOPMENT_UPDATE_20261002.md) for the Intern
memory failure and [parallel execution rules](PARALLEL_EXECUTION.md) for scheduling.
The completed five-case motor development roster was fixed as sorting layout 0,
tower-building layout 0, sorting layout 1, tower-building layout 1, sorting
layout 2 (all source seed 0, all development partition). Retain failures; do not
replace cases after observing their outcomes. It supplies sufficient development
evidence to retain G0.5; move next to matched supervision rather than more of the
same screen. See [the full screen report](G05_DEVELOPMENT_SCREEN_20261002.md).
Future formal bindings include hashes of the ancillary embodiment config files.

The shared EEF translation/hold development probe now passes: 80 sequential
native actions, two separate 20 mm upward targets and return, zero paid calls.
See [the controller report](EEF_CONTROLLER_CHECK_20261002.md). This is not contact
qualification or Stage C completion. The budget-enforced Responses route is
verified for the actual Sol 6.1 model and Flex tier. Native supervision has not
yet completed an episode; XR1's incomplete sparse trial executed 50 actions.
See [bring-up update](SUPERVISION_RC365_BRINGUP_20261002.md).
The $85 shared ceiling and all unresolved holds remain. Latest snapshot:
$75.934460744300 spent plus holds, 154 unsettled reservations; no automatic
retry or Standard fallback. See [XR1 screen and next gate](XR1_DEVELOPMENT_SCREEN_20261002.md).

Motor-only native bridge qualification is now evidence-reviewed and bound to
the exact resolved configuration, not applied to supervision by inference.
The motor-only source/config/manifest freeze is verified on the GPU host and
backed up locally; no held-out tasks were opened.
See [qualification review](XR1_NATIVE_QUALIFICATION_20261002.md). Raw historical
development results remain unchanged; Stage D and held-out comparisons are open.

Latest gates: [exact pi0.5 access and direct-call feasibility](PI05_ACCESS_AND_COMPARISON_GATES_20261002.md).
The current host lacks OpenPI/JAX, contrary to the older bring-up runtime note.
Source updates invalidate the prior XR1 code freeze until regenerated.
