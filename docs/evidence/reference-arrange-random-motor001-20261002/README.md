# Remaining Arrange Reference Motor Baselines

Three selected random-variant reference cases ran concurrently, not repeated
capacity seeds. All failed at1050 actions/score0.0:
`arrange_largest_number__random__g0__l0`, `...__l1`, `...__l2`.
The full five-case group, including the two previously executed standard
reference cases, has zero successes and mean native partial score0.03.
That is3/100 on the reference display scale, not full RoboDojo performance.

3150 actual controls,70 H50/15 policy calls per case, zero API calls,
434.3894 s rollout excluding startup/reset/shutdown. Native reset was slow;
the timer is not total wall rental time. The installed native task variant,
layout SHA/path, manifest, horizon, original prompt, checkpoint, source
predictions, per-environment RNG, nonblank cameras, actual ACKs and nonempty
native completion checks passed the included motor audit. Both GPUs idle
after exit; no controller faults or unresolved actions.

`plan.json` is the pre-launch case/config/source binding. `report.json` and
`offline-audit.json` retain exact outcomes and audited execution.
`group-summary.json` checks checkpoint/config/manifest/source equality before
combining the two standard and three random waves and lists the three missing
semantic candidates. The two standard candidate failures are separate evidence
in `../reference-arrange-semantic001-20261002/`; no random candidate was run.

These cases retain original test partitions but the task family was already
opened. Reports stay `native_unqualified`; not untouched evaluation, complete
benchmark coverage or evidence of hierarchy benefit. Only small reports and
operators were copied locally, no weights. Raw unique inputs/sensors remain
remote pending verified backup; no shutdown/retirement clearance is implied.
