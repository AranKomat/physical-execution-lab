# Start here — PDF-grounded revision

This package supersedes the first `physical_runtime_lab.zip` for the DynaHarness
reproduction effort. **Read `HANDOFF.md`, then `docs/PAPER_FIDELITY.md`.**

The attached 37-page source paper is included at
`references/2609.40306v1.pdf`. Its **Appendix A, page 14** materially changes the
setup: LIBERO grounding uses simulator state. Do not accidentally attempt the
sensor-only extension while labeling it a matched paper reproduction.

```bash
python -m pytest -q
python paper_run.py audit
python paper_run.py run \
  --config configs/dyna/fixture_A2ctrl.json \
  --manifest manifests/synthetic_dev.json --output runs/local-contract-check
```

The above is a **synthetic contract check**, not a robotics result. On a GPU host,
follow the native setup and experimental sequence in `HANDOFF.md`. Preserve the
existing BEHAVIOR project and the closed GPU-assembly branch; neither is modified.

Do not start by adding more agent abstractions. Qualify geometry and a genuinely
useful analytic pick/place, then run the frozen policy and matched executors.
