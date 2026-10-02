# Parallel Execution

## Current Choice

Use the existing two RTX 4090s before renting more GPUs. Two independent
pi0.5/task workers are launched: tower layout1 control on GPU0, sorting layout1
control on GPU1. Each has its own loaded checkpoint, seed0 RNG, simulator,
policy bridge, proposal artifacts and output directory. These are full native
development task attempts, not additional component tests. No paid calls.

| Worker | GPU | Source / Bridge / Sim Ports | Cohort |
|---|---:|---|---|
| Original | 0 | 19114 / 19603 / 19117 | semantic-pi05-hierarchy-001 |
| Transport variant | 1 | 19115 / 19604 / 19118 | semantic-pi05-hierarchy-parallel-001 |

GPU1 receives an explicit recomputed adapter binding and separate config freeze.
Its inherited cadence/prompt evidence includes the previous GPU1 context/ACK
probe. This does not establish new bitwise physical parity or instruction
obedience. GPU1 results must not silently enter the original condition's report;
matched candidates should use the same worker binding. Preserve the original
five-case roster and record missing variants rather than replace cases.

The operator refuses paid GPU1 work until parallel relay accounting is reviewed.
Do not share relay tokens, overwrite output paths, or merge episode histories.
Audit source NPZ/journal equality, inference indices, natural H50/15 cadence,
actual ACKs and native evaluator agreement independently. Back up and SHA-verify
payloads before retiring redundant observations.

## Shared-Model Task Batching

Inspected upstream OpenPI `Policy.infer` supports batched transformed inputs.
The current websocket server nevertheless calls inference synchronously per
request, with no batch scheduler. The JAX policy also advances one shared RNG;
concurrent clients alone would therefore serialize inference and mix random
streams. Our source metadata explicitly says fresh seed0 server per episode.

A later throughput experiment should share immutable model weights while
keeping per-episode RNG, prompt, sequence indices and action receipts isolated.
Measure batch1 versus batch2 throughput, simulator coexistence memory and
per-episode output/cadence parity before adopting it in a new execution freeze.
Do not claim batching is implemented or faster yet. Multiple simulators can
also contend for CPU, disk and GPU rendering; utilization samples alone do not
prove end-to-end speedup.

Intern currently needs both GPUs and remains separately scheduled. Additional
GPUs become useful if simultaneous Intern/other-model work is required, or
measured queueing/throughput shows these two workers are insufficient.
