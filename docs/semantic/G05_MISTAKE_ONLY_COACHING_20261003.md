# G0.5 Mistake-Only Coaching

## Frozen Question

Can sparse observed-error feedback rescue baseline failures without disrupting
G0.5's own stage selection? Original-only baseline002 is 5/10 successes, mean
native score0.62. Subtask-only/recovery001 is 3/10, mean0.38, with four accepted
recovery goal changes but no recovered task success. Neither is official SR.

The next condition keeps the exact original task and appends a short temporary
`Correction:` note only after an observed original-task violation, lost grasp,
repeated failed placement or sustained stall. `recover` requires `failed`;
uncertain future mistakes and another valid stage do not qualify. Ordinary
`set_subtask` is forbidden. `clear_feedback` requires active feedback, observed
completion and an empty goal; it restores the original instruction byte-for-byte.
Stop remains incomplete abstention, not success. Evidence gates validate the
interface; whether the claimed error/completion is visible requires visual review.

The motor core, source G05 BF16/FM artifact, cameras, cases/layouts/horizons,
H32 prediction/H16 executed prefix, ACK history and shared B10 seed0 RNG remain
unchanged. Review target100 is checked at the next drained H16 boundary,
normally112. Same GPT-6.1 Sol/medium/Flex-preferred route and authorized capacity
fallback; $3 cohort/$95 shared cap, retaining unresolved holds. Simulation still
pauses for inference. No claim of fewer GPT checks or asynchronous execution.

Preemptive feedback is a separate future condition, not included here. No
task-specific examples, recipes, previous-run solutions, extra crops, boxes,
hidden state or evaluator scores are supplied to the actor.

## Checklist

- [x] Implement explicit correction prompt mode and observed-failure/clear gates.
- [x] Preserve legacy planner schema and default state behavior.
- [x] CPU verification:477 passed, including no-error action-stream parity and
  correction/clear cycles with unchanged ACK history. Not native phase completion.
- [x] Review baseline transfer: no file in cohort-admission CORE was edited;
  contracts/state/planner add opt-in language behavior only. Default original
  prompt remains exact and native motor wrapper/control/batching are unchanged.
- [ ] Deploy reviewed sources while GPUs idle; create a separate preparation
  and new source freeze before outcomes. Preserve all historical freezes.
- [ ] Run all ten distinct tasks concurrently in one bounded coaching condition.
- [ ] Audit actual model prompts, decision gates, prediction prefixes and ACKs.
- [ ] Hash-verify a complete local evidence backup and independently rerun audit.
- [ ] Review all task/feedback epochs; distinguish issued instructions, followed
  corrections, rescued successes and harm to baseline-successful tasks.
- [ ] Publish results and stopping decision; do not expand language sweeps if
  corrective execution remains unreliable.

Untouched-task Phase E, supported target/native-AR conditioning, motor
post-training, second backend and asynchronous native planning remain unfinished.
