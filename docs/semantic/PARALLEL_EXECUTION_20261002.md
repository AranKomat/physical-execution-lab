# Parallel Execution

## Current Choice

Use the existing two RTX 4090s before renting more GPUs. Two independent
pi0.5/task workers completed concurrently: tower layout1 control on GPU0, sorting layout1
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
The existing budget relay holds the campaign's `runner.lock` exclusively for
its lifetime. Separate ports alone cannot enable concurrent paid trials. Keep
one paid planner plus one no-API motor trial until shared reservation/settlement
locking and per-worker authentication are explicitly implemented and reviewed.
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

## First Completed Worker

Tower layout1 original-only finished with native success, score 1.0, 729 actions,
49 policy calls and 433.13 seconds controller wall time. The source/ACK/scoring
audit passes. Its matched hierarchy candidate subsequently failed at
1050 actions, score 0.0, 70 policy calls, 674.43 seconds and ten settled GPT
calls/$0.05549250. One prompt change, no resets, shortening, faults or unresolved
actions. Its source/ACK/scoring audit passes; all 2,301 backup files are locally
SHA-verified before redundant remote observation retirement.
This negative development pair is retained without retry. The earlier positive
tower0 pair does not establish a reliable hierarchy benefit.

Policy inference took 36.94 seconds (about 8.5% of controller wall time).
Environment stepping plus ACK handling took 367.51 seconds (about 84.8%).
Thus shared-model inference batching alone cannot remove most of this run's
wall time, even with an idealized elimination of inference. Episode concurrency
overlaps the dominant simulator work. This is one run's timing breakdown, not
a controlled serial-versus-parallel throughput experiment.

The GPU1 sorting layout1 transport variant completed at the full 1100-action
horizon without success, native partial score 0.4, 74 policy calls and 622.48
seconds controller wall time. Zero GPT calls, controller faults, resets,
corrections, semantic shortening or unresolved actions. Its final five-action
prefix stopped at the native horizon. This is a negative development result;
no hierarchy candidate in this worker binding has run yet.
Its audit passes and all 2,323 files are locally SHA-verified. The tower control
has 1,553 SHA-verified backup files. Redundant remote observations were retired
only after verification. Public small records are in
`docs/evidence/semantic-pi05-hierarchy-parallel-001/motor_only/sort-l1/` and
`docs/evidence/semantic-pi05-hierarchy-001/motor_only/tower-l1/`.
