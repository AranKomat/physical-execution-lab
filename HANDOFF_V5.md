# Physical Execution Lab v0.5 — Semantic Subtask Hierarchy

Prepared 2026-10-02. Self-contained handoff for the external coding/research agent.

## 0. Start here: package and live-repository boundary

This is an **additive implementation update**, not another replacement of the working robotics stack. New code is in `semantic_lab/`, with `run_semantic.py` as its entry point. It turns the high-level model from a motor-trajectory reviewer into a language-subtask planner. It preserves the motor policy's normal executed prefix, observation acknowledgements, and inference schedule.

**Use the additive installer on a separate worktree of the live repository. Do not unzip this whole package over the GPU checkout.** The archive includes the previously supplied v0.4 source tree so its CPU examples and tests run standalone. It is not a complete mirror of current GitHub main. Direct Git cloning/binary download was unavailable on the build host. Current source seams and progress were inspected through the GitHub connector at:

- Repository: https://github.com/AranKomat/physical-execution-lab
- Reviewed revision: `dc2e704064bc8e997f64d7978bb9714e995e65f2`

The installer copies only new semantic code, tests, scripts, configuration guidance and these new documents. It never overwrites `k1lab/`, existing model/provider configs, native evidence, old handoffs, results, or deployment scripts. Native execution from the bundled older tree is intentionally blocked by the reviewed-source check. Newer live changes require a source-seam review, not resetting the working project to old code.

The previous `HANDOFF.md`, `TAKEOVER.md`, `run_bench.py`, and old `*_sparse` conditions remain historical. **This document supersedes their research priorities, not their factual evidence.** No native robot episode, GPU inference, paid API call, training run or remote repository write was performed for this update.

## 1. Converged objective

Test whether a strong general-language model can improve a frozen motor policy by supplying useful **current semantic subtasks**, without per-task executable skills, exploration-memory recipes, extra demonstrations, or weight updates.

The architecture is:

```text
original task + current RGB/proprio + within-episode progress/receipts
                            |
                     semantic planner
                            |
                current short language subtask
                            |
     original task / task+subtask / subtask-only prompt adapter
                            |
                 unchanged frozen motor policy
                            |
                unchanged native action prefix
                            |
            actual actions -> actual observations/ACKs
                            |
      semantic check only at a normal motor-prefix boundary
```

The planner controls language context, not individual arm movements. Opening a drawer, picking up an object and operating an appliance are normally language-conditioned behaviors. They are not added to a catalog of benchmark-specific Python skills.

Generic controllers remain useful when they genuinely provide better execution: navigation, known-pose transit, joint/EEF control, local sensing, and native machine/tool interfaces. A screwdriver, PLC or navigation stack can expose its own API. This update does **not** add such a catalog merely to improve benchmark scores.

## 2. Research references and what is actually borrowed

### π0.7: conceptual reference, not an available checkpoint

Primary sources:

- https://www.pi.website/blog/pi07
- https://www.pi.website/download/pi07.pdf
- Official released OpenPI stack: https://github.com/Physical-Intelligence/openpi

π0.7 uses training with diverse context, including task/subtask language, performance metadata and visual subgoals. Its appliance coaching illustrates language-level intermediate goals, rather than separate hand-coded appliance controllers. We adopt **language-conditioned hierarchy** as the design target. We are not reproducing its training, its motor model, or its generated-visual-goal conditioning. Simply adding text to a different checkpoint does not confer π0.7's learned steerability.

### τ₀-VLA: concrete high-level interface reference

- Paper: https://arxiv.org/abs/2608.16885
- Project: https://tau0-vla.github.io/
- Official source: https://github.com/sii-research/tau-0-vla
- Inspected revision: `f1665fbaf624d1468b168e3a54cccc9e326212d9`
- Proposal guide: https://github.com/sii-research/tau-0-vla/blob/f1665fbaf624d1468b168e3a54cccc9e326212d9/high_level/proposal/README.md
- Format source: https://github.com/sii-research/tau-0-vla/blob/f1665fbaf624d1468b168e3a54cccc9e326212d9/src/tau0_vla/high_level/proposal/format.py
- World model guide: https://github.com/sii-research/tau-0-vla/blob/f1665fbaf624d1468b168e3a54cccc9e326212d9/high_level/world_model/README.md

The released proposal interface consumes task, three named camera views, and task memory; it returns a subtask and updated memory. This is our interface reference. The released planner uses its own trained tokens/format and recommends adaptation to the robot/camera/task setup. We do not transplant those special tokens into π0.5/G0.5/Intern/XR1 prompts.

`semantic_lab/tau_reference.py` exports legal reset/current observations to the proposal JSONL format with explicit camera identity. It does not load a 9B model, train it, or integrate the complete search/value/reflection system. Missing camera views fail rather than being synthesized. Keep τ₀ as a future planner comparator, not another urgent model installation.

Distinguish two future uses of generated images: τ₀-style imagined outcomes help choose a subtask; π0.7-style visual goals condition motor execution. Neither is implemented. Do not put a generated goal image into a normal camera slot of a policy never trained to use it that way.

### Other references

- HomeBody: https://tml.stanford.edu/homebody/ — retain the ideas of local execution, typed sensing/controllers and persistent spatial context; do not copy its appliance-specific skill split into this branch.
- Unofficial OpenPI effort: https://github.com/Knight1112D/CBC_Pi0.7_Openpi — its own README labels the project unofficial and separates implemented chunking work from planned π0.7-like world-model work. It is not a π0.7 checkpoint or benchmark reproduction.
- K1: https://github.com/Robo-Harness/k1 — retain as the generic perception interface reference. RoboDojo still has the existing RGB contract, not an implemented K1 RGB-D port.
- GPT-as-Policy: https://github.com/anonymous-report-421/GPT-as-Policy — existing native server, robot-only DLS/FK, policy transport and evaluator separation remain in use through the live repo.

The new implementation is independent. The references motivate interfaces and experiments; no reported paper gains are imported as our results.

## 3. Latest inspected project status, not new results from this build

Read the live `docs/EXPERIMENT_PROGRESS.md` before starting. At the reviewed revision, exact π0.5 and G0.5 completed the same five-case development screen at 4/5 and 3/5 respectively. The earlier π0.5 sparse-review tower episode failed at the full native horizon after frequent shortening. An every-chunk trial ended on a quaternion contract error; a separate corrected trial ended at its 75-review budget after 658 native actions. These are different outcomes and must remain separate.

Intern's two-GPU feasibility and a successful native pilot were subsequently recorded. The more comparable 30-sample loopback timing was **1114 ms median**, not the earlier three-sample direct-probe median of about 820 ms. The inspected progress report still described the last Intern development case as live. Do not assume it later passed or failed. The XR1 RoboCasa365 screen remained 2/6 with supervision incomplete.

These are inherited development observations, not the result of this package. They do not establish broad policy rankings. Their raw negative/censored records must not be rewritten under a new condition name.

The active priorities are exact π0.5 first, G0.5 retained, Intern when its current native qualification/resources support it, and the separate XR1 RoboCasa365 track. Xiaomi RoboDojo is still deferred. Do not reactivate it, FLUX retargeting, BEHAVIOR, or the closed GPU-insertion branch automatically.

## 4. What changed from interruptive review

The old supervisor could choose accept, shorten or a numeric correction. A `shorten` changed when the motor policy was queried again. Monitor events could also truncate its prefix. Even a nominally sparse GPT schedule could therefore perturb the motor rollout substantially.

The new planner can return only:

- `continue`: retain the current language goal exactly.
- `set_subtask`: propose a new coherent language goal at a drained native boundary.
- `recover`: replace the semantic goal after evidence of failure, only when explicitly enabled.
- `stop`: abstain/end incompletely. This is never native success.

There is no `shorten`, action array, joint pose, EEF pose, tool code, or task recipe in the schema. Numeric GPT corrections remain in the historical runner, not this condition. A future correction condition must be a separate qualified experiment.

A soft tracking/failure event schedules a later semantic review; it does not interrupt the current motor prefix. A genuine controller fault, terminal signal or resource limit may still stop motion. Those interruptions are recorded separately and cannot be described as normal semantic shortening.

The first implementation is **synchronous at sparse native boundaries**. The simulator still pauses during GPT inference. Fixed step-based motor cadence is preserved, but uninterrupted real-time physical movement during GPT requests is not demonstrated. `mailbox.py` provides a tested, observation/epoch-bound admission primitive for a future asynchronous worker; the native runner deliberately rejects `async_planner=true` rather than pretending asynchronous operation works.

## 5. Implementation map

| File | Responsibility |
|---|---|
| `semantic_lab/contracts.py` | Immutable original task, three prompt modes, versioned context, bounded decisions, frame-supported claims |
| `state.py` | Current goal and retractable within-episode memory; minimum semantic dwell; periodic/event review requests |
| `planner.py` | Multimodal high-level planner through existing Responses/file/subprocess client; one semantic decision, no motor commands |
| `policy.py` | Source-specific instruction routing while preserving real ACKs, motor-prefix length and history |
| `transport.py` | New loopback semantic-policy protocol; context and prefix-completion operations; implementation hash handshake |
| `runner.py` | New isolated execution loop, scoring separation, contiguous ACK journal, prompt-exposure records and metrics |
| `protocol.py` | Reviewed adapter seams, new source/config/manifest freeze, semantic qualification gates |
| `audit.py` | Reconstructs actual prefix/action/review order from journal, not merely zero-valued counters |
| `report.py` | Full denominator, missing/status/score coverage and task-cluster paired summaries |
| `tau_reference.py` | Export to the released τ₀ proposal input format; no trained planner claim |
| `mailbox.py` | Future asynchronous response admission only, not a native asynchronous loop |

The baseline v0.4 code is not edited by the overlay. The launcher shim imports the **live** owned-process launcher and changes only which controller entry point it launches. Existing GPU placement, native fixture verification, cleanup behavior and source fixes remain in that live code.

## 6. Critical implementation detail: language is not a physical ACK

A policy proposal binds two different things:

1. The actual observation stamp: original task, current RGB, proprioception, measured robot poses and native step.
2. The effective policy prompt: original task, or its explicitly conditioned view.

The original observation is not mutated. The actor and evaluator keep the original instruction. The policy receives a temporary instruction-conditioned view, and the proposal is rebound to the actual observation with both hashes recorded.

Per backend:

- **π0.5:** the adapter sends the effective text through the source `instruction`/prompt argument. It is stateless with respect to delivered observation history. Its H50 prediction and 15-action execution prefix remain distinct: the normal 35-action suffix discard is not a GPT intervention.
- **G0.5/Intern/XPolicyLab:** context changes are admitted only after all exposed actions are acknowledged. The source input cache is refreshed with new language at the same boundary. In the inspected Intern adapter, source session `update_obs` advances action history only when model actions are pending; the rebind requires that queue to be empty. No fabricated ACK or full history reset is used to change instructions.
- **XR1 RoboCasa365:** the new text is supplied to the official client's inference argument. The existing image/state history is not appended again merely because a prompt changed at the same native step.

A normal `continue` triggers none of these changes. It does not reset a policy, alter its seed, invalidate a queue, change execution length or make an extra inference call. `finish_prefix` explicitly accounts for executed actions, normal unused prediction suffixes and genuine abort suffixes.

The adapter attestation records the string passed to its source model boundary. **It is not proof that tokenization retained the whole subtask, or that the policy obeyed it.** Inspect each model's tokenization/truncation, then measure language responsiveness on development cases. Qualified execution requires separate evidence for this.

## 7. Prompt variants and experiment conditions

`original_only` passes the exact original string, byte-for-byte. It is the baseline.

`task_plus_subtask` passes:

```text
Overall task:
<original untouched task>

Current subtask:
<one concise semantic goal>
```

`subtask_only` passes only the current subtask once one exists. The high-level planner still retains the original overall objective and constraints. Before an active subtask exists, both conditioned modes fall back explicitly to the original task.

These are **our experimental prompt formats**, not claims about π0.7's exact token layout or the training interface of the installed motor checkpoints. Task-plus-subtask might help, do nothing or hurt; subtask-only may be more compatible with some checkpoints. Do not declare either the winner in advance.

The configuration generator derives four conditions from one known working, artifact-bound motor config:

1. New motor-only original-task baseline.
2. Semantic shadow: GPT plans and maintains shadow progress, but cannot affect the motor prompt, action sequence, stop decision or cadence.
3. Semantic hierarchy with task-plus-subtask.
4. Semantic hierarchy with subtask-only.

Shadow is important. In a deterministic CPU fixture it must have the exact same actions, policy-call steps and ACK sequence as motor-only. On the GPU, report any numerical/runtime nondeterminism rather than asserting bitwise equivalence. Shadow still consumes model-call budget and wall time, so an external resource limit can censor it before motor-only finishes; disclose that rather than claiming complete physical parity. A separate review-frequency ablation may compare every natural boundary with sparse boundaries, **with no change to motor prefix length in either condition**.

Default reviews are requested every 100 native steps and admitted at the next natural prefix boundary. Default minimum goal dwell is 30 steps. These are generic development defaults, not literature-derived constants or automatic subtask-completion detectors. Completion and strategy changes are assessed from observed evidence during semantic checks. Local events can request checks. Do not use native reward/partial score as a phase detector.

## 8. Install the additive update

On the external machine, use a separate worktree so a live trial and its frozen sources remain intact:

```bash
cd /path/to/physical-execution-lab
git worktree add -b semantic-hierarchy-v5 ../physical-execution-semantic \
  dc2e704064bc8e997f64d7978bb9714e995e65f2

# From the extracted package; first inspect the dry-run output.
python scripts/semantic/apply_overlay.py \
  --target /path/to/physical-execution-semantic
python scripts/semantic/apply_overlay.py \
  --target /path/to/physical-execution-semantic --apply

cd /path/to/physical-execution-semantic
python run_semantic.py doctor
python -m pytest -q tests/semantic
```

The installer is checksum-checked and refuses conflicting existing files. It does not create a GitHub branch, push, install GPU dependencies, download weights or stop workers. Commit the additive update locally only after reviewing it. A newer worktree is also acceptable after checking drift in the adapter seams; do not bypass a mismatch by blindly changing hashes.

For a standalone CPU check of the extracted full package:

```bash
python -m pip install -e '.[test,multibench]'
python -m pytest -q
python run_semantic.py synthetic --output runs/semantic-cpu-check
```

A standalone `doctor` may report that the bundled v4 adapter files do not match the reviewed live base. That is intentional. Only the additive worktree is the native deployment target.

## 9. Wire the existing motor providers

Use the prepared provider environments and verified assets already present. Do not reinstall JAX/Torch/Isaac into one shared environment.

Generate conditions from a **working bound motor-only configuration**, not an old template with unresolved checkpoint hashes:

```bash
python run_semantic.py prepare \
  --from-config /absolute/path/to/working-pi05-motor-only.json \
  --output configs/local/semantic-pi05 --max-calls 32
```

The command preserves checkpoint identity, native action convention, environment settings and authorized model route. It removes old monitor/shortening/correction knobs. It does not alter the source configuration.

For remote providers, start the new semantic service in the existing motor environment:

```bash
python run_semantic.py serve-policy \
  --config /absolute/path/to/bound/in-process-provider.json \
  --port 19600 --allow-policy
```

The service wraps the existing `pi05`, `xpolicylab`, or `xiaomi_robocasa` provider. A legacy remote server is refused because it cannot accept semantic context updates. The client and server compare semantic protocol and implementation hashes. Keep each mutable policy session under one owner.

π0.5 still requires the verified underlying OpenPI server. Intern retains the live two-GPU component-placement configuration. XR1 RoboCasa365 retains its official checkpoint/client, crop, history and action conversion. This update does not make those dependencies optional or combine incompatible robots/action spaces.

## 10. Native pilot commands

For RoboDojo, reuse the existing source panel, full grouped manifest and a development case:

```bash
python scripts/semantic/launch_robodojo.py \
  --config /absolute/path/to/derived-semantic-config.json \
  --manifest /absolute/path/to/grouped-cases.json \
  --case-id YOUR_EXISTING_DEV_CASE \
  --source-panel /absolute/path/to/verified-panel.json \
  --sim-python /absolute/path/to/isaac-python \
  --robodojo-root /absolute/path/to/RoboDojo \
  --output runs/semantic-dev-001 \
  --development --allow-policy --allow-api
# This prints the plan only. Add --execute after reviewing it.
```

For the new motor-only baseline omit `--allow-api`. Do not run a source panel with different task/layout ordering or silently sample an easier scene.

For RoboCasa365, with its official policy server ready:

```bash
python run_semantic.py run-case \
  --config /absolute/path/to/derived-xr1-semantic-config.json \
  --manifest /absolute/path/to/existing-robocasa-manifest.json \
  --case-id YOUR_EXISTING_DEV_CASE \
  --output runs/xr1-semantic-dev-001 \
  --development --allow-native --allow-policy --allow-api
```

The task-set label `target50` is not the kitchen split. Preserve the existing split, registry ordering, global episode indices and seeds. Do not combine a different benchmark release or kitchen distribution with a published score.

A recorded-input policy probe is also available:

```bash
python scripts/semantic/probe_conditioning.py \
  --policy-config /absolute/path/to/policy-only-config.json \
  --observation /absolute/path/to/reset-observation.wire.json \
  --subtask 'A concise development-only instruction' \
  --prompt-mode task_plus_subtask \
  --output runs/prompt-probe.json --allow-policy
```

It issues no robot action or paid GPT call. It explicitly cancels the unused proposal rather than faking ACKs. It is not a zero-shot task result and does not prove instruction following.

## 11. Experiment sequence and stopping rules

**First: carry forward current evidence.** Finish/audit any already-owned running episode through the external operator; do not restart it from this handoff. Read authoritative budget and disk state. Preserve existing failed and censored runs.

**A — no-interference qualification.** Run the wrapped original-task motor baseline, then shadow. Verify native prefix lengths, policy-call indices, source prompt, ACK count and retained observation history. Changes in semantic review frequency must not create more motor inferences or history resets. If this fails, stop; do not spend GPT budget trying to compensate.

**B — prompt plumbing and responsiveness.** Check the exact input reaching each model, including whether tokenizer truncation removes the subtask. Confirm that changed instructions produce a legitimate different conditioning input without added observations. A response change alone is not success. A lack of response may indicate weak language following or incompatible post-training, not a broken planner.

**C — matched language hierarchy.** Use the existing fixed development roster. Compare original-only against task-plus-subtask first; run subtask-only as a controlled variant. Hold checkpoint, source runtime, native prefix, sensors, steps, GPT model/tier and case list fixed. Retain full failures, abstentions, call-budget stops and API capacity errors. Do not replace cases or rerun until a success appears.

**D — semantic recovery, separately.** Only after the basic hierarchy is interpretable, set `allow_semantic_recovery=true` in a new frozen condition. Recovery changes the language goal after an evidence-backed failure; it does not synthesize a new controller or numeric action. Do not call it successful recovery merely because an instruction was emitted.

**E — held-out tasks and second motor/backend.** Freeze choices on development data, then use the existing untouched task groups. Do not regenerate the split or tune on held-out failures. Extend to Intern/G0.5 or XR1 only as a distinct factor. A single good tower episode is not generalization.

**Later:** asynchronous native planning, learned phase/progress models, optional K1 RGB-D, τ₀ Proposal as planner comparator, motor post-training for explicit context conditioning, and world-model guidance. These are not prerequisites for testing the language hierarchy.

## 12. New qualification and freeze

Old motor-only approvals do not qualify the new conditioning interface. Generate a new template and attach hashed native evidence:

```bash
python run_semantic.py qualification-template \
  --config /path/to/condition.json --output /path/to/qualification.json

python run_semantic.py freeze \
  --manifest /path/to/grouped-cases.json \
  --configs /path/to/baseline.json /path/to/candidate.json \
  --output /path/to/semantic-freeze.json
```

The checks cover motor-only parity, exact model-boundary prompt, no-op continuation, context/ACK/history separation, independent native termination/scoring, model identity and subtask survival through tokenization. Complete a check only from evidence. Freeze records cover both semantic and legacy executable source, configuration and manifest. Code or configuration changes require new bindings.

For held-out `run-case`, omit `--development` and supply `--freeze` and `--qualification`. A freeze is integrity/preregistration, not proof of safe robotics or real-world transfer.

## 13. Metrics, audits and honest interpretation

Every new episode records the original task, conditioned prompt/hash, actual model-boundary exposure, semantic epoch, proposal, actual contiguous action ACKs, source prefix receipt, local abort reason, and native terminal result separately from planner progress.

Report success on the full scheduled denominator; partial score with coverage; native steps and simulated seconds; wall time split into policy, review, environment, ACK transport and evidence I/O; GPT attempts and provider usage; policy calls; prompt changes; actual semantic transitions; normal suffix discards; true aborted prefixes; and unresolved actions after transport errors.

Never label π0.5's routine H50-to-15 discard as a GPT interruption. Never drop a budget-censored episode from the denominator to improve apparent success. Cached and uncached tokens have different costs; reasoning tokens are a subset of output. Missing usage stays missing.

```bash
python run_semantic.py audit --episode runs/semantic-dev-001/controller
python run_semantic.py report \
  --manifest /path/to/grouped-cases.json --runs runs/evaluation \
  --partition test --conditions BASELINE_NAME CANDIDATE_NAME \
  --baseline BASELINE_NAME --candidate CANDIDATE_NAME \
  --output reports/semantic-comparison
```

The audit reconstructs cadence from the journal rather than trusting counters. Reports reject duplicate attempts, retain missing cases, separate statuses, and provide a task-cluster paired estimate. Small development panels remain descriptive. API wait pauses the simulator here; no real-time disturbance rejection is demonstrated.

## 14. Operating boundaries

Preserve the user's selected **GPT-6.1 Sol / medium / Flex-only** route. The configured model identifier is inherited from the user's working setup; this build did not establish API access. Use the existing budget-enforced relay. No automatic request retry, tier/model substitution or release of unresolved reservations is introduced. New semantic config token caps are not a substitute for the shared dollar ledger.

The inherited shared ceiling is $85. Its current balance is external state, not reliably inferable from this document. Check the authoritative ledger before any call. Likewise check actual free disk space; do not delete raw evidence or unrelated files. Never reboot the host, modify global GPU packages, stop unrelated workers or expose the policy service publicly.

Classify capacity errors, failed model parsing, contract errors and partial native episodes honestly. A known physical ACK is journaled before model-side ACK delivery so that a transport failure cannot erase already-observed motion. Unknown physical effects are never replayed automatically.

## 15. Deferred ideas retained rather than silently discarded

Egocentric human data remains a future representation/training direction, not an active dependency. Candidate sources discussed include:

- https://www.eidon.ai/
- https://github.com/Eidon-AI
- https://huggingface.co/buckets/eidon-ai/egocentric-pov
- https://huggingface.co/datasets/eidon-ai/tracker-pov-imu
- https://huggingface.co/datasets/LightwheelAI/EgoStandard
- https://egosuite100k.lightwheel.ai/

Re-audit licenses, actual modalities, synchronization, calibration and data quality before ingestion. IMU orientation is not ground-truth Cartesian hand position or robot actions. No dataset download, new pretraining pipeline, retargeter or collection hardware is included.

Persistent spatial memory from the BEHAVIOR work is also deferred. The present benchmark uses only current-episode memory and no target-task recipes. Preserve those separate repositories; import generic sensing/state interfaces later only when the task requires them.

## 16. Build verification and next deliverable

The package includes CPU tests for prompt modes, stale decisions, semantic epochs, retractable claims, context/ACK separation, the π0.5/XPolicyLab/XR1 source seams with test doubles, remote protocol, exact continuation/shadow parity, terminal/abort accounting, no reward leakage, new freezes, overlay safety and report denominators. Synthetic rollouts and audits exercise the entire new loop.

The build-time native gap remains: GPU tokenization/model responsiveness, actual prefix-history behavior in each full source runtime, simulator co-location/resource contention, real task improvement and asynchronous execution have not been demonstrated here.

**Next deliverable:** one native no-interference/conditioning qualification and a small matched language-hierarchy result with all outcomes retained. Do not write another platform, add task-specific skills, or begin world-model training before that evidence exists.
