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

## Sampling Check And Revised Execution Choice

On two retained legal five-env observation batches, per-row transforms after
the native JAX cast and per-env seed0 RNG advances matched the isolated path.
Nevertheless fused model outputs were not equivalent: maximum raw action
differences were 0.96344 and 0.00766 over the full H50 predictions. Within the
executed 15-action prefixes, maxima were 0.21286 and 0.00487. The largest full
prediction difference was a joint coordinate, not merely gripper clipping.
This screen does not identify the numerical cause; do not attribute it solely
to BF16 or assume it is harmless.

Default experimental pi0.5 execution now shares simulator runtime and model
weights but calls the source Policy.infer on one row at a time, restoring each
env's separate JAX RNG state. This avoids changing the native sampling shape.
The source gripper conversion remains explicit and raw predictions retained.
The old fused B1/B5 timing evidence still describes the old execution mode; it
is not relabeled as the new runner's throughput result.

A retained-input stream check exercised five rows, followed by reordered rows
[2,0,4]. Per-env call counts and source RNG-key advances passed. Its repaired
attempt also matched both native reference batches bitwise. An earlier fresh
worker differed by 0.00635 and failed the strict numerical assertion; retain
that evidence rather than treating the subsequent exact match as proof of
universal fresh-load reproducibility. The second check explicitly separates
RNG/accounting assertions from measured numerical agreement.

An initial input-comparison probe also stopped because it compared pre-cast
NumPy values against converted JAX tensors. Native inference performs that
same cast. The corrected comparison uses the native cast on both paths.
Both failed probes are retained. All sampling checks made zero paid calls and
executed zero controls.

Small evidence and scripts: [sampling checks](evidence/vector-sampling-20261002/).
A fresh native-singleton full-horizon simulator wave is now testing terminal
handling on the existing layouts [0,1,2,0,1], without opening held-out layouts.
Repeated layouts are not independent task coverage. Its results must be
recorded separately from the fused bounded waves and frozen hierarchy pairs.

## Full Native-Singleton Wave

The full wave subsequently completed all five episodes in **574.35 s** of
rollout time, executing **4,790 native controls** through 74 vector request
boundaries. It made no GPT/API calls and used one shared model runtime with
separate native single-row inference streams. Memory snapshots remained
9,907 MiB on the simulation GPU and 8,654 MiB on the policy GPU.

| Env | Layout | Actual Controls | Native Success | Native Score |
|---|---:|---:|---|---:|
| 0 | 0 | 1018 | yes | 1.0 |
| 1 | 1 | 813 | yes | 1.0 |
| 2 | 2 | 1100 | no, native horizon | 0.0 |
| 3 | 0 | 759 | yes | 1.0 |
| 4 | 1 | 1100 | no, native horizon | 0.4 |

Source proposal equality, row routing, actual contiguous native counter ACKs,
H50/15 prefix cadence, post-action state payloads, per-env singleton call
counts and terminal snapshots matching the final ACK all passed offline audit.
Completed rows received no more policy calls/actions and were not replaced or
reset. Their physics still advanced globally; native score snapshots were
frozen at first terminal. No environment was flagged unstable.

This is an integrated development rollout, not merely reset/render capacity.
It demonstrates working five-env completion/horizon handling with shared
simulation and weights. Aggregate throughput was 8.34 controls/s. It does
not establish a production speedup: there is no matched full-horizon serial
wave with identical evidence IO, and an archive/backup ran concurrently for
part of this wave. Setup is outside the rollout timer. It also does not
establish policy success rate across RoboDojo: only three previously opened
layouts were used, including repeats. Layout1's two different outcomes are
retained, not selected away.

Evidence and the revised native-singleton operators:
[full wave](evidence/vector-full-wave-20261002/). This is explicitly a separate
execution cohort with scored_benchmark_qualified=false. Layout-file hashes are
recorded, but complete isolated-reset/scene/sensor parity is still unproven.
The next step is a fixed broader development roster and semantic batch
integration, not more maximum-batch-size sweeps. Frozen single-env hierarchy
variants still need their own results and are not replaced by this wave.

## Single-GPU Co-Location Result

Five environments and one shared pi0.5 runtime subsequently ran together on
physical GPU1, executing 750 controls (150/env) in 92.20 s through ten vector
request boundaries. Device usage was **18,520 MiB (18.09 GiB)** with 5,562 MiB
free. Simulator and policy processes were independently observed on GPU1;
a separate paid single-env hierarchy trial ran concurrently on GPU0. This
demonstrates co-location during a bounded rollout, not a measured worst-case
peak or full-horizon co-location qualification.

Routing, source proposals, contiguous actual ACKs, H50/15 cadence, post-action
states, nonblank cameras and singleton call counts passed audit. No unstable
environment was flagged. Status is `bounded_wave_incomplete`: no native
terminal outcome was reached. Layouts remain [0,1,2,0,1], not five independent
tasks. Evidence: [co-location](evidence/vector-colocation-20261002/).

Simulator sharing is the first scaling lever: five shared environments use
roughly 9-10 GiB for simulation, whereas one additional independent simulator
previously added 5.68 GiB. Model weights and simulator runtime are shared;
episode observations, action counters, policy RNG/history and journals remain
separate. pi0.5 continues native single-row inference because fused action
parity has not passed.

The next practical target is two concurrent five-env waves, one per 4090,
starting with same-family layouts. G0.5 needs its own native vector execution
and co-location check before claiming that configuration works. Arbitrary
mixed-family scenes, semantic planning integration and isolated scene/reset
parity remain open. Prefer expanding a bound development roster over another
maximum-batch sweep; no new GPU rental is justified yet. Retain original
benchmark camera settings, physics and horizons while testing this scaling.

## G0.5 Co-Location And Native Cadence

The same simulator executor now also supports the pinned G0.5 FM provider.
A five-env bounded wave completed **800 actual controls in 114.38 s**, with
ten source prediction boundaries and 160 controls per env. Observed device
usage at the end was **22,412 MiB (21.89 GiB)**, leaving **1,670 MiB** free.
Both model and simulator were observed on physical GPU1, while the frozen
subtask-only tower0 trial ran on GPU0. No paid calls were made by this wave.

The worker shares weights but calls the source single-row adapter, restoring
separate Python/NumPy/Torch CPU/CUDA seed0 RNG streams per env. Source history
keys remain env-specific; the loaded checkpoint reports num_obs_steps=1.
There are no within-episode model resets. It preserves the source's returned
16-action chunks and executes all 16; the underlying prediction horizon is
32, but the native adapter exposes only 16. This is not pi0.5's H50/15 cadence
and is not a fused-inference speed measurement.

Source proposal equality, gripper conversion, row routing, contiguous actual
ACKs, 16-action prefix cadence, post-action states, camera nonblank checks and
per-env singleton call counts all passed. All five rows remained active at
the explicit budget; no native outcome or unstable environment was reported.
The shared layouts [0,1,2,0,1] are capacity rows, not broader task coverage.
Evidence and reproduction operators:
[G0.5 co-location](evidence/vector-g05-colocation-20261002/).

Both policy runtimes therefore fit with five environments on separate single
4090s during bounded runs. Two simultaneous five-env model waves have not yet
been tested. G0.5's smaller headroom argues against increasing environment
count before full-horizon measurement. Native-singleton RNG isolation is
implemented, but isolated-trajectory equivalence, arbitrary task-family mixing
and scored benchmark qualification remain unproven. This implementation does
not alter the frozen semantic production runtime or complete V5 Phase E.

## Choosing The Two-GPU Topology

Sharing environments inside one simulator is the memory optimization;
co-locating that process with inference is a placement choice, not additional
sharing or pooled VRAM. Each device still has an independent 24 GiB limit.

- **One model, larger task/layout wave:** default to simulator on one GPU and
  inference on the other. This removes the combined allocation constraint and
  avoids local renderer/inference contention. Optimal environment count and
  end-to-end throughput still need measurement.
- **Two independent model comparisons:** co-location permits one shared
  simulator/model pair per GPU. Five-env bounded checks now pass separately
  for pi0.5 and G0.5, but a concurrent five-plus-five comparison and any speed
  advantage over the split topology remain unmeasured.
- **InternW0-Delta:** its tested component placement already spans both GPUs
  (roughly 14.84/13.39 GiB reserved in the model screen). Simulator coexistence
  and growing policy history remain untested. Neither the single-GPU model
  pairing nor the dedicated inference-GPU plan applies unchanged. Measure
  simulator placement alongside this exact loader before selecting env count;
  isolated allocator reservations are not proof that the live workload fits.

Prioritize simulator sharing in either topology. Do not lower camera quality,
change action cadence or merge episode histories to make a capacity test pass.

## Concurrent Task Families With Shared Inference

Two independent native family simulators now share one source pi0.5 runtime:
sorting runs layouts [0,1,2,0,1], tower-building [0,1,0,1,0]. Each simulator
uses native five-env batching on GPU0; model weights load once on GPU1 and
native single-row inference retains separate RNG streams keyed by wave/env.
This is not arbitrary mixed-family scenes inside a single Isaac process.

Both waves completed their explicit 150-action/env bounds: **1,500 controls
total**, twenty vector request boundaries and 100 native singleton policy
calls. Sorting rollout wall was 88.75 s and tower 94.21 s. Concurrent wave
wall including simulator startup was 161.18 s; total including shared model
startup and shutdown was 196.09 s. These timers differ from previous rollout
timers; no matched serial speedup or completed-episodes/hour claim is made.
All rows were still active at the bound; no native success/horizon outcome.

Both source/routing/actual-counter/cadence/post-state/camera audits passed.
The shared service recorded ten calls per env per wave; RNG advances matched
source seed0 streams independently, and original family instructions stayed
unchanged and distinct across waves. No environment was flagged unstable.
Live placement showed two simulator processes on GPU0 and one policy process
on GPU1. A concurrent boundary recorded 18,922 MiB on GPU0 and 8,706 MiB on
GPU1, leaving 5,160/15,376 MiB free. These are observations, not worst-case
peak guarantees. Full trace copies were downloaded and both local action
audits passed. Remote source evidence remains.

Evidence and exact operators: [multi-family execution](evidence/multifamily-pi05-20261002/).
The initial supervisor dispatch used an older copy and failed its busy-GPU
preflight before creating a run or executing any action. The revised owned
supervisor waited for idle GPUs; it did not interrupt the active paid trial.
After terminal reports, completed audits and absence of the remote supervisor
were confirmed, its lingering local SSH transport was closed. No episode was
restarted or replaced due to the transport issue.

**Next (superseded by the full-wave result below):** full-horizon concurrent termination/membership handling, then
per-episode semantic state/planner integration with the campaign's serialized
budget relay. Bind the roster and explicit new execution cohort before
comparisons; do not open held-out families to debug the runner or count
repeated layouts as independent task coverage. Stop further serial paid
comparisons while this parallel path is being finished. This bounded test is
working native execution, not completion of the research phases.

## Full-Horizon Concurrent Execution

The follow-up completed both five-environment families to native termination,
with one shared pi0.5 runtime: **9,432 controls**, zero paid calls and no
unstable environments. Sorting executed [760,1100,1100,855,716] controls
(three successes, two horizon failures); tower executed [1050,1050,701,1050,1050]
(one success, four horizon failures). These are repeated development layouts,
not ten independent tasks or a benchmark success-rate estimate.

Sorting rollout took 566.85 s, tower 533.84 s. Concurrent wall including
simulator startup was 635.73 s; including model startup/shutdown, 670.83 s.
There is no matched serial speedup measurement. Reported device snapshots were
19,018 MiB on GPU0 and 8,674 MiB on GPU1, not measured worst-case peaks.

Audits verified source prediction equality, contiguous actual ACKs, H50/15
cadence, removal of terminal rows, final score snapshots, original prompts,
per-wave/per-row source RNG and call counts. Retired rows' physics continues
globally inside each family, while their terminal scores remain frozen.
Exact executed operators and audits are in
[full-wave evidence](evidence/multifamily-full-wave-20261002/).

Next qualify the existing semantic runner on this executor, first without
paid calls, then with per-episode planners and serialized budget accounting.
Do not resume serial paid comparisons or merge this new motor cohort with
the historical frozen hierarchy pairs. No extra GPUs are needed for this
tested topology. G0.5 and Intern semantic integration remain unqualified.

The existing semantic-loop motor-only adapter passed a subsequent five-row,
750-control native pilot in 102.00 s rollout, with exact source predictions,
controller/native ACK equality and original prompts. It ended at the explicit
150-action bound, not native termination. Zero paid calls. The CPU structural
test also covers isolated prompt changes and retiring an abstaining episode;
that portion remains synthetic. Per-episode paid planners are still untested
on the native parallel executor. Prototype sources and both audits are in
[semantic coordinator evidence](evidence/semantic-vector-coordinator-20261002/).
