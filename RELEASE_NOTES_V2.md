# Revision 2: what changed after the full PDF review

This revision supersedes the first “inspired” package for the user's DynaHarness reproduction objective. The old sensor/K1 code and historical documents remain available, but `paper_run.py` / `prl/dyna/` is now the main path.

## Material changes

1. Main LIBERO profile now uses explicitly disclosed simulator-state geometry, matching Appendix A, instead of imposing a sensor-only problem.
2. A symbolic capability planner is separated from geometric grounding. No slow-model numeric poses are accepted.
3. A reconstructed analytic library supplies approach/descent/grasp/lift/corridor/slot/placement and articulated mechanism execution. This targets the main source of the paper's gains, not just the runtime wrapper.
4. Native environment access is direct LIBERO-PRO; the frozen policy remains behind the inspected RPent transport. This preserves articulated geometry and independent completion sampling.
5. Separate A2static, A2seq and A2ctrl paths implement nominal-success replanning, bounded fixed retries, frozen sequences and dynamic reactions. Source gaps in exact branching remain explicit.
6. Source suite budgets, ten-action chunks, multiple clock domains, latching, affordability and plan/command leases are represented explicitly.
7. New model-service wrapper overrides RPent's five-action default, verifies local model bytes and exposes a checked live attestation.
8. New Eq5 cell-level admission and broader regression logic replaces the earlier per-seed interpretation.
9. All source findings now trace to the attached PDF. The original source-only audit is preserved in `docs/legacy/`.

## What has not happened

No native robot benchmark, GPU policy inference, live LLM request, real-hardware action or comparable performance measurement has been run. CPU fixtures are labeled synthetic and are not engineered to reproduce the paper's score margins. Native skill/controller/geometry qualification is the next step.

Exact low-level source constants, full capability/diagnostic rosters, model revision/quantization/sampler details and block-C files are still unavailable. The fidelity document distinguishes these omissions from implemented source requirements.
