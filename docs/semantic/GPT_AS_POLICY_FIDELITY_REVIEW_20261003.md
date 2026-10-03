# GPT-as-Policy Fidelity Review

## Why This Changes The Next Experiment

The owner questioned why our numeric hybrid did not show the large gain reported
by GPT-as-Policy. Our numeric005 is an adapted sparse screen, not a reproduction
of that reported condition. No negative claim about the original method follows
from its three successes, two native failures and five model-directed stops.

Source inspected on the GPU host: `external/GPT-as-Policy`, revision
`8f3d362b077d8efb77e2a7274d5b2c20e2243846`.
Public source: <https://github.com/anonymous-report-421/GPT-as-Policy>.
Public report: <https://anonymous-report-421.github.io/public-website/?lang=en&view=1>.
These observations describe the released implementation, not proof that every
historical published episode used exactly its current configuration.

## Material Differences

| Factor | Released reference | Numeric005 |
|---|---|---|
| Review cadence | Infer, inspect, decide, execute, then fresh inference/review | Sparse/event reviews; up to seven H15 prefixes / 105 actions between periodic reviews |
| Stopping | Frozen evaluation requires native termination; model abstention is forbidden | `stop` was accepted as `model_stop_incomplete` on five tasks |
| Action interface | Original student prefix, EEF target, or edit of the student trajectory | Accept/shorten or absolute EEF corrections; no trajectory-edit operation |
| Teacher execution | Persistent Codex agent with file/image inspection, scripts, calculations and writable notes | Structured Responses reviewer with four history rounds and compact progress |
| Teacher identity | Released settings require GPT-6 Astra/xhigh | GPT-6.1 Sol/medium |
| Evaluation | Multiple episodes with standard/randomized scene mix | Ten tasks, one fixed standard layout each |
| Motor inference | Source OpenPI inference | Shared fused-vmap executor; retained small numerical differences from singleton source |

The EEF target limits match in the inspected sources: 5 cm, 0.35 rad, up to five
correction steps; student acceptance is up to 15 actions from an H50 proposal.
Do not explain the performance gap simply as tighter target bounds. Sparse
monitor-triggered mid-prefix interruption is another treatment difference;
numeric005 recorded 113 interruptions and 515 shortened chunks.

Reference locations: `hybrid_rollout/robodojo/skill/SKILL.md`,
`robodojo_server/client.py`, `robodojo_server/validation.py`, `settings.py`,
and `public_results/provenance.json` under that pinned checkout.
Our locations: `k1lab/multibench/actor.py`, `runner.py`, `governor.py`, and the
retained numeric005 configuration/journal.

The reference provenance explicitly says official baselines are reweighted
for the selected ten tasks and scene mix, not paired seed reruns. Its published
62.6 versus 24.43 comparison is mean partial-credit score, not success rate.
Numeric005 has only five native final scores; a comparable ten-task mean is
unavailable. Do not substitute a scored-subset mean or score missing values zero.

## Five Numeric Stops

Retained returned `robot_decision` records explicitly requested `mode=stop`:

- Tower: repeated return to transporting a green nonwooden cube after attempted
  release corrections; GPT did not establish task completion or sustained stability.
- Language sorting: remaining category-placement errors and no useful recovery
  in the next near-reset motor proposal.
- Kong: no verified tile acquisition, matching-set assembly or declaration.
- Table organization: unresolved keyboard/drawer work and stationary proposals.
- Packing: uncertain disengagement from a box wall after repeated corrections.

These are model-authored visual judgments, not independently verified physical
diagnoses. They are neither provider failures nor native-scored task failures.
Premature stopping itself is a policy treatment, not missing infrastructure.

## Next Sequence

- [ ] Finish and independently audit semantic001 without changing its frozen
  task-plus-subtask condition. Preserve all native results, abstentions and errors.
- [ ] Complete a separate original-only full-ten repeat on the rebuilt host
  before attributing gains to the approach across different installed binaries.
- [ ] Prepare a separately named reference-style hybrid control: every-proposal
  review, native benchmark termination, equivalent student/edit/EEF interface,
  outcome/intent gate, public task semantics and persistent legal analysis context.
  Preserve the ten-task concurrent/method-major owner schedule.
- [ ] Record remaining departures explicitly, including teacher model/effort,
  inference vectorization, evaluation mixture and runtime. A Sol API reviewer with
  every-chunk review alone is still not the full reference agent.
- [ ] Estimate requests/cost against the existing $3 cohort/$95 shared limits
  before launching. Do not silently exceed them, drop tasks, or loosen gates.
- [ ] Establish that control before spending on further sparse-cadence tuning.
  Change one factor at a time where feasible; retain all previous conditions.
- [ ] Revisit direct only as a fresh generic-interface ablation, with explicit
  dual-arm shape and held-target semantics, not task-specific executable skills.

This does not replace the V5 language-hierarchy objective with a reproduction
project or claim any phase completed. It adds a necessary control to interpret
the numeric branch. No new paid experiment was launched for this review.

## Subtask Training Distinction

The original pi0.5 paper explicitly trains semantic subtask prediction and
conditions low-level actions on subtasks:
<https://arxiv.org/html/2504.16054v1> (Sections IV and IV-B).
Do not claim pi0.5 was never trained with subtasks. That does not establish that
our RoboDojo-finetuned checkpoint reliably obeys arbitrary externally supplied
`Overall task / Current subtask` text. Our model-boundary/cadence audit proves
routing, not language obedience or preservation of the original training behavior.
Equivalent subtask-specific training for this G0.5 checkpoint remains unverified.
