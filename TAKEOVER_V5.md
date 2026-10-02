# External agent takeover — semantic hierarchy v0.5

Read `HANDOFF_V5.md` and the LIVE repository's latest `docs/EXPERIMENT_PROGRESS.md` before acting.

## Primary goal

Implement/qualify the already-added language hierarchy: **GPT chooses a current semantic subtask; the motor policy executes its normal native prefixes continuously between sparse semantic checks.** Do not make GPT a critic that repeatedly shortens motor proposals.

The new modules are `semantic_lab/`; entry point `run_semantic.py`. All source-native infrastructure remains in the existing live `k1lab/` tree.

## Install correctly

This archive contains the old v4 baseline for standalone CPU use, plus the new additive code. It is NOT a complete checkout of the latest GitHub repository. Do not overwrite the GPU checkout by extracting everything into it.

Use a new worktree from the inspected revision `dc2e704064bc8e997f64d7978bb9714e995e65f2`, or review later source drift. Run the extracted `scripts/semantic/apply_overlay.py --target <worktree>` first in dry-run mode, then with `--apply`. It adds new files only and refuses conflicts. `python run_semantic.py doctor` checks the adapter source seams. Preserve local modifications and active workers.

## What to test first

1. Run CPU tests and the synthetic trace auditor. No paid model calls yet.
2. Start the semantic policy wrapper around an existing verified provider. Do not use the legacy server: the new client requires context/prefix-completion operations and a matching implementation hash.
3. Qualify original-task motor-only and shadow no-op parity. A GPT `continue` must not reset, shorten, reseed, resample or add a physical observation to the motor stream.
4. Verify task/subtask text at the real model boundary and through tokenizer truncation. Then measure prompt responsiveness on development cases; do not assume it from the API.
5. Compare `original_only` with `task_plus_subtask`; test `subtask_only` as its own configuration. Keep model weights, control/action cadence, observations and case list unchanged.
6. Only then enable semantic recovery in a separate condition or evaluate held-out groups.

Exact π0.5 is the first backend; retain G0.5 and the current Intern two-GPU path. XR1 RoboCasa365 stays a separate track with its original checkpoint/client/crop/history and split. Xiaomi RoboDojo/FLUX retargeting are not automatically reactivated.

## Non-negotiable semantics

- The actor/evaluator original task is immutable. Only a policy-facing view receives the subtask.
- `continue` is a no-op for the motor. `set_subtask` changes language only at a natural prefix boundary.
- No task-specific controllers/recipes, task demonstration retrieval, grader-guided subtask detection, or hidden object geometry.
- Real observations ACK real actions exactly once. A language cache refresh is not an action ACK. Do not clear WAM history merely to change an instruction.
- Routine H50/15 suffix discard is not supervision. Early aborts and ambiguous requests are accounted separately.
- Planner `stop` is incomplete/abstention, not native success. Partial scores never enter its prompt.
- The native v5 runner is synchronous at sparse boundaries. The mailbox utility is NOT a proven async robot runtime; do not claim continuous real-time execution through GPT waits.

## Scope and operating constraints

π0.7 is the conceptual reference; τ₀'s task/images/memory→subtask format is the open implementation reference. No π0.7 checkpoint, visual-goal policy training, τ₀ value/search stack, learned phase detector, new egocentric pretraining or hardware action is supplied by this package. K1 RGB-D has not been ported to RoboDojo.

Use GPT-6.1 Sol medium/Flex-only through the authorized budget relay. Check actual shared $85 ledger and outstanding holds before requests. No automatic retry, model/tier fallback, worker reset or hold release. Preserve the previous negative/censored runs. Check free disk space and preserve native backups and unrelated workloads.

Prepare conditions from a *working bound motor-only config* using `run_semantic.py prepare`; do not use unresolved templates. New semantic freezes/qualification are mandatory for held-out evaluation. Old motor-only evidence does not automatically qualify language conditioning.

Return measured results with actual prompt exposures, prefix/ACK audits, task success/partial score coverage, wall-time breakdown, GPT cost/calls, policy calls and all failures/censoring. The next milestone is physical evidence, not more architecture.
