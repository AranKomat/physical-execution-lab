# Supervision And RoboCasa365 Bring-Up

This is the earlier bring-up snapshot. For the completed six-case baseline,
initial bridge parity and incomplete native supervision, see
[XR1 development screen](XR1_DEVELOPMENT_SCREEN_20261002.md). Its next actions
supersede the preparation-only items below; do not repeat the baseline screen.

## Stage C: API Evidence, Not Physical Success

The G0.5 motor-only development screen remains 3/5 successful. Two fresh sparse
supervision attempts on sorting layout 1 each generated one policy proposal but
executed zero native actions. Neither establishes supervised policy performance.

- `g05-sparse-sol-flex-dev-001`: HTTP 404 parameter-routing rejection.
- `g05-sol-flex-route-002`: isolated route check succeeded; actual model
  `openai/gpt-6.1-sol`, served tier `flex`, one function call, 5128 input tokens,
  145 output tokens, zero reported reasoning tokens, cost $0.0071035.
- `g05-sparse-sol-flex-dev-002`: HTTP 200 structured failed response, `usage:null`,
  explicit Flex processing temporarily unavailable. No automatic retry or Standard
  fallback. A null-usage handling error in the relay was subsequently fixed.

The loopback relay keeps credentials on the Mac and uses the existing shared
budget ledger. It removes the upstream `parallel_tool_calls` parameter because
the chosen route does not advertise it; the local actor still requires exactly
one function call. Future resolved pilot provenance must record this normalization.
No model, reasoning effort, tier, images or action schema is substituted.

Accounting snapshot: $75.865119744300 spent plus unresolved reservations, leaving
$9.134880255700 under the $85 ceiling. There are 153 unsettled reservations.
The two new unknown-usage holds, $0.0538605 and $0.0538500, remain reserved.
These snapshots are not substitutes for the authoritative shared ledger.

Public sanitized records are in `docs/evidence/g05-supervision-bringup/`.
Full API audits remain private: they contain ephemeral relay authentication.
Native backups are retained locally under `runs/native-evidence/`; archive hash
`d4089a19d0b4e7ee3b76a5c8df5bf954adb9fd725759dacfd8f4ba4acb30aad4`
matches the remote copy. Both native attempts and their infrastructure failures
remain in the evidence; neither is hidden as a missing successful episode.

## Stage D: Official XR1 Provisioning

Host: `92.180.27.84:53210`, repository `/root/physical-execution-lab`.
No system package, driver, unrelated process or model-precision change was made.

- Simulator: isolated `.venv-rc365`, Python 3.11, RoboCasa source revision
  `456174f62b89b8fca99eaaf33949c29fec9cfc2a`, robosuite revision recorded in
  `upstream.lock.json`, MuJoCo 3.3.1, NumPy 2.2.5, Torch 2.7.1.
- Deploy: isolated `.conda-xr1`, Python 3.12, Torch 2.8.0+cu128,
  torchvision 0.23.0, torchaudio 2.8.0, transformers 4.57.1,
  official prebuilt Flash Attention 2.8.3 wheel.
- Checkpoint: `XiaomiRobotics/Xiaomi-Robotics-1-RoboCasa365`, pinned HF revision
  `3a6d0293bfa90759d34a7fc48c2c62413cd7bcf4`, Apache-2.0, stored remotely at
  `model-artifacts/xr1-robocasa365`. Three safetensors shards and tokenizer hashes
  match the publisher metadata. No RoboDojo checkpoint substitution.

Verified SHA-256 hashes:

```text
model-00001-of-00003.safetensors 5c9412f29facda098d5dcf1a58c06830edeeba7c0c59799480dd28b35c3fcc53
model-00002-of-00003.safetensors 72884ec9b026794df9e3b5c1eb75341e503ae94f0e2555d1178157e3290b7f7d
model-00003-of-00003.safetensors 5859c4408351a0b894c6175cf6f7a41e5e431637517a1d45587ad94f03d29cac
tokenizer.json aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4
```

RoboCasa macros were generated; official kitchen asset acquisition completed.
Dependencies and hashes alone do not qualify reset/render, inference or native success.
The unmodified official BF16/Flash Attention server loaded on physical GPU 1
and listened on loopback port 19611. `MIBOT_SERVER_SEED=7` was explicit, and the
checkpoint was loaded offline. The loader logged a Flash Attention dtype
warning, but completed; inference dtype/behavior is not yet qualified. The
load-only probe ended at its explicit 120-second timeout, not an OOM or crash.
Its log is backed up at `runs/native-evidence/xr1-server-load-001.log`.

The official scheduler generated the full 2500-job manifest for target50,
50 trials/task, seed 7. It is backed up under
`configs/local/xr1-target50-reference-manifest-001.json`; no jobs executed.
The harness also generated `configs/local/xr1-target50-cases-001.json`. All 2500
task names, global indices and episode seeds match the official manifest.
These initial manifests retain test partitions; any case used in bring-up must
be excluded from subsequent held-out claims, not silently reused as a test.
Server loading and subsequent native bring-up remain separate gates.
Use one policy server on GPU 1 and simulator on GPU 0, not eight workers.
Retain split pretrain, task set target50, seed 7, history 4 / interval 2,
crop 0.95 and 16 actions/query. Generate the full 50-trial manifest before
selecting a preregistered development subset. A horizon-20 smoke is not a full
episode or benchmark replication.

## First Native Baseline

The unmodified official evaluator `evaluate_task` ran one explicit episode
index 0 with `num_trials=50`, preserving the official global-index/seed formula.
Task selection used the official target50 registry. No demonstration or task
recipe was imported; the policy received the official RGB/proprio/instruction
processing. This is development evidence, not an untouched held-out episode.
Exclude this seed/case from later held-out claims.

- Smoke `xr1-smoke-001`: CloseBlenderLid seed 7, 20 actual steps, no success.
  The shortened horizon was a bring-up check, not a negative full-task result.
- Full `xr1-native-001`: same task/seed with a fresh server/environment,
  native horizon 900, **success at 286 steps**, 18 policy queries, zero GPT calls.
  The official evaluator's episode-loop progress timer reports 22.98 seconds;
  this excludes cold model loading and preceding environment creation and is
  not directly comparable to the harness runner's complete episode wall metric.
- Snapshot during smoke: simulator GPU 0 used 1671 MiB; policy GPU 1 used
  10326 MiB. These are device snapshots, not isolated peak allocations.
- Official logs retain observation-space checker warnings at reset/step,
  missing optional robosuite-models/mink warnings and video metadata fps fallback.
  Neither the controller nor source preprocessing was changed to suppress them.
- Video samples render nonblank, but show substantial robot occlusion in the
  official views. Native success is evaluator evidence, not a new independent
  visual-clearance or physical-safety certificate.

Local archives under `runs/native-evidence/` match remote SHA-256:

```text
xr1-smoke-backup.tar.gz fed25ae04d7fd21af67007eb82ab75dd10e0a635a99d957e4456a77d8d4fdfba
xr1-native-backup.tar.gz 77f5cfcf955a0d8dc54d0150fe893d5fb0bea14019161191d5401868407ff862
```

Both worker/server pairs exited. Both GPUs were idle after the native run.
This establishes the official XR1-only path on one development case; it does
not qualify the harness bridge, complete Stage D, reproduce 57.28%, or establish
that supervision improves this policy.

## Next Physical Results

1. Bind and qualify the harness XR1 bridge against this official configuration.
2. Preregister a balanced development subset, retaining all successes/failures.
3. Resume bounded G0.5 supervision when Flex capacity is available, keeping
   ancillary-bound-004 and normalization provenance identical across conditions.
4. Freeze and run matched comparisons only after development qualification.

Exact RoboDojo pi0.5 remains unavailable. Intern and Xiaomi RoboDojo remain
deferred by owner scope; two-GPU Intern sharding has not been tested.
