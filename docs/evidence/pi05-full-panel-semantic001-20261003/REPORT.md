# Full-Ten Semantic Task-Plus-Subtask Trial

## Condition

Ten distinct fixed standard-layout RoboDojo tasks concurrently, one shared
pi0.5 fused-vmap motor runtime, three native simulator groups on the rebuilt
two-4090 host. GPT-6.1 Sol/medium/Flex supplied language goals at sparse natural
motor boundaries. Semantic recovery was explicitly disabled; planner abstention
was allowed. No weight updates, task-specific executable skills or external
solution memories. This is a single-attempt screen, not official RoboDojo SR.

All-ten reset admission passed under freeze004 and the explicit simulator-only
C++ runtime preload recorded in numeric005. Installed binary equivalence to the
old-host baseline003 is not established. No setup changed during this trial.

## Outcomes

| Task | Outcome | Actions | Native Score |
|---|---|---:|---:|
| arrange_largest_number | Planner abandoned incomplete | 840 | Unavailable |
| build_tower | Planner abandoned incomplete | 630 | Unavailable |
| classify_objects_by_language | Native failure | 1100 | 0.0 |
| fold_clothes | Native success | 298 | 1.0 |
| imitate_sorting_sequence | Native failure | 622 | 0.0 |
| make_kong | Native failure | 600 | 0.0 |
| classify_objects | Native success | 714 | 1.0 |
| organize_table | Native failure | 1000 | 0.5 |
| pack_objects_into_box | Native failure | 1300 | 0.25 |
| put_bottles_into_dustbin | Planner abandoned incomplete | 105 | Unavailable |

Two verified successes among ten scheduled tasks; seven native endpoints and
three model-directed abstentions. No API/contract/controller errors or owner
interruptions are reported. Native score coverage is 7/10; a full-panel mean
is unavailable. Under score range [0,1], full-panel mean bounds are [0.275,0.575],
not estimates. Do not score the three unavailable results zero or report a
scored-subset mean as the full-panel mean.

## Execution And Accounting

- Cohort wall including startup: 1322.7775 s (22.05 minutes).
- 7,209 actual native actions; 483 motor predictions; 28 motor prompt changes.
- 74 semantic requests, 74 provider reservations, 74 settled Flex calls.
- Settled cost: $0.44593025. No new unresolved hold or standard-tier fallback.
  The existing shared $95 ceiling, $3 cohort cap and prior holds remain unchanged.
- Journal/prefix audit passed all ten cases. Every executed action matched its
  retained source prediction and emitted native command. All actor-request
  episode bindings, per-task effective request prompts and recorded full-prompt
  tokenizer retention checks passed; token limit is 200.
- Zero GPT-induced motor resamples, history resets or prefix shortening; no
  numeric corrections. Natural H50 prediction/H15 execution cadence is retained.
- Simulation pauses during synchronous planner inference. Timing includes
  coordination/peer waits and is not a pure physics-speed measurement.

The independent audit is retained beside this report. It proves record integrity,
prompt delivery/token survival and cadence, not subtask obedience, calibration
of visual judgments, task improvement or official benchmark qualification.

## Interpretation

There is no demonstrated gain: prior original-only baseline003 achieved three
successes, numeric005 three, and this semantic condition two. Both semantic
successes were also baseline successes; the bottle baseline success was lost
through early abstention. Different installed host binaries and one attempt per
task preclude a strong causal ranking.

All three final abstention decisions explicitly cite recovery being disabled:

- Number arrangement: GPT reported sustained lack of progress and an incorrect
  digit order, then abandoned at step 840.
- Tower: GPT could not verify the active upright-block placement and abandoned
  at step 630.
- Bottles: GPT saw an empty left gripper and the pink bottle no longer on the
  table but could not observe placement inside the bin; it abandoned at step 105.

These are model-authored judgments, not hidden-state diagnoses. In particular,
unobservable placement does not establish physical failure. Recovery-disabled
abstention is a clear treatment limitation; it does not establish that language
hierarchy cannot work or that the policy ignored every subtask.

Prompt plumbing and native cadence are now verified for this full-ten condition.
Reliable steerability and useful semantic recovery remain unproven. Do not
substitute more component tests for those experiments.

## Preservation

The complete raw run and remote audit were archived as
`runs/pi05-full-panel-semantic001-evidence.tar.gz` and downloaded locally.
Remote/local SHA-256 matched:
`bc049d07942dc3ad86179d5ce2af978f7f148a3a064f121e3277d48fd036e407`.
The extracted local run independently passed the same offline audit, receipt
`runs/pi05-full-panel-semantic001-local-audit.json`. Provider wire records and
the 74-call summary remain local. No model weights were copied to the Mac.
Remote raw evidence remains intact; owned relay/tunnel/worker cleanup completed,
and both GPUs reported zero allocated MiB after the run.

## Next Work

1. Complete a separately named original-only full-ten repeat on this host;
   preserve baseline003 rather than replacing its evidence.
2. Inspect retained current-episode goal/progress evidence and prepare a fresh
   recovery-enabled semantic condition. Preserve native cadence, sensor/evaluator
   separation, explicit stopping semantics and the same full-ten roster.
3. Distinguish wrong goal selection, weak motor response, mistaken observation
   judgments and premature abstention. Do not tune during an active frozen run.
4. Numeric reference reproduction is deferred at the owner's direction; keep
   `GPT_AS_POLICY_FIDELITY_REVIEW_20261003.md` as an interpretation boundary.
5. Held-out transfer, multiple layouts/seeds and second motor/backend comparisons
   remain unfinished. This screen does not complete the V5 objective.
