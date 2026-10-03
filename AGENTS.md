# External implementation agent instructions

## Active v0.5 Direction

Read HANDOFF_V5.md and docs/semantic/LIVE_INTEGRATION_20261002.md first.
Semantic language hierarchy supersedes the v0.4 research priorities below;
the old evidence and runners remain intact. Qualify unchanged motor cadence and
shadow parity, then model-boundary prompt/tokenizer plumbing, before comparing
original-only, task-plus-subtask and subtask-only. Preserve actual ACK history.
Do not resume the old interruptive-review sequence automatically or tune on the
opened held-out arrange_largest_number case. Use Sol6.1/medium/Flex preferred and
the existing budget-enforced relay. The owner authorizes same-model Standard
fallback only after explicit no-output Flex capacity rejection, with all holds
retained, a $95 shared ceiling and $3 per cohort. No native V5 qualification is
implied by CPU tests. Current status/checklists in docs/semantic supersede the
handoff's stale scoped-phase status, $85 ceiling and Flex-only restriction.

Read HANDOFF.md and IMPLEMENTATION_STATUS.md before editing. This v0.4 scope
supersedes earlier benchmark prioritization; original K1/LIBERO code remains.

## Objective
Obtain honest native comparisons of frozen-policy-only, every-chunk GPT review,
and sparse GPT review on RoboDojo, then Xiaomi-only vs Xiaomi+GPT on RoboCasa365.
Separately compare robot-policy-free dense vs sparse direct control. Use
`gpt-6.1-sol` with explicit Responses service tier, not an implicit Astra fallback.

## Boundaries
- Never report synthetic CPU success/call counts as robot performance.
- No benchmark solution recipes, added task-specific skills, or offline target
  demonstrations. Current-episode memory and native task instruction streams are
  allowed. Benchmark-trained policies are labeled as such.
- Do not send evaluator score, hidden object state, success geometry, future
  contact simulation, or another episode's trace to the actor.
- Keep benchmark/controller/policy normalization, action conventions, native
  frequencies and source revisions explicit. Do not silently turn EEF outputs
  into joints or duplicate a missing camera.
- Policy queues are acknowledged ONLY after actual native steps. Reset/cancel
  on a shortened prefix/intervention; never fake acknowledgements.
- Respect episode/task budgets. Unknown RPC outcomes poison the attempt; do not
  retry uncertain physical writes or reset the same scored episode.
- Same-model/same-policy comparisons need matched sensors, data, budgets and
  service tiers. New models and new sensors are separate experimental factors.
- Development and test task groups stay separate. Freeze after native development
  qualification, before opening held-out results. Keep failures and missing runs.
- A generic motion monitor cannot detect every wrong semantic intent. Preserve
  periodic reviews; do not disable all reasoning because trajectories are finite.
- Do not redesign the framework. First make one native case and one real policy
  chunk run correctly. Fix actual source-contract mismatches before broad sweeps.

## First actions
1. Run the CPU suite and synthetic matrix.
2. Read source contracts in docs/multibench/SOURCES.md; bootstrap only needed repos.
3. Capture a development RoboDojo observation with zero API calls.
4. Qualify π0.5, then Xiaomi/G0.5/Intern interfaces and latency on the same hardware.
5. Run one complete native episode per proposed backend before paid wide evaluation.
6. Bind artifact/provider settings, record qualification, freeze, then compare.

Do not edit or operate the user's unrelated BEHAVIOR or closed GPU-assembly
workers. No GPU instance, paid API call, remote deployment or account action is
authorized merely by opening this archive; use the owner's explicit budget and
environment permissions.

## Execution efficiency

Overlap independent setup, downloads, validation and analysis whenever useful.
Keep simulator episodes, mutable policy sessions and GPU memory reservations
isolated; do not parallelize dependent actions within one episode. Preserve this
practice for subsequent runs, not just initial provisioning.
