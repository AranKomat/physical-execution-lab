# Native RoboDojo Bring-Up

Subsequent update: one G0.5 motor-only development episode succeeded. See
[the pilot report](NATIVE_PILOT_20261002.md). The exact pi0.5 artifact is still
blocked; no checkpoint substitution was used to obtain that G0.5 result.

**Host:** 2x RTX 4090, NVIDIA driver 580.178.04 after reboot
**RoboDojo:** pinned checkout at `ee67a1468510da7624a089164402359f2afc72c8`
**Case:** `classify_objects__standard__g0__l0` (development partition)
**Panel:** `robodojo_panel60_v1`

## Completed

- Downloaded and filtered the RoboDojo assets; the host asset cache is about 66 GiB.
- RoboDojo installation verification: 14 passes, 0 failures; 54 runnable tasks.
- Isaac Sim 5.1 / Isaac Lab / cuRobo imports and CUDA visibility passed.
- Repaired the host NVIDIA user-space/kernel mismatch (`580.178.04` libraries with an old `580.95.05` module) by rebooting.
- Installed the missing `libGLU.so.1` runtime dependency.
- Formal 60-case source panel imported and a one-case development manifest was created.
- Capture-only reset/render succeeded. Evidence is retained in `runs/native-evidence/capture-005/`.
- Bounded native action probe succeeded. One valid 14D `x5_joint14` command produced exactly one native ACK and one post-action observation. Evidence is retained in `runs/native-evidence/native-action-probe-001/`.
- FK validation passed for both arms with approximately `5.8e-8 m` position error and `1.7e-7 rad` rotation error.
- Native completion conditions were non-vacuous: one `check_list` condition was registered.

These are bring-up and interface results, not task success results. The probe intentionally did not attempt the sorting task.

## Remaining Gate

The exact RoboDojo-trained pi0.5 artifact is not on the host:

```text
configuration: pi05_base_aloha_full_sim_arx-x5_seed_0
normalizer: arx_x5_sim
checkpoint: RoboDojo-sim-arx_x5-joint-0/59999
```

The OpenPI/JAX environment is installed and sees both GPUs, but a generic pi0.5 checkpoint must not be substituted under this identity. The next substantive experiment is one native pi0.5 smoke episode after the exact checkpoint, processor, normalizer, and artifact manifest are available.

## Host / Harness Notes

- The native launcher now discovers the pinned XPolicyLab checkout so the donor `client_server` import works in capture-only mode.
- The native extra includes `msgpack`, required by the donor RPC protocol.
- Simulator startup/reset is roughly 110 seconds on this host; this is environment/render setup overhead and does not include policy inference.
- RTX/material warnings remain in the Isaac log but did not prevent the verified capture or one-step probe.
