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

## Host Binding Preparation Completed

At repository revision `ea8d067`, the source-only preparation command created
`runs/reference-execution-freeze002.json` on the existing two-GPU host. The
retained copy is `../evidence/reference-execution-binding001-20261002/freeze.json`.
It binds3003 files, including executor callbacks/coordinator/shared worker,
native environment/task/config/utils, installed OpenPI source, donor policy
client/server/session code, provider/artifact metadata and layout config bytes.
The execution snapshot SHA256 is
`00177ed46e1a6c75ffaae39fab4a53f49cf1540bf8301ac7b05eb2313c9eeb9d`.
Recomputing the snapshot immediately matched; separately checking every selected
layout against the sealed manifest verified all50 hashes. No simulator/model
was loaded, paid request made, or native qualification issued.

The first preparation omitted actual layout bytes and remains separately on
the host as `reference-execution-freeze001.json`. Attempting the expanded
binding via `external/RoboDojo/Assets` was rejected before output creation:
that directory is a symlink. The successful selection uses its repository-local
resolved `.cache/robodojo_assets_repo/Assets/Eval_Layout/RoboDojo/arx_x5/0` tree.
Do not weaken symlink rejection. The native runner also checks resolved layout
paths and actual hashes after reset and before controls.

This snapshot binds the existing motor and arrange semantic configurations,
not the future four-way comparison. It does not cover installed binary/physics
asset integrity, prove the dependency graph complete, enforce itself in the
prototype runner, admit untouched task variants or establish policy obedience.
The next steps are evidence-backed qualification/pre-action enforcement and
the separately frozen pi0.5-first matched panel. Both GPUs were idle; the host
had5.5GiB free. New sensor-heavy waves need a storage plan first. Unrelated
CPU work and untracked remote files were preserved. No model weights were
downloaded to the Mac.

## Pre-Action Source Enforcement

The retained prototype operator now requires `--execution-freeze` for reference
episodes. It calls `protocol.verify_binding(..., require_execution_sources=True)`
before creating an output/worker/simulator and again after reset/model readiness,
before dispatching any controls. The second check rereads manifest/config bytes
from disk rather than trusting the earlier objects. It records both freeze and
execution-source hashes, and explicitly sets
`execution_binding_is_native_qualification=false`.

The archived deployed operator is in
`../evidence/reference-execution-binding001-20261002/operator_reference_rollout001.py`.
The worker-only entry point still loads no simulator; the reference driver
validates its worker source in the snapshot. Any changed code or config needs a
fresh binding; neither earlier preparation snapshot can authorize this changed
executor. The original full `protocol.verify` continues to require all seven
native checks and hashed evidence. Source binding alone cannot admit untouched
task groups; the prototype's unopened-group guard is deliberately retained.

This completes implementation of the two pre-action source checks, not runtime
admission or a comparison phase.401 CPU tests pass. Reuse the retained native
prediction/cadence/RNG/prompt/tokenizer audits to document each qualification
check's tested scope before producing a new qualification record. Do not simply
copy the older development qualification's true flags onto a new executor.

### Deployed Gate Verification

At revision `70dd9c7`, deployment first checked that the existing remote
prototype matched its earlier recorded hash, then copied the archived patched
operator. No externally changed file was overwritten. Fresh host preparation
produced `runs/reference-execution-freeze003.json`; the retained copy is
`../evidence/reference-execution-binding001-20261002/freeze003.json`.
Its execution-source SHA256 is
`57366bd5c4ab0d3de5e581633faa46bac5aead23e341bdf88addc72de8693e3c`.
On the host, `verify_binding` rejected freeze002 and accepted freeze003 with
the exact existing motor configuration. No worker, simulator or paid call was
started for this verification.

### Retained Evidence Review

The two-case arrange semantic audit covers2100 actual controls,70 predictions
per case, normal prefix cadence, source-proposal/request-prompt equality and
separate native RNG streams. Its tokenizer replay contains140 request/env rows;
all complete cleaned prompts survive, with at most115 active tokens out of200.
These are execution/plumbing results, not semantic obedience results.

Comparing the motor trial's pre-action source hashes against the current host
shows five unchanged files: native callbacks, coordinator, reference binding,
planner and report. The sixth file, the rollout operator, differs only by the
new freeze argument, two verification calls and binding-report fields; its
worker inference/control/reset code is unchanged in the reviewed diff.
The tokenizer report hashes the policy factory **function source**, not the
entire module file; comparisons must use the same hash scope.

The retained evidence supports cadence, ACK/context routing, model-boundary
prompt delivery and token survival for the tested source paths and prompts.
It does not prove future prompt retention or runtime support behavior for the
seven unopened groups. No broader native qualification has been issued or
historical result relabeled. The remaining work is a scoped qualification
record with per-check evidence, future-prompt retention enforcement, native
variant admission and the matched approach panel; no new capacity sweep is
needed.

### Future-Prompt Retention Guard

`semantic_lab/token_retention.py` wraps the source policy's actual input transform
once, decodes its active native tokens, verifies the full cleaned incoming
prompt, records the result and returns the exact same transformed object.
It does not rewrite text, sample a second prediction or change source RNG.
The standalone reference worker and shared pi0.5 worker both attach it.
Prediction metadata retains successful checks; an append-only JSONL records
checks before rejection so a truncated prompt does not disappear with a worker
exception. Truncation stops prediction delivery, with no repair/retry.

CPU checks cover pass-through identity, exactly one transform invocation,
truncation rejection and invalid masks. A separate bounded source-model replay
is prepared to compare guarded versus original inference on one retained input
with identical source RNG. No successful robot result or completed phase is
implied by these checks; results remain pending until the replay actually runs.

The replay subsequently completed on GPU1 at revision `6f5ecc6`, without
simulator actions or paid requests. Original and guarded source inference on
the same retained input/source seed0 produced identical50x14 predictions
(maximum absolute difference0.0) and identical post-inference RNG. The guarded
prompt retained101 active tokens out of200. The retained report is
`../evidence/reference-execution-binding001-20261002/live-token-guard-probe001.json`.
This is one input on one runtime, not full task/trajectory parity, obedience,
native variant admission or a completed benchmark phase.406 CPU tests pass.
