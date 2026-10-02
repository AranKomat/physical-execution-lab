# Reference Executor Admission

## Scope

The50-case selected GPT-as-Policy roster has10 task groups and13 runtime
variants. Static preparation verified every selected layout SHA against the
manifest and found each native task class/config. It imported no simulator,
loaded no model, and read no published outcomes. Source/config hashes,
locally defined support methods and horizon expressions are retained in
`../evidence/reference-admission-preparation001-20261002/report.json`.
Inherited behavior is not established by that inventory. None of its rows is
native-admitted merely because the static check passed.

## Reviewed Execution Path

Native `EvalEnv.run_eval` registers reward/score checks before entering the
policy loop and queries an initial support-arm trajectory when interactive.
`register_native_evaluation` mirrors that preamble, rejects empty completion
checks, and keeps evaluator predicates out of actor inputs.

Native `take_action_batch` executes robot controls, steps the reward manager,
then queries support trajectories and stability when interactive. Native
`process_control_info` consumes non-target support-arm queue entries at physics
substeps. The reference callbacks invoke these native methods directly; they
do not substitute a support-arm controller. This is source evidence only:
the untouched support-arm workloads still require runtime admission.

Actor observations contain original instruction, three native RGB views,
joint/gripper command state and robot EEF poses. The evaluator score is supplied
only on native termination, not as a planner phase signal. No task object poses,
reward predicates, layout object coordinates or privileged collision state
are supplied to the planner/motor. Native unstable outcomes must remain visibly
invalid/censored, not be silently replaced or pooled into successful episodes.

The installed `Pi05Client.infer` maps the same three HWC camera arrays to CHW,
passes joint state and instruction, accepts a finite50x14 prediction and clips
only the continuous opening columns6/13. The reference worker uses the same
policy factory/input shape/clip and calls ordinary `policy.infer`, with no
model warmup inference. The installed `Policy.__init__` defaults to
`jax.random.key(0)`, matching each reference episode's independent RNG stream.
These source comparisons support motor-contract parity, not bitwise reset or
numerical trajectory parity. Actual prediction/ACK/RNG audits remain required.

## Required Next Work

1. Prepare an execution-source freeze using
   `scripts/semantic/freeze_executor.py`. The optional snapshot in
   `semantic_lab.protocol.freeze` binds explicitly selected operator/native
   source files and config trees, including directory membership. Verification
   rechecks manifest contents, the snapshot and qualification's
   `execution_sources_sha256`. Missing, changed, newly added or unsafe linked
   sources fail closed. This mechanism is implemented; its selected graph,
   native review, qualification and pre-action enforcement are not automatically
   complete. The prototype's old narrow pre-action binding is not full admission.
2. Review the unchanged source prediction/cadence/RNG/prompt/ACK evidence against
   that freeze. Establish all seven checks in `semantic_lab.protocol.verify`;
   document that parity means source motor contracts, not bitwise scene replay.
3. Reuse the actual input-transform tokenizer replay only for its tested prompt
   scope. New prompts need retained-token checking; never infer obedience from
   token retention. Preserve binding validation without response repair/retry.
4. Admit unseen native variants with exact reset layout/horizon, nonempty
   completion registration, original support-arm behavior and sensor contracts.
   Preserve the grouped test split and frozen hierarchy condition; do not tune
   on their scores. Retain all failed, unstable, rejected and missing cases.
5. Run matched motor/candidate coverage across the reference task groups, then
   expand the remaining selected cases and the separately qualified second
   backend. The article score differs only by a100x display scale; scale
   conversion requires no rerun, but missing matched baselines do.

No new capacity sweep is needed. Current native reports remain
`native_unqualified`; these notes do not retrospectively relabel them. The three
missing random arrange cases completed as real original-only motor baselines:
all horizon failures, score0.0. All five selected reference motor cases of that
already-opened family are now executed, not untouched evaluation or capacity
rows. No new semantic prompt tuning or paid requests were involved.

## Binding Scope

The new preparation command requires explicit `--execution-source` selections
and refuses to overwrite its output. It does not create qualification records,
download checkpoints, run physics or authorize motion. Source snapshots cover
selected project/native source and config bytes, not installed binary integrity.
The reviewed graph must include the executor callbacks/coordinator, source
policy/client/transform code, native environment/task/config/layout sources and
resolved provider/checkpoint metadata. Existing model-load identity checks still
need to verify checkpoint bytes. A caller selecting an incomplete graph does
not acquire qualification simply because its snapshot verifies.

Legacy freezes without the optional snapshot remain readable; they do not gain
new execution-source coverage. Future reference-executor qualification must
require the snapshot and its exact hash rather than reuse an old qualification.
Historical results/qualification artifacts remain unchanged.
