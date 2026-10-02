# V5 Live-Repository Integration

## Scope and Provenance

The owner requested incorporation of `physical_execution_lab_semantic_v5_overlay.zip`
and `PHYSICAL_EXECUTION_LAB_V5_HANDOFF.md`. The checksum-checked additive installer
was reviewed, dry-run, and applied to a separate worktree based on live commit
`37f59b7`, not the older bundled source. All four adapter blobs match the overlay's
reviewed `dc2e704` base. The intervening runtime changes are the explicit
comparison180 budget/preparation profile; they do not alter those adapter seams.

All 37 overlay files were added without overwriting legacy runtime files.
The supplied overlay manifest and build-host evidence are preserved unmodified.
Repository integration adds package discovery/CLI entry point for `semantic_lab`
and updates the active documentation. Old qualifications do not qualify V5.

## Local Verification

- Full CPU suite: 369 passed, including after integration changes.
- Doctor: all four reviewed adapter blobs match; asynchronous native runner false.
- Eight synthetic rollouts across four conditions complete. Their outcomes are
  fixture behavior, not robot success rates or hierarchy improvement.
- All eight synthetic journal/cadence audits pass. An isolated wheel build
  includes the semantic package and `physical-semantic` console entry point.
  The initial no-build-isolation attempt lacked local setuptools; the isolated
  build succeeded without modifying the existing runtime environment.
- Native config preparation on the Mac is blocked by missing remote artifact
  paths, as expected. Do not strip artifact checks; prepare on the GPU host.
- No new paid calls, model downloads, remote deployment or native V5 episodes.

## Carry-Forward Evidence

- Fixed development screens: pi0.5 4/5, G0.5 3/5, Intern 3/5. These cover two task
  families, not full RoboDojo. Their rankings are not reliable benchmark rankings.
- Matched warm loopback medians: pi0.5 454 ms, G0.5 801 ms, Intern 1114 ms.
- The old held-out motor-only trial completed at 1050 actions with failure,
  score 0.15, 70 policy calls and no GPT calls. The task is now opened; do not
  tune V5 on it or relabel it as untouched/development.
- All 2,562 baseline payload files were copied locally and SHA-256 verified
  under `runs/native-evidence/pi05-matched-heldout-001/motor_only/`. Redundant
  remote native observation payloads were retired only after verification;
  retained records and local full evidence remain available.
- Old sparse/every-chunk conditions for that held-out study were not started.
  Their pause is a direction change, not an observed failure or success.
- A CPU-only motor-freeze refresh failed on relative evidence paths before any
  episode. Its partial record remains; it does not justify replaying a trial.

## Next Sequence

1. Qualify wrapped original-only cadence and semantic shadow without interference.
2. Verify exact model-boundary prompts, tokenizer survival and ACK/history behavior.
3. Freeze a matched development comparison: original-only, task-plus-subtask,
   subtask-only, with the existing fixed roster and unchanged motor prefix.
4. Add evidence-backed semantic recovery only as a separately frozen condition.
5. Freeze choices before unopened held-out groups and a second motor/backend.

The first runner is synchronous: simulation pauses during planner inference.
No uninterrupted real-time planning, native language responsiveness or native V5
benefit is established. Retain Sol/medium/Flex-only, the authoritative $85 shared
ledger and unresolved holds. Check disk and ledger before execution. No reboots,
global package changes or interference with unrelated CPU work.
