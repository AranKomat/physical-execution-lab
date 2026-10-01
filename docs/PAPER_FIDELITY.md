# DynaHarness: source-to-implementation fidelity audit

Source: **Deng et al., DynaHarness: A Dynamic Physical Harness for Self-Evolving
Robot Agents**, arXiv:2609.40306v1, 37 pages, September 30, 2026. Page numbers below
refer to the printed PDF pages. The uploaded file, not a search summary, is the
basis of this revision. Its SHA256 is in `configs/dyna/paper_spec.json`.

## The corrections that change the experiment

| Issue | What the PDF actually says | Change made |
|---|---|---|
| Geometry source | LIBERO execution parameters come from simulator state; physical experiments use camera images. Appendix A, p14. | New `privileged_sim` reproduction profile with body/geom/site/joint/contact extraction. No sensor-only claim. |
| Headline mechanism | Removing analytic contact skills changes A2ctrl 74.0% to 16.6%, close to bare 16.2%. Sec4.7, p9; Table16, p23. | Implement documented geometric/contact skill families, not only monitor/retry infrastructure. |
| Initial harness | Without evolution: 13.9% versus 17.1% for bare policy, seeds1–20. Sec4.5, p8. | Do not expect an unqualified wrapper to recreate the headline gain. Make native skill qualification the next milestone. |
| Planner output | Capability plus symbolic arguments, not poses. Sec3.2, p4. | Separate symbolic schema from metric grounding; numeric geometry arguments are rejected. |
| Baseline definition | A2static calls the one-step planner after nominal success, but not on failure. Fixed retries/reexecution replace dynamic reactions. pp24–26. | Dedicated A2static/A2seq/A2ctrl loops; trace auditor checks forbidden dynamic events. |
| Budgets | Spatial220, Object280, Goal300, Long520; main experiment uses Goal/10. p16. | Per-case suite budget, not 520 for everything. No reset-based budget renewal. |
| Action chunk | Ten actions per policy chunk; example vla_act contains two chunks/20 steps. pp27–28. | Require [10,7] chunks; explicit wrapper changes RPent's inspected five-action default. |
| Clocks | 20Hz control, 2Hz governance, 50Hz envelope checks; joint envelope2rad/s. pp4,14,27. | Separate latch/poll/control/watchdog accounting; optional direct physics-substep hook. Native hook still requires testing. |
| Latching | OR over sampled benchmark verdicts; cannot reconstruct events the sampler missed. pp4,14,29. | Independent `VerdictLatch`, same sampling period for on/off comparison. |
| Admission | Total successes nondecreasing; harness-attributed failures nonincreasing; success counts in policy-winning cells protected; zero contamination; broader regression needed. Eq5, pp5,15,32,37. | New cell-level gate, not v1's blanket preservation of every stochastic seed win. |
| Generalization | Post-selection block C is new states of the same40 task/perturbation cells, not new task families. p37. | Explicit block/split labels. No claim that official indices41+ reproduce block C. |
| Outcome counts | Infrastructure failures count against all episodes; some protocol amendments reran whole host assignments, not selected failures. pp17–21. | Full planned denominator, missing/failed cases surfaced, incomplete campaigns marked incomplete. |
| Self-evolution | Diagnostics and admission are automated; limitations describe them surrounding probing/revision. No detailed autonomous coding agent is specified. pp11,37. | Offline review/gate interface; no claim of reproducing an autonomous skill-synthesis agent. |

## Reference results must not be mixed

The main development aggregate is 594/800 = 74.25%. A separate remeasurement is
593/800 = 74.125%. The concurrent executor control is **592/800 = 74.0%**, versus
**511/800 = 63.875%** for A2static and **510/800 = 63.75%** for A2seq. Its archived
bare-policy comparison is **130/800 = 16.25%**. These are development comparisons.

The post-selection block-C champion is **602/800 = 75.25%**, reported as75.2%,
versus **140/800 = 17.5%**. This uses a newly generated state bank after freezing.
These values belong to the source paper, not this repository's measurements.

The primary executor comparison has89 Full-only and8 A2static-only wins. Its
+10.125-point effect is joint dynamic execution, not a recovery-only or
latching-only effect. Removing recovery alone changes the concurrent control by
only7/800, with reported p=.21. See Tables16–18, pp23–25.

## Mechanism map and remaining approximation

| Mechanism | Code | Exactness boundary |
|---|---|---|
| Symbolic advisory / complete initial plan | `prl/dyna/planner.py` | Schema and temporal role match; exact original prompt and decoder implementation unavailable. |
| Atomic scene/task epochs | `scene.py`, `engine.py` | Implemented; current local simulation has one episode/task epoch. |
| Simulation geometry | `native.py`, `scene.py` | Actual native objects/sites/joints extracted. Asset naming, semantic region class and handle association require native audit. |
| Pick/place stages | `capabilities.py` | Approach, descend, close, lift, corridor, lower, release, retreat implemented. Exact grasp geometry/controller gains are reconstruction choices. |
| Transport/object offset | `capabilities.py`, `engine.py` | Object-to-TCP transform measured after contact+lift. Not a whole-arm collision-free planner. |
| Receptacle slots | `destination_position` | Geometric free-slot selection implemented; not the authors' exact slot algorithm. |
| Flat support vs cavity | `destination_position` | Explicit region class and clearance checks; regression fixture rejects the paper's5mm-hob failure pattern. |
| Push refusal and carry substitution | `capabilities.py`, `engine.py` | Explicit final-relation-preserving substitution; `push_only` forbids it. Contact-span rule is reconstructed. |
| Drawer grasp change | `capabilities.py` |20mm shift implemented from p31. Exact widened closure threshold not provided; local grasp checking uses contacts+motion. |
| Drawer reseating | `engine.py`, `capabilities.py` | Bounded reseat and retry hook implemented. Offset and exact two-stalled-pull state machine remain approximations. |
| Knob/door/handle | `capabilities.py` | Bounded axis/pivot arc execution implemented. Need asset-specific *physical* calibration, not per-task solution tables. |
| Seven analytic removal arm | `CONTACT` | Seven documented families reconstructed. PDF does not enumerate the exact removed registry IDs. Treatment is labeled approximate. |
| Six recovery removal arm | `RECOVERY` | Four documented families reconstructed. Not an exact six-entry removal. |
| Keyframe return | `scene.py`, `capabilities.py` | Pose/held-state/episode provenance; not a reset or teleport. |
| Failure-state probing | `native.py` | Saves physical state at failure. Does not yet capture controller/RNG/full agent state; exact replay not qualified. |
| 13-layer attribution | `admission.py` | Ordered configurable reconstruction; unknown evidence yields an error. Exact original taxonomy/check predicates unavailable. |
| Eq5 + broader gate | `admission.py` | Mathematical admission semantics implemented. Requires reviewed attribution and complete broader coverage. |

### The stage-cost table is approximate

Table4 lists approximate observed costs. With70 carry steps, its listed stages sum
to211, although its whole pick/place row says approximately230. We do **not**
silently invent another19 physical actions. The reconstruction reserves at least230
steps at admission, while accounting only actual executed actions. This conservative
reservation and the interpolation schedule are engineering choices needing tuning
on the development block. They are not alleged exact source code.

### Local status is not task success

Jaw width alone does not prove holding an object. TCP arrival does not prove
insertion. The reconstructed grasp verification checks finger contact plus observed
object lift. Placement/joint checks are local geometry checks. The task outcome is
still only the native benchmark predicate. A successful command can be insufficient
for a task, and a locally failed command can coincide with native task success.

### What the simulator privileges do and do not mean

Using simulator geometry is *faithful to this paper's simulation experiment*.
It does not establish vision-based grounding or sim-to-real deployment. The frozen
policy is still given its normal camera/proprioceptive input; it does not receive
the explicit geometry used by the analytic system. This is a system comparison,
not a pure same-information model comparison. K1 should later replace the privileged
grounder in a separately labeled experiment, not be silently folded into this one.

## Source access / outstanding materials

The complete PDF was read. No supplement is embedded in the file. Page11 states
that an anonymized supplementary package contains implementation/configs/records,
but the PDF provides no direct package URL. The linked public implementation URL
`https://github.com/Denghaoyuan123/DynaHarness` returned404 when checked during this
revision. If that source becomes available, use it to replace guessed controller
constants and exact treatment rosters before spending a large evaluation budget.

The public policy's exact revision/hash, normalization, diffusion sampler, Qwen
quantization recipe, original prompts and original block-C state generation are
not fully specified by the PDF. These remain qualification items, not fabricated
answers. Absence of those details does not prevent useful independent reproduction,
but it does prevent an honest claim of exact parity today.
