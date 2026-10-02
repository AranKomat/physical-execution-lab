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
