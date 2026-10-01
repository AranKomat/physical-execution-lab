# Exact Pi0.5 Native Pilot

## Result

The released exact RoboDojo seed-0 pi0.5 checkpoint completed
`classify_objects__standard__g0__l0` successfully: **native score 1.0,
994/1100 actual actions, 67 policy queries, zero GPT/API calls or corrections**.
Runner wall time was 546.40 seconds; simulated time was 39.76 seconds at 25 Hz.
This is one complete development episode, not a five-case screen, held-out
result, published-score replication, or evidence of a supervision benefit.

The policy received the three original RGB cameras, measured robot state and
native instruction. No hidden object geometry, score feedback, task recipe,
added demonstration or cross-episode memory was fed to the policy.
All executed commands were native joint14 actions; the available robot DLS
correction interface was not used.

## Binding And Runtime

Exact checkpoint provenance and publisher hashes are in
[the access report](PI05_ACCESS_AND_COMPARISON_GATES_20261002.md).

```text
native params/assets hash d15fb8bd1d29cb30b69f01b71c66596cb0293c1a8a94111b343c1580dd3e3e5b
harness artifact identity c70c9a59e650d484c8b921d8e17181cacd8e24b20c4cbae8277a1dffe9b69ee9
policy identity 78de83adc06eae60af453f72fd026f40de9c3eef3a214bf528770f51abd321c2
resolved motor config af24908a77cde16230bd25e26e46ef37d17742ec53ff806a0b8cdfb0d7b112f8
```

Runtime is isolated at `.venv-pi05`, installed from the vendored XPolicyLab
Pi_05 OpenPI lockfile using uv 0.8.22, frozen sync, the lerobot group and default
dependencies. Key versions: Python 3.11.16, JAX/JAXlib/CUDA plugin 0.5.3,
Flax 0.10.2, Orbax 0.11.13, NumPy 1.26.4, Torch 2.10.0, Transformers 4.53.2,
LeRobot 0.4.4. Installation used no persistent wheel cache to limit disk usage.
The first import omitted the default group and failed because upstream imports
pytest from model code. Restoring the original lockfile's default group fixed
that setup issue; no model/source or system-driver patch was made.

`prepare_pi05_bundle.py` binds actual artifact contents and checks the donor's
recorded native checkpoint identity. `run_pi05_native_pilot.py` owns the fresh
source server, bridge and native launcher, archives commands/logs, and cleans
up its own process groups. Source JAX seed 0 and original H50/15-action prefix
are retained. Policy ran on GPU 1; simulator ran on GPU 0. Observed policy-GPU
snapshots were approximately 8.6 GB, not continuously measured peaks. Both GPUs
were idle after all owned workers exited.

## Audit And Timing

Controller and native evaluator agree on success, score, step count and limit.
The local journal verifies all 1197 events and exactly contiguous ACKs 1..994.
Source inference indices are 0..66; all predictions have 50 actions. Accounting
is 3350 proposed = 994 executed + 2356 discarded, with zero unresolved actions.
Generic metrics show 67 shortened chunks/invalidation requests because the
source executes only 15 of each H50 prediction. These are normal source-prefix
discards, not 67 GPT interventions or temporal-memory resets: pi0.5 is stateless.
Small public results/audit: `docs/evidence/pi05-native-pilot/`.

Runner timing components: setup 22.87 s, environment 379.50 s, ACK transport
97.16 s, policy blocking 39.35 s, review 0 s. Cold source/bridge launch and prior
artifact hashing are outside runner elapsed time. The first source inference
took 15.65 s including first-call compilation. Remaining 66 rollout source
inferences had p50 265.00 ms and p90 284.94 ms. These are source-only timings
on changing rollout inputs, not the independent-observation end-to-end
30-sample speed test required for Stage B. Do not directly compare them with
G0.5's end-to-end replay percentiles.

G0.5 also succeeded on this nominal case, using 812 actions/51 calls/475.09 s.
Initial proprioception is identical. RGB is not byte-identical; per-camera mean
channel differences are 0.415/0.339/0.320 on a 0-255 scale. Same case/seed/layout
does not prove a complete hidden-state or exact sensor replay. One such case
cannot rank overall motor quality or demonstrate a harness improvement.

## Remaining Sequence

Update: the fixed five-case roster and matched warm timing are now complete;
see [the screen report](PI05_DEVELOPMENT_SCREEN_20261002.md). The sequence below
describes the next steps at the time of this first pilot.

Retain pi0.5 as viable. Run the same fixed five-case development roster used
for G0.5: sorting layouts 0, 1, 2 and tower layouts 0, 1. This successful pilot
supplies sorting layout 0; do not replace any later failure. Also complete the
matched recorded-input warm speed measurement. Then qualify/freeze shared
bindings and compare motor-only/every-chunk/sparse, plus policy-free dense/sparse.
Paid supervision still has unresolved Flex failures; no retry or tier fallback
occurred in this turn.

Future bridge starts now get unique proposal recording subdirectories, fixing
filename collisions when using the same bound root across fresh episodes. The
running pilot was not patched: it used the original flat recording directory.
The regression test verifies that two fresh bridges preserve both recordings.
The launcher timeout was also extended to cover simulator startup plus the
unchanged native episode wall budget; algorithm/action budgets were not raised.

Full recordings/configs are backed up in
`runs/native-evidence/pi05-native-001-backup.tar.gz`; remote archive SHA-256:
`ee6b05851507b49a66d7e13b515aa071ac7249de13b296c7a78a28fa4830f4f5`.
Weights remain remote. Raw results retain `native_unqualified`; complete native
development behavior is not a retrospective held-out qualification.
