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
| A: native qualification | Complete for active motor-only RoboDojo scope | Reset/render/FK/conventions/ACK and complete episodes verified; exact G0.5/pi0.5 motor-only qualification and full-manifest freezes verify. GPT correction/contact integration remains a separate Stage C gate |
| B: speed/quality screen | Complete for active RoboDojo policies | Same fixed five-case roster: G0.5 3/5, exact pi0.5 4/5; all native-limit failures retained. Same-input 30-sample warm timing: G0.5 p50 801 ms, pi0.5 p50 454 ms. Development evidence only; qualification/freeze and matched supervision remain separate |
| C: matched harness comparison | First full sparse development result; overall incomplete | Pi0.5 tower0 sparse fails at full 1050-action limit, score 0.0, 27 settled Flex reviews/$0.258; nominal motor-only succeeded at 714 actions. Every-chunk stops at 626 actions on an invalid-quaternion correction; 69 settled API calls/$0.656, native score null. Held-out matched conditions and direct comparisons remain open |
| D: RoboCasa365 | Motor-only qualified/freeze refreshed; comparison pending | Fixed six-case screen: 2/6 success, no infrastructure errors. Initial official-client chunk matches exactly. Current-source motor freeze verifies; supervision/corrections remain unqualified. Sparse kettle pilot reached 50 steps then Flex capacity failed |
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
  publisher hashes and donor previous-load identity; native milestone is recorded below.
- [x] Exact pi0.5 isolated OpenPI/JAX runtime, real inference and complete native
  development episode: score 1.0, 994 actions, 67 policy calls, zero GPT calls.
- [x] Minimum five-case G0.5 development screen: 3/5 success, native scores
  1.0 / 1.0 / 0.4 / 1.0 / 0.0; all failures retained, zero paid calls.
- [x] Same fixed five-case exact pi0.5 screen: 4/5 success, 4,292 actions,
  289 policy calls, zero GPT/corrections; sorting layout 2 fails at full limit.
- [x] Pi0.5 matched saved-input warm timing: 30 samples after three warmups,
  p50/p90/p99 454/488/523 ms, same input corpus as G0.5, no simulator running.
- [ ] Frozen matched hybrid and direct comparisons.
- [x] First complete supervised development episode: pi0.5 sparse tower0,
  full native-limit failure, score 0.0; 21 shorten decisions and five one-action
  corrections. Retained as negative evidence, not successful recovery.
- [x] Official XR1 RoboCasa365 full native development pilot: CloseBlenderLid,
  seed 7, success at 286 steps; smoke/reset/render/inference also completed.
- [x] Fixed balanced XR1 subset: 2/6 successful, 7845 native actions, 494 policy
  queries, zero GPT calls. All four native-limit failures retained.
- [x] Initial legal-observation official-client parity: all 16 actions match exactly.
- [ ] Matched XR1 supervision comparison: one sparse pilot executed 50 steps after
  a successful Flex review, then stopped on capacity failure at request two.

Removed from active scope: Intern inference/native qualification (stock BF16
loader exceeded 24 GB), and Xiaomi RoboDojo native EE versus donor DLS checks.
Owner subsequently reopened Intern feasibility. Its two-GPU probe now loads and
completes four action inferences, warm median 820 ms/10 exposed actions;
native qualification remains pending. Xiaomi RoboDojo remains deferred. See
[two-GPU Intern probe](INTERN_TWO_GPU_PROBE_20261002.md).

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
verified for the actual Sol 6.1 model and Flex tier. Pi0.5 sparse supervision has
now completed a full native episode with failure; XR1's incomplete sparse trial
executed 50 actions.
See [bring-up update](SUPERVISION_RC365_BRINGUP_20261002.md).
The $85 shared ceiling and all unresolved holds remain. Historical pre-pi0.5 snapshot:
$75.934460744300 spent plus holds, 154 unsettled reservations; no automatic
retry or Standard fallback. See [XR1 screen and next gate](XR1_DEVELOPMENT_SCREEN_20261002.md).

Motor-only native bridge qualification is now evidence-reviewed and bound to
the exact resolved configuration, not applied to supervision by inference.
The motor-only source/config/manifest freeze is verified on the GPU host and
backed up locally; no held-out tasks were opened.
See [qualification review](XR1_NATIVE_QUALIFICATION_20261002.md). Raw historical
development results remain unchanged; Stage D and held-out comparisons are open.

Latest gates: [exact pi0.5 access and direct-call feasibility](PI05_ACCESS_AND_COMPARISON_GATES_20261002.md).
OpenPI/JAX has now been installed and tested in an isolated environment; see
[the complete pi0.5 pilot](PI05_NATIVE_PILOT_20261002.md).
The prior XR1 code freeze was invalidated by source updates and is now refreshed.

Latest: [complete pi0.5 screen](PI05_DEVELOPMENT_SCREEN_20261002.md).
Stage B is now complete for the active RoboDojo scope. Four new pi0.5 cases
ran on two isolated colocated workers; observed usage was about 15-16 GB per
GPU. This is not evidence that Intern fits across both GPUs. Exact motor-only
qualifications/freezes now verify; complete matched supervision/direct comparisons
remain unfinished. Preserve the paid holds and Flex-only route while resolving
the paid-lane gate; do not substitute more baseline screens for Stage C.

See [current qualification and freeze update](NATIVE_FREEZE_UPDATE_20261002.md).
The new [complete sparse result](PI05_SPARSE_SUPERVISION_20261002.md) establishes
physical execution of supervision, not its benefit. All 27 paid requests settled;
the earlier holds remain charged. Latest shared remaining budget: $8.807538505700.

Latest: [self-contained research handoff](RESEARCH_PROGRESS_HANDOFF_20261002.md).
Every-chunk tower0 stopped at 626 actions with `infrastructure_or_contract_error`:
`EEF quaternions are unit wxyz`. All 69 API calls settled ($0.65624150);
68 reviews were valid. This is neither full-horizon failure nor a completed
matched comparison. Preserve the rejected response and investigate correction
validation before another named trial; no automatic retry. Shared ledger now
has 4633 reservations/$76.848702994300 spent plus holds, $8.151297005700 remaining.
