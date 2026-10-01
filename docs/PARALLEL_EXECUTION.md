# Parallel Execution

Default to overlapping independent preparation, CPU tests, artifact checks and
development experiments when resources permit. Do not turn the phase sequence
into a queue of serial component diagnostics.

- Give each stateful motor policy its own process, port and episode owner.
- Give each simulator a fresh output directory and separate RPC port.
- Deliver observations only after actual native acknowledgements; never share
  temporal buffers or use invented acknowledgements to batch episodes.
- Check measured VRAM before colocating a simulator and policy. Two 24 GiB GPUs
  are separate budgets, not an automatic 48 GiB device.
- Retain failed setup and inference attempts separately from physical episodes.
- Label CPU/disk/GPU overlap in timing evidence. Use isolated runs for final
  latency rankings and matched policy comparisons.
- Stop only processes owned by the experiment; preserve unrelated workloads.
- Back up completed native evidence locally and verify hashes before cleanup.

Explicit policy RNG seeds bind future providers and are recorded in proposal
diagnostics. They do not guarantee bitwise CUDA determinism or retroactively
seed older pilots. Keep source-session seeds consistent with the wrapper seed.
