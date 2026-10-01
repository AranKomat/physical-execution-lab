# Agent instructions — paper-grounded revision 2

## Work on the user's current objective

The user wants a faithful-enough implementation to reproduce comparable **DynaHarness** gains, not a generic harness demo. Read `HANDOFF.md`, `docs/PAPER_FIDELITY.md` and the attached 37-page PDF. Main work belongs in `prl/dyna/` through `paper_run.py`. The old sensor-first `run.py run` is a separate legacy path.

Do not rewrite the architecture, merge into BEHAVIOR, reopen GPU assembly, train unrelated models, or polish a factory animation. Native analytic competence is the critical next milestone.

## Source and evidence rules

1. Appendix A explicitly permits simulator-state geometry in the evaluated LIBERO implementation. Use `privileged_sim` and label it honestly. Do not call it sensor-only or silently mix it with K1 results.
2. The slow brain proposes symbolic capabilities/relations, not metric poses. Never parse native goal clauses into a pre-solved action plan. No task-ID/seed special cases.
3. The large headline gain depends on the evolved analytic library. A successful runtime unit test is not evidence of comparable task gains.
4. Keep archived development, concurrent ablation, and new-state results separate. No supplied paper numbers belong in local result rows.
5. The PDF does not enumerate every skill/controller constant, exact removal roster or thirteen diagnostic checks. Preserve reconstruction labels; replace missing details with author source when available.
6. Qwen3-VL-4B-Instruct and public PI pi0.5 LIBERO are the main reproduction models. Stronger reasoners, piRLinf/fullshot weights, K1, and different libraries are separate conditions.

## Native bring-up

Use a fresh Python 3.10–3.12 environment. Bootstrap only reviewed pins. Dependencies are source-inspected, not yet native-qualified. Verify setup before starting hundreds of episodes.

Inspect geometry/frames/contact and controller scaling; perform one small native move; inspect a ten-action policy chunk; then execute real analytic and policy smoke cases. Qualify the physics-substep watchdog. Do not call repeated stale reads or a 20 Hz per-action check a 50 Hz physical loop.

The current direct environment seam uses pinned LIBERO-PRO and RPent's policy client. Its object/site/joint mappings, approach conventions, cavity handling and local effects need native testing. Prioritize these over more infrastructure.

## Evaluation rules

- Goal 300 / Long 520 physical actions. No resetting the budget on retry. Record settling separately.
- Native task predicate is distinct from local completion and model claims. Same sampling/latching contract across matched controls.
- A2static replans after nominal success only; A2seq plans once; no dynamic substitution or failure replan in either. Audit their actual traces.
- Match state hashes, model bytes, observation contract, settings, prompts, capability library and environment. Log server attestation and unseeded stochasticity.
- Hold out states only after freezing. Full denominator includes infrastructure failures. Incomplete runs remain visibly incomplete.
- On host faults, predeclare symmetric rerun/replacement rules and retain originals. Never retry only the failed benchmark episodes for a better score.
- No test-set memory, oracle branch table, or direct contact geometry in a sensor-only condition.

## Safety and resource boundaries

No real robot is supported. Native simulation and model/API use are explicit opt-ins. Respect configured call/time/token ceilings. Do not invent a guaranteed dollar cap from token estimates. Never print keys or silently download weights. Do not attach to unrelated held simulator episodes or stop shared services.

If a native write may have partially executed, stop and reconcile; do not retry it. Never bypass a guard merely to achieve a success score. A simulation watchdog is not a hardware safety certification.

## Regression / revision

Use the actual failed state for diagnosis when possible, but the current physics-only snapshot is not a complete controller/RNG/agent resume. Attribute failures with evidence, treating labels as hypotheses. Local thirteen-layer names are reconstructed.

Revise reusable physical mechanisms, not individual task IDs. Paired targeted admission is necessary but insufficient: run broader checks on the same candidate hash. Preserve cell success counts in policy-winning cells per Eq.5, rather than imposing the old per-seed rule. Record any human-written versus agent-generated change honestly.

Before handing off: run CPU tests, compile, source audit, native checks actually available, and keep `IMPLEMENTATION_STATUS.md` and `validation.json` accurate. Report native gains only when measured.
