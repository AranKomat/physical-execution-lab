# V5 Native Qualification Progress

## Scope

This is development qualification for semantic language hierarchy, not a full
RoboDojo success-rate estimate. The retained tower0 case is used; no unopened
held-out task was inspected. Native execution uses commit `63cfbb9`, the exact
pi0.5 checkpoint, GPU0 for both simulator and policy, seed0, three RGB views,
H50 prediction and 15-action execution prefixes. The local relay fix does not
change the GPU runner, policy source or frozen development configuration.

## Wrapped Original-Only Baseline

The full episode completed unsuccessfully at the 1050-action horizon, native
score 0.10, 70 policy calls, zero semantic calls, 607.33 s wall time and 42 s
simulated time. All 70 natural prefixes execute 15 actions. The 2450 unused
prediction-suffix actions are routine H50-to-15 discards, not GPT interruptions.

The offline audit verifies 1050 contiguous actual ACKs, native nonvacuous
completion registration, controller/evaluator agreement, 70 original source
NPZ proposals matching the journal, exact original prompt, fresh contiguous
source inference indices, bound checkpoint and source seed0. No unresolved
actions, controller faults, numeric corrections or semantic interventions.

The earlier tower0 screen succeeded at 714 actions, but its reset observation
hash differs (`71e64ae...` versus this episode's `5a6fbb6...`). The native case,
policy identity and environment contract match. We cannot attribute the changed
outcome to a wrapper regression or assert reproducible physical parity from
these two episodes. Keep both results; do not replace the new failure.

## Actual Tokenizer and Conditioning Probe

An independent GPU1 process loads the same source policy and consumes the
retained current baseline reset RGB/proprio. No simulator actions or API calls
are issued. A manually supplied non-goal instruction, `Keep both hands still.`,
is a wiring probe, not a planner-generated zero-shot task solution.

| Prompt Mode | Active Tokens / Limit | Subtask Retained | RMS Action Difference From Original |
|---|---:|---|---:|
| Original only | 67 / 200 | Not applicable | 0 |
| Task plus subtask | 80 / 200 | Yes | 0.0110 |
| Subtask only | 61 / 200 | Yes | 0.1444 |

Noise and RNG are identical across these three inferences. RMS is a mixed
numeric action-space difference across joint and gripper channels, not metres,
task effectiveness or language-obedience accuracy. No prompt truncation occurs
for these exact inputs. Different output establishes sensitivity, not obeying
the instruction, and says nothing about longer instructions on other tasks.
This direct-source probe alone does not qualify the complete remote wrapper.

Evidence: `docs/evidence/semantic-pi05-prompt-probe-001/report.json`.

An additional fresh seed0/default-noise source re-inference on GPU1 of the
recorded first native proposal input is not bitwise identical to GPU0's
recorded output: maximum exposed-action difference 0.00383115. It issues no
motion or paid call. Its cause is not established; do not describe it as
proven kernel nondeterminism, exact wrapper parity, or a wrapper regression.
The native shadow test must disclose numerical/runtime differences rather
than assume deterministic replay from matching seeds.

## Deployment Fix

The existing paid relay rejects any function except the historical
`robot_decision`. V5 emits `semantic_goal`, so unmodified deployment would fail
before reserving a paid request. The relay now has explicit `--tool-name
semantic_goal`; the default remains `robot_decision`, and either mode rejects
the other tool. Shared/local budgets, Sol/medium/Flex, no fallback, no retries
and unresolved-reservation handling are unchanged. The full CPU suite passes
372 tests, including actual semantic Responses-schema bounds. These tests do
not complete native qualification.

## Remaining Gates

- Native shadow comparison with the same GPU runtime/source and prepared
  condition roster. GPT must not change prompts, prefixes, resets or cadence.
- Full model-boundary/context-switch/ACK qualification; current pi0.5 is
  stateless, and its evidence does not qualify stateful Intern/G0.5/XR1 history.
- Matched development hierarchy and separate recovery condition.
- Freeze choices before unopened held-out task groups.

No native V5 hierarchy gain, full no-interference qualification, asynchronous
planning or full-benchmark replication is established yet.
