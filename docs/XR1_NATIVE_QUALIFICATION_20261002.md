# XR1 Motor-Only Qualification

Evidence reviewed 2026-10-02. This closes the motor-only native bridge
qualification gate for the exact resolved configuration hash
`368fbcda158133fe2c57f881ff739c9b36c787da0f79f5759ac597218848eb30`.
The machine-readable record is
`docs/evidence/xr1-development-screen/motor-qualification.json`.
It does not qualify other configurations merely because they share a provider.

## Evidence Review

| Required Check | Evidence And Scope |
|---|---|
| Native reset/render | All six fixed development cases returned legal RGB/proprioception, completed full episodes without infrastructure errors, and retained initial/decision-boundary sensor captures in the verified local backup. |
| Action space | Adapter uses the official 12D converter. Fresh official-client initial OpenDrawer prefix matches all 16 harness actions exactly. Later complete-trajectory parity is not asserted. |
| Nonvacuous completion | Source Gym wrapper lines 374-385 obtains success from native `_check_success()`. Two episodes succeed; four reach their original horizons unsuccessfully. No replacement completion conditions are installed. |
| Legal actor inputs | Source `observation_to_state` lines 58-71 selects measured EE, gripper and base state; `collect_images` lines 74-78 selects official cameras. Adapter passes instruction and actual measured history. Hidden object state and evaluator scores are not inference arguments. No GPT actor runs in this qualified configuration. |
| Observation ACKs | Policy history accepts exactly one observation per real native step and rejects gaps. All 7845 journal ACKs are contiguous; proposal accounting matches actual execution and discarded suffixes. |
| Controller timing | Every episode records native 20 Hz and simulated seconds equal actual actions / 20. Official conversion/controller are unchanged. Wall time includes inference/setup and is not a real-time guarantee. |

Source review on the live host reconfirmed Xiaomi revision
`0dd7aef8dc87296246aae812a1f59ccb708e5546` and RoboCasa revision
`456174f62b89b8fca99eaaf33949c29fec9cfc2a`. Xiaomi's checkout is clean;
RoboCasa has only an untracked asset README, not modified tracked source.
The retained results include runtime/package fingerprints and the bound policy
identity; this is not a universal binary/runtime lock.

## Limits And Next Gate

This is a retrospective, evidence-reviewed software qualification, not a new
physical experiment or a certificate of real-world safety. Original records
remain unchanged and marked `native_unqualified`. All six cases remain
development. Fresh-server seed-7 scheduling remains different from the official
persistent 2500-job schedule; no published-score reproduction is claimed.

Stage D remains incomplete. Full matched sparse/every-chunk supervision,
correction-path evidence and a frozen scored comparison are still missing.
The incomplete Flex-capacity trial is not a qualification for GPT corrections.
Freeze the reviewed motor-only configuration/source before opening untouched
held-out tasks; changes to either invalidate that freeze. Do not run an expanded
motor-only evaluation without the matched comparison and budget plan.
