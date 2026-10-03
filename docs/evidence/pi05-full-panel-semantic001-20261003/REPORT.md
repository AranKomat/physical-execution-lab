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

There is no demonstrated reliable gain. The fresh same-host original-only
baseline004 achieved two successes and mean native score 0.345; this semantic
condition also achieved two successes. Semantic gains classification (native
score 1 versus 0.4), retains folding, and loses bottles through early abstention.
Packing improves descriptively from 0.10 to 0.25. Baseline003's three successes
and mean 0.44 remain historical old-host evidence, not a clean matched contrast.
Single attempts, numerical/runtime variation and different rollout RNG-stream
consumption preclude a strong causal ranking even for the same-host pair.

All ten semantic task trajectories have now been visually inspected against
their actual prompt epochs. See
[the visual review](../pi05-semantic-visual-audit001-20261003/REPORT.md) for
per-task findings and images. Visible compliance is mixed: several correct
object/action sequences, clear destination/object mismatches, and continued
overall-task behavior under a narrow current subtask. This is not proof of
language causality or evidence that every failure is instruction rejection.

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

Post-trial inspection of the exact actor-visible bottle frames confirms that the
pink bottle is visible on the table at step 0 but not at step 105; the current
overhead view shows the right fingers around the yellow bottle. The left wrist
view is empty, and the bin interior is not adequately visible. This is compatible
with ongoing object handling but does not prove pink-bottle placement, a stable
yellow grasp, or successful task completion. The model's inability to verify the
active pink-bottle goal is not enough to certify physical failure.

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

1. Same-host baseline004 is complete; preserve baseline003 as historical evidence.
2. All-ten visual review is complete. A recovery-enabled condition is prepared
   but unrun; it isolates the recovery toggle, not motor steerability. Next
   distinguish prompt-format responsiveness using matched states and short
   observed rollouts before attributing this screen to deficient subtask training.
3. Distinguish wrong goal selection, weak motor response, mistaken observation
   judgments and premature abstention. Do not tune during an active frozen run.
4. Numeric reference reproduction is deferred at the owner's direction; keep
   `GPT_AS_POLICY_FIDELITY_REVIEW_20261003.md` as an interpretation boundary.
5. Held-out transfer, multiple layouts/seeds and second motor/backend comparisons
   remain unfinished. This screen does not complete the V5 objective.
