# Simulator Sharing And Policy Batch Capacity

## Decision

Prioritize a native shared-process simulator runner over more model batch-size
sweeps. Five independently launched simulator processes are not a practical
24 GiB configuration. Five environments in one RoboDojo/Isaac process passed
reset/render checks on one 4090, using 9,459 MiB (9.24 GiB) total GPU memory.
This is capacity evidence, not scored rollout qualification or a speedup result.

## Measured Evidence

All probes used the existing two-4090 host, without paid calls or robot control
actions. Model probes used retained legal observations, two warm repetitions
per batch, and reset sessions. They are rough capacity/throughput screens.

| Probe | Result | Limitation |
|---|---|---|
| One additional independent simulator | Added 5,821 MiB beside an existing worker | Marginal measurement in that configuration, not a universal per-env cost |
| Five environments in one simulator process | 9,459 MiB total; all 15 RGB streams nonblank | One task family, reset/render only; no action or scoring test |
| G0.5 fused inference | B1: 0.623 s; B8: 0.793 s; B32: 1.724 s | B32 peak reserved 8.51 GiB; identical input rows, not live episodes |
| pi0.5 model-level fused inference | B1: 0.0921 s; B8: 0.4237 s; B16: 0.7970 s; B32: 1.5633 s | Deployed websocket server still serial; batched RNG parity unverified |
| Intern shared runtime | 1/2/4 sessions: 0.941/1.853/3.657 s | Sequential prediction loop; essentially no throughput gain |

pi0.5 throughput largely saturates around B8-B16. At B32 its JAX active
allocation peak was about 10.20 GiB, but its allocator pool was about
16.07 GiB and NVML usage about 16.50 GiB. Pool reservation matters when sharing
a GPU with simulation. Intern reserved about 14.84 GiB on GPU0 and 13.39 GiB
on GPU1; growing episode histories were not tested.

The five-env simulator completed setup/reset/render checks in 66.36 seconds.
That number is not simulation steps/second. Its seeds were [0,1,2,0,1]; this is
not five independent benchmark cases or verified isolated-reset parity.
Camera nonblank checks do not establish visibility, seed parity or absence of
cross-environment scene contamination. The first probe stopped on an import
shadowing error; correcting operator sys.path order let the second probe pass,
without changing upstream or production code.

Small reports and reproduction operators:
[batch-capacity evidence](evidence/batch-capacity-20261002/).
The reports distinguish model allocation, allocator reservation and device
usage; do not combine these into a claim that a full live configuration fits.

## Next Implementation

1. Use RoboDojo's existing get_obs_batch/take_action_batch and per-env native
   counters/scoring. Replace the donor server/session's env0-only assumptions
   in an experimental wrapper, not the frozen comparison runtime.
2. Start with one task family and five cases per wave. Share simulator assets,
   renderer/runtime and model weights, but isolate case IDs, seeds, observations,
   policy histories/RNG and output journals. Run other task families in later
   waves; arbitrary mixed-family support remains unverified.
3. Account for every physics advance and actual action ACK for every live env.
   Do not silently advance paused episodes, reset completed ones or replace
   failed cases mid-wave. Define completed-env handling explicitly.
4. Qualify batch1 versus batchN observation isolation, native H50/15 cadence,
   per-env termination/scoring and reproducibility before using results in
   matched comparisons. Do not assume batching preserves stochastic samples.
5. Put shared simulation on one GPU and G0.5/pi0.5 inference on the other for
   the first integrated test. Intern needs both GPUs, so its simulator
   coexistence requires a separate measured configuration, not an assumed fit.
6. Measure completed episodes/hour and simulator/action latency in a small
   motor-only wave. Then expand the fixed evaluation roster. Sparse paid GPT
   planning stays serialized through the campaign lock; a synchronous planner
   pause may stall the entire wave until asynchronous handling is qualified.

No additional GPU rental is justified by these capacity results yet. A useful
first target is five live cases per wave, not finding the maximum possible
batch size. Existing serial development results remain in their original
cohorts; new vectorized results need an explicit execution-condition label.

## Native Bounded Rollout Update

An experimental runner now drives native take_action_batch with shared fused
pi0.5 inference on GPU1 and shared simulation on GPU0. The production semantic
runner and frozen source fingerprint remain unchanged.

| Wave | Actual Controls | Fused Predictions | Rollout Wall | Simulator MiB | Policy MiB |
|---|---:|---:|---:|---:|---:|
| B1, layout0 | 150 | 10 | 43.4562 s | 6,703 | 8,668 |
| B5, layouts [0,1,2,0,1] | 750 (150/env) | 10 | 88.1929 s | 9,907 | 8,660 |

Both source-action/routing/native-counter/post-action-state/H50-15 audits pass.
All legal input cameras are nonblank, native task completion checks are
registered, and neither wave flagged an unstable environment. No paid calls,
GPT conditioning, recovery or controller-generated task skills were used.
Both waves stopped at the explicit 150-action budget, with no native terminal
outcome. They are not successes, failures at the native horizon or five new
independent cases. Repeated layouts are deliberate capacity rows.

Aggregate action throughput is 8.50/s at B5 versus 3.45/s at B1, about 2.46x.
This is one short wave at each size, including first inference compilation,
request/result file exchange and retained evidence IO, but excluding model and
simulator setup before the rollout timer. It is not a confidence interval,
completed-episodes/hour measurement or comparison with the production runner.
Five environments add 3,204 MiB over B1 in this implementation, far below the
cost of four independent simulator processes.

Attempt001 stopped before executing any action because the experimental worker
rejected out-of-range raw gripper values. The source Pi05Client explicitly
clips continuous openings to [0,1], as native execution does. Attempt002
implements that same conversion, retaining raw and converted arrays. This
was an operator omission, not a model/backend failure; no failed physical
episode was silently replaced.

Evidence and operators: [vector rollout](evidence/vector-rollout-20261002/).
Full sensor/proposal/ACK payloads remain under remote runs/vector-pi05-* and
local runs/native-evidence/vector-rollout-20261002 after completed download.

### Remaining Gates

- Per-env policy RNG streams and a batch1/batchN preprocessing/sampling check;
  current fused sampling uses one seed0 stream per wave, not isolated parity.
- Validate sensor/physics isolation and task/layout asset binding beyond
  nonblank camera and correct row-routing checks.
- Test native termination, frozen terminal-score snapshots and the subsequent
  exclusion of completed rows. Global physics continues for completed envs;
  that is disclosed, not represented as a paused scene.
- Bind a fixed broader development roster before full-horizon waves, preserving
  untouched held-out cases. Integrate semantic conditions without contaminating
  the original frozen cohort, then resume matched/subtask-only/recovery phases.

These gates are the next runner work, not reasons to revisit maximum batch
sizes or install additional models. The two GPUs have enough measured headroom
for the tested five-env pi0.5 configuration.
