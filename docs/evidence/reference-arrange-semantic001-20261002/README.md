# Reference-Bound Arrange Semantic Pair

Two fixed selected GPT-as-Policy reference cases, historically opened task
family, original test partition preserved. Not an untouched held-out result
or a full RoboDojo denominator. Baseline evidence:
`../reference-arrange-motor001-20261002/`.

| Case | Motor Score | Task+Subtask/Recovery Score | Success Either Condition |
|---|---:|---:|---|
| arrange_largest_number__standard__g0__l0 | 0.00 | 0.15 | No |
| arrange_largest_number__standard__g0__l1 | 0.15 | 0.15 | No |

Both candidate cases reached the native1050-action horizon.2100 controls,
70 policy calls/case, twenty valid planner calls, six applied recoveries
(2/4). Sol6.1 medium/Flex cost$0.12829000. Candidate rollout514.3175 s;
motor316.4768 s, excluding startup/shutdown. Partial-score increase on one
case is descriptive; no success-rate or causal advantage established.

`plan.json` binds source/config/baseline and discloses baseline-first chronology.
`paired-summary.json` retains every selected outcome, exact reference/layout/
checkpoint identity equality and claim limits. `offline-audit.json` checks
actual source predictions, motor request prompts, action ACKs, per-environment
RNG, cadence, response bindings and recovery counts. `planner-decisions.json`
contains structured decisions and metered usage, not encrypted reasoning or
credentials. Native evaluator scores never entered actor control.

`tokenizer-replay.json` replays every actual retained request through the same
installed policy input sequence on CPU: default-prompt injection, data
transforms, checkpoint normalization, model transforms/tokenization. Every
entire cleaned prompt was present in decoded active tokens. No model weights
were loaded or simulator actions taken. This checks truncation for these inputs,
not instruction obedience or general future prompts; it is offline replay,
not live token capture. The executed operator is included.

Current native qualification remains incomplete (`native_unqualified`). This
result does not admit untouched tasks automatically. Keep seven unopened task
groups sealed until frozen executor admission. Broader reference coverage and
second-backend comparisons are still outstanding.

Only small reports/operators were copied locally. Unique raw sensors remain
remote pending verified backup; do not treat this directory as shutdown or
artifact-retirement authorization. No local model-weight download occurred.
