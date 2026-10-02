# Experimental Semantic Vector Adapter

This directory preserves the prototype used on the two-4090 host. It is not
a change to the frozen production runtime or a completed hierarchy comparison.
Copy the operator files to the repository's ignored `runs/` directory to use
their existing imports; do not execute the native operator on a local Mac.

## Evidence

- `cpu-structural-report.json`: synthetic CPU episodes, distinct prompts,
  abstention of one episode while another continues, partial terminal prefix.
  No learned inference, physics or paid API calls.
- `native-motor-report.json` and `native-motor-audit.json`: five native sorting
  rows, 750 controls, 102.00 s rollout, source H50/15 and actual ACK audits.
  Explicit 150-action bound; incomplete, not native failures. Zero paid calls.
- The native callbacks expose RGB, proprioception and robot FK only. Native
  termination/reward enters controller results, not planner observations.
- Each episode uses the existing semantic runner and instruction policy;
  only the coordinator dispatches inference and physics. Source singleton
  inference preserves per-episode RNG rather than claiming fused parity.

## Remaining Gate

Qualify native per-episode planners, including divergent decisions, abstention,
prompt isolation and shared budget accounting. Paid calls require explicit
`--allow-api`; the retained pilot config is motor-only. Planner calls are
serialized by a host-wide file lock, so semantic wait can stall family barriers.
No planner throughput or hierarchy benefit is claimed. Bind a fresh matched
roster/cohort before larger comparisons, preserving historical serial results.

## Executed Pilot

```sh
env CUDA_VISIBLE_DEVICES=0 OMNI_KIT_ACCEPT_EULA=YES OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 \
  /root/miniconda3/envs/RoboDojo/bin/python3.11 -u \
  /root/physical-execution-lab/runs/operator_vector_pi05_rollout001.py \
  --num-envs 5 --steps 150 --tag 010 --task classify_objects \
  --inference-mode native_singleton \
  --semantic-config /root/physical-execution-lab/runs/semantic-vector-motor-pilot001.json
```

Tag 010 already exists; do not overwrite it or silently rerun it. Large sensor
payloads remain on the host; public evidence contains small reports and code.
