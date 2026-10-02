# Native Parallel Planner Pilot

Five native sorting environments shared pi0.5 weights on GPU1, with simulation
on GPU0. Each episode retained its own semantic runner, planner history,
instruction context and journal. This was an explicitly bounded integration
cohort, not a full-task hierarchy comparison.

## Results

- 750 actual controls: 150 per environment, ten H50/15 motor predictions each.
- Ten settled Sol 6.1 medium/Flex calls: two per environment, **$0.04298250**.
- 185.73 s rollout; device snapshots 9,907/8,666 MiB; no unstable rows.
- All episodes `resource_limited` at the explicit action bound, not native
  success, native horizon failure or semantic abstention.
- One initial semantic change per episode, then CONTINUE. Within-episode
  replacement goals and native planner abstention remain untested here.
- Existing semantic audits, source H50 equality, actual ACKs, request prompt
  routing, episode/stamp/step binding and served model/tier checks passed.
- No motor resampling, policy reset, prefix shortening, recovery or unresolved
  actions. Actor state used the RGB/proprio/FK whitelist; no evaluator truth.

Planner calls used the existing serialized shared budget relay and a host-wide
planner lock. Review timers include lock wait (27.77--85.28 s per episode) and
overlap, so their sum is not elapsed planner wall. Family barriers pause while
reviews complete. No serial speedup or planner throughput claim is made.

## Transport And Retention

The SSH launcher returned a timeout after all calls settled. A new read-only
connection found the terminal report, and the offline native audit passed.
Both GPUs were subsequently idle. The episode was not restarted or retried.
The ten structured tool decisions/usage records are public; raw provider
responses and requests remain local and are not published. Unique native
sensor payloads remain on the host and need backup before retirement.

## Next Comparison

The prepared multi-family semantic supervisor accepts three sorting rows and
two tower rows, matching the five unique development layouts without capacity
duplicates. Its new 2/3-row modes and cross-family semantic execution have not
yet run. Freeze a separate vector cohort before full original-only,
task-plus-subtask and subtask-only waves; do not pool historical serial pairs.
Retain every abstention, API error and missing case, and complete full outcomes
before claiming hierarchy benefit. Recovery and held-out/backend phases remain
pending. More capacity-only sweeps are not the priority.
