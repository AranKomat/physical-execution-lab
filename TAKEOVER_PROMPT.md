# External Codex takeover — DynaHarness PDF reproduction

You are continuing the attached `physical-runtime-lab` repository, paper-grounded revision 2. Read `START_HERE.md`, `HANDOFF.md`, `AGENTS.md`, `IMPLEMENTATION_STATUS.md`, `docs/PAPER_FIDELITY.md`, and `references/2609.40306v1.pdf`.

**Objective:** obtain comparable real LIBERO-Pro gains through a faithful-enough implementation of DynaHarness's analytic library plus fast/slow execution. Do not merely build another inspired wrapper or inflate a synthetic benchmark.

The key correction from the old package: the paper uses **simulator-state geometry for LIBERO**. Main path is `prl/dyna/` / `paper_run.py`; legacy `run.py run` is sensor-first and not the reproduction. Keep K1 as a later separately measured replacement of privileged grounding.

The paper's large gain depends on analytic competence. Nominal versus dynamic execution with the same library is a separate roughly ten-percentage-point comparison. Your first native priority is working physical skills under the official 300/520 action budgets, not more harness infrastructure.

Immediately:
1. Run CPU tests and the paper audit. Check whether author code/supplement is now available; replace uncertain local reconstruction details with documented source where possible.
2. Provision one isolated Python 3.10–3.12 LIBERO-PRO environment and the pinned RPent policy service. Use public PI pi0.5 LIBERO, NOT RLinf/fullshot. The provided server explicitly changes RPent's default five-action chunk to ten and emits a live weight/config attestation.
3. Create the actual hashed state catalog. Qualify two cameras, current simulator geometry, contacts, handle/joint bindings, OSC scaling, one bounded motion and one policy chunk. The helper script `scripts/native_paper_smoke.py` supports inspect-only, 1 cm motion, and inference-without-execution.
4. Qualify an analytic pick/place; then receptacle slots/relational placement/drawer/knob/door on a disclosed development subset. Correct physical asset metadata without task-ID/seed-specific branches. Current insertion is cavity placement, not a finished universal insertion controller.
5. Freeze code/settings and run matched `bare`, `A2static`, `A2seq`, `A2ctrl` via `paper_run.py`. Audit traces, retain all failures, and report actual counts, uncertainty, calls, steps and wall time. Treat source-paper scores only as references.

Unknowns are explicit in the fidelity matrix. Exact skill source/rosters, all constants, original prompt, sampler/quantization and block-C bytes are not in the PDF. Do not fill them in as source facts. The 50 Hz native substep hook is mock-tested, not native-qualified. No native episodes, LLM calls or model training have been run in the build environment.

No real-hardware action is authorized. Respect user-approved API/GPU budgets and unrelated services/held episodes. Do not reopen BEHAVIOR/GPU assembly or work on factory animation. Update the handoff with source diffs, native evidence, failures, next experiments and precise claims.
