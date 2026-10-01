# XR1 Development Screen

## Fixed Roster

Before the harness results, preparation fixed six episode-0 cases from existing
development task groups: two per official target50 category. Trial count remains
50 for the global index calculation; this is not six tasks renumbered from zero.
The pretrain kitchen split, seed base 7 and native horizons remain unchanged.

| Task | Official Category | Episode Seed | Native Horizon |
|---|---|---:|---:|
| OpenDrawer | atomic_seen | 307 | 750 |
| TurnOnElectricKettle | atomic_seen | 757 | 450 |
| RinseSinkBasin | composite_seen | 1257 | 1350 |
| StoreLeftoversInBowl | composite_seen | 1607 | 2550 |
| CategorizeCondiments | composite_unseen | 1857 | 1650 |
| PanTransfer | composite_unseen | 2157 | 1800 |

No failure will be replaced with a different task or seed. All episodes are
development; this roster is too small to reproduce the benchmark score.
CloseBlenderLid was previously opened for bring-up despite its initial test
partition. The new full manifest explicitly quarantines its entire task family
as development, without rewriting the original manifest or pretending it was
never exposed. Unopened test tasks are not moved into this roster.

## Binding

Preparation: `scripts/multibench/prepare_robocasa_development.py`, remote/local
output `configs/local/xr1-development-001/`. Shared motor/every-chunk/sparse
conditions use one unchanged provider, sensor processing and controller.

```text
development manifest d78d9a8cd01f389fb2d3845322ca82a5ce00d5208717da7743b0b1884da07911
artifact content identity 074ffdf26db2b7d510ab0b6a14b27b1e7809d2e3c29b559ef906f3eb4f27f353
provider config cb088b1e7f9c2d91a886341f2e4a7eae885f523d2c47507096e23b0da99d19c5
policy identity 71592c5cdddba0983c8d055753e1e021af5e983d16d53a597d4e2cd09281b48b
```

Each episode starts a fresh official XR1 server on GPU 1 with explicit
`MIBOT_SERVER_SEED=7`, BF16/Flash Attention2 and the official checkpoint.
The simulator runs on GPU 0. No paid calls, demonstrations, task solutions,
hidden geometry or score feedback are used to select actions.
The model receives history 4 / interval 2, crop 0.95, and executes a 16-action
prefix through the official converter. Actual observations update history after
every executed step. A discarded suffix is never acknowledged as executed.

## Results

| Task | Success | Native Steps | Policy Calls | Runner Wall Seconds |
|---|---|---:|---:|---:|
| OpenDrawer | No | 750 | 47 | 65.00 |
| TurnOnElectricKettle | Yes | 98 | 7 | 20.92 |
| RinseSinkBasin | No | 1350 | 85 | 106.96 |
| StoreLeftoversInBowl | No | 2550 | 160 | 212.47 |
| CategorizeCondiments | Yes | 1297 | 82 | 115.20 |
| PanTransfer | No | 1800 | 113 | 129.09 |

**2/6 successes**, 7845 actual native actions, 494 policy calls, zero GPT calls.
All four failures reached their original native horizon; no infrastructure or
contract error occurred. Category rates were 1/2 atomic seen, 0/2 composite seen,
and 1/2 composite unseen. Six selected development tasks cannot establish the
published target50 rate or a comparison against G0.5 on a different benchmark.
The 95% Wilson interval for this small roster is approximately 9.7%-70.0%.

Runner wall time includes reset/setup but excludes cold server startup and
preceding artifact hashing. RinseSinkBasin overlapped the bounded source-parity
replay on GPU 0; its timings are shared-host measurements, not isolated peaks.
Servers are fresh per episode, unlike the official scheduler's persistent
multi-episode RNG streams. This is a reproducible development protocol, not an
exact reproduction of the official 2500-episode scheduling/RNG regime.

## Bridge Evidence

Native 20 Hz, legal observation validation, per-step history acknowledgement and
source action conversion passed the full episodes' runtime gates. Offline
journal verification confirms contiguous, exactly-once ACK counters across all
7845 actions. This is software/provenance evidence, not a robot safety proof.

A fresh seed-7 official server replayed OpenDrawer's retained initial public
RGB/proprioception through the official client. Its 16 actions **exactly matched**
the harness's initial proposal (maximum absolute error 0). This checks initial
processing/action parity only, not every later historical input or control path.
See `docs/evidence/xr1-bringup/initial-parity.json`.

The full screen archive is backed up locally under `runs/native-evidence/` and
matches the remote hash:
`42300241bc2fd2d75a7d7a8d1282b37024192ca6fa0c8318897c9cc6f91e5739`.
The generated full-denominator report is in
`docs/evidence/xr1-development-screen/`.

## Sparse Supervision: Incomplete Infrastructure Result

Fresh `xr1-supervision-kettle-001` used the same case, policy identity, controller
and initial legal sensor arrays as the successful motor-only kettle case. The
different observation stamp reflects the new episode identity; all initial RGB
and state arrays compare exactly equal, not merely the same nominal seed.
That equality does not prove equality of all hidden physics state.

The first actual Sol 6.1 Flex review completed and chose **shorten to 8 steps**:
the model claimed the proposal aligned with approaching the kettle but wanted
to inspect lever alignment. These are model claims, not independently certified
object-state facts. The harness executed 50 native steps, made five policy
queries and one completed review, then stopped when the second API request
returned explicit Flex capacity failure with no usage. No retry or Standard
fallback occurred. No every-chunk trial was started afterward.

This is not a successful paired comparison or evidence that supervision hurts
physical task competence. The censored result stays visible. Confirmed cost was
$0.003701; the failed request retains its full $0.0656400 reservation. The shared
ledger now has 4537 reservations, 154 unsettled, $75.934460744300 spent plus
holds, and $9.065539255700 remaining under $85. All earlier holds remain charged.

The immutable original result reports token values for the one successful
response, not the entire two-request attempt. Full input/output/reasoning totals
remain unknown; known subtotals are 2314 / 168 / 26. Its review timer omits the
failed request's wait. These reporting issues are fixed for future runs:
unknown full usage stays null, known subtotals are separate, and failed-review
wait is counted. Pending proposal accounting is also explicit: the historical
attempt proposed 80 actions, acknowledged 50, discarded 14, and left 16 pending
at the API error. A lost physical ACK must never be assumed to be a discard.
The raw historical files were not rewritten to look as if they used the fix.

Supervision backup hash, verified locally and remotely:
`6c14aa2943acc1dff8ebb5f00c7ea23cb2aa915969af2a87770753ceb7da33c2`.
API audits remain private; no account credentials were transferred to the GPU
host or published. The temporary relay/tunnel and all model/simulator processes
from this screen are stopped.

## Next

The baseline development screen and initial bridge check are complete. Stage D
as a whole remains open: qualify/freeze the native bindings and complete matched
supervision under a consistently available, explicitly selected serving tier.
Do not run more baseline cases or tiny controller diagnostics just to avoid the
current Flex-capacity blocker. Exact RoboDojo pi0.5 still needs its released
checkpoint; do not substitute a generic model or reopen Intern.
