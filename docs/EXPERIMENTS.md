# Experiment sequence — PDF-grounded revision

Use `paper_run.py` and `configs/dyna/` for this sequence. The old `run.py` remains
available for the original sensor/K1 engineering branch, not paper replication.

## 0. CPU verification and source audit

Run all tests and `python paper_run.py audit`. Read Appendix A, D.1 and the fidelity
matrix before editing. Do not count synthetic fixture results as robotics evidence.

## 1. Native substrate / geometry / model identity

On the external GPU machine, fetch pinned upstreams using `scripts/bootstrap.py`,
install the isolated native environment, and freeze versions. Create a catalog of
actual installed official initial states; make a small *development* manifest.
Run `scripts/native_paper_smoke.py` without motion first. Inspect names/geometry,
camera orientation, articulated axes, regions and source hashes. Then use the
explicit1cm motion option. Confirm actual low-level scale and watchdog callbacks.

Serve the frozen **public PI pi0.5 LIBERO checkpoint**, not the stronger RLinf
LIBERO130 fullshot checkpoint. Fingerprint its actual bytes. The supplied server
wrapper uses10-action chunks and exposes a live attestation. Check an unexecuted
policy chunk before beginning a full policy episode. Exact source checkpoint and
sampler parity still require documentation.

## 2. Analytic competence before aggregate scores

Use a few disclosed paper cases as diagnostic examples, not held-out evidence:
`goal_swap[5]` seed22 (push refusal/carry); `10_task[7]` seed21 (two objects in a
basket); `10_task[6]` seed23 (two relative placements); and later `10_swap[9]`
seed21 (mug into microwave, close door). The latter is tight at520 steps and should
not block the first simple physical success.

Start with genuine native pick/place and object-effect verification. Add
receptacle slots/corridor, then door/knob, then drawer shift/reseat. Test physical
parameters across multiple development states. A test count or a valid plan does
not substitute for a useful executed skill. No per-task/seed coordinate branches.

The original un-evolved harness underperformed the policy. If our basic analytic
skills do not work, stop the800-case run and fix those skills. Do not make more
Qwen calls, add another high-level agent, or rename a TCP motion 'success'.

## 3. Matched systems and runtime controls

Freeze the local library/parameters. Use the same official development state
manifest across **bare**, **A2static**, **A2seq** and **A2ctrl**. Run a small native
pilot over predetermined cells first; then cover40 cells ×20 states21–40.

The headline comparison is the complete analytic system versus frozen policy.
The runtime-specific comparison is **A2ctrl versus A2static**, with the same
capabilities, prompt/model, sensing, geometry and budgets. A2seq is supporting
because its planning horizon/output schema differs.

Each run is separately recorded. `scripts/audit_paper_run.py` checks that nominal
arms do not substitute/recover/replan on failure, A2seq calls its planner once,
and withheld capabilities are not executed. If a run fails this audit, it is not
the intended treatment, regardless of its success rate.

## 4. Ablations after useful competence

Run local no-contact, no-recovery, no-VLA and latch-off treatments. Our removed
rosters are explicit approximations until original source is available. Latch-off
must keep the sampling period fixed; never compare an every20-step unlatched poll
to an every10-step latched poll and attribute the difference to latching alone.

Do not treat effect sizes as additive. No-VLA also affects routing/runtime. Do not
infer VLA weakness from its low success conditional on being called; difficult
states disproportionately trigger it.

## 5. Evolution and generalization

Diagnose source evidence, reproduce the physical fault from the actual reached
state, and change one reusable mechanism. The saved physics archive is not yet a
complete replay checkpoint; qualify controller/RNG reconstruction before branching.

Use Eq5's cell-count gate and a broader regression block. Both must test exactly
the same candidate hash. Reject or revert a failing candidate; do not redefine the
gate afterward. The thirteen-layer taxonomy in this package is a reconstruction.

After freezing, test untouched official states, clearly labeled as our held-out
bank. The paper's new800-state bank C is not bundled. Do not call an index selection
'newly sampled states' or silently substitute it for the author's bank.

## 6. K1 / larger model / harder benchmark extensions

Only after the above is interpretable:
- replace simulator geometry with K1 RGB-D grounding, holding downstream control
  as stable as possible; call this the sensor-grounded extension;
- swap the high-level model with matched inputs/budgets and recorded cost;
- add LIBERO-Plus or a limited RoboSuite transfer suite with separately frozen
  settings and controllers; do not assume the main configuration transfers.

No BEHAVIOR integration, robot post-training, factory animation or new vertical
research is on the critical path of this reproduction.

## Reporting

Report every planned episode, infrastructure flag and missing case. Use the full
planned denominator as the source paper does; mark unfinished campaigns unfinished.
For complete paired runs, report discordant wins/losses, exact two-sided test and
bootstrap intervals resampling task/perturbation cells (20,000 draws, seed20260926).
Report physical steps, successful-task wall time, failed-task wall time, policy
calls, actual model calls, fast decisions, refusals, substitutions, rework/replans,
and analytic versus policy step share. Do not quote scheduler computation latency
as end-to-end latency, and do not quote synthetic tests as model performance.
