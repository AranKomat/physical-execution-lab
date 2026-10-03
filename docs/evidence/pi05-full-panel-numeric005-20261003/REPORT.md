# Full-Ten Numeric Hybrid: New-Host Trial

## Scope

One frozen numeric-hybrid method, ten distinct fixed RoboDojo tasks concurrently,
one shared pi0.5 motor runtime, three simulator groups on two RTX 4090s. No
task-specific skills, weight updates or new demonstrations. This is a bounded
screen, not an official benchmark result or a multi-seed success-rate estimate.

The fresh host required a cold-extension-cache repair, an explicit simulator-only
C++ runtime preload, and an owner-approved reboot after automatic Ubuntu updates.
Earlier numeric003/004 startup failures remain separate. Driver after reboot:
580.178.04. Task-layout/reset/FK admission passed for all ten cases. Installed
binary/runtime equivalence to the old host is not established.

## Outcomes

| Task | Outcome | Native Steps | Native Final Score |
|---|---|---:|---:|
| arrange_largest_number | Native failure | 1050 | 0.15 |
| build_tower | Model stopped incomplete | 685 | Unavailable |
| classify_objects_by_language | Model stopped incomplete | 994 | Unavailable |
| fold_clothes | Native success | 298 | 1.0 |
| imitate_sorting_sequence | Native failure | 636 | 0.0 |
| make_kong | Model stopped incomplete | 513 | Unavailable |
| classify_objects | Native success | 800 | 1.0 |
| organize_table | Model stopped incomplete | 560 | Unavailable |
| pack_objects_into_box | Model stopped incomplete | 344 | Unavailable |
| put_bottles_into_dustbin | Native success | 510 | 1.0 |

Three verified successes among ten scheduled tasks. Five native endpoints: three
successes and two failures. Five explicit `model_stop_incomplete` outcomes, not
HTTP errors, owner interruptions or native-scored failures. No task was replaced
or retried until success. Early stops are approach non-completions; their missing
native scores must not be silently treated as zero or excluded from a full-panel
mean. Score coverage is 5/10. Full-panel score bounds are [0.315, 0.815], assuming
the native score range [0,1]; these bounds are not an estimate of missing scores.

## Execution And Cost

- Wall including startup: 2117.27 seconds (35.29 minutes).
- Native actions: 6390, with matching contiguous physical ACKs. Integrity audit
  passed all ten case streams and indexed robot-only FK admission.
- Policy calls: 537; actor reviews: 145; corrected actions: 37; motor actions: 6353.
- Shortened policy chunks: 515; recorded interruptions: 113. These are distinct
  counters, not interchangeable with routine H50-to-H15 suffix discards.
- Provider reservations: 146; settled calls: 145; actual settled cost: $2.7378600.
- Retained no-output Flex capacity hold: $0.0538185, request numeric005-0.
  Charged with this hold: $2.7916785, below the frozen $3 cohort cap.
- Same GPT-6.1 Sol, medium reasoning. Flex capacity rejection triggered only the
  authorized same-model standard fallback. All actor outputs used standard tier.
  No generic retries, model changes or released holds.

Timing fields include coordination/peer waits in this synchronous simulator
architecture; do not interpret their sum as a pure physics or kernel profile.
Shared inference used partial batches as tasks/interventions diverged. Simulation
pauses during actor inference; this does not demonstrate real-time control.

## Interpretation And Next Work

The earlier original-only baseline had three successes and complete native scores
on all ten cases. This trial does not show a numeric-hybrid benefit: the verified
success count is unchanged, several tasks were abandoned, and review/cadence
overhead is substantial. Different installed host binaries also limit direct
causal attribution against that retained baseline.

Next: run the separately frozen semantic task-plus-subtask condition on the same
ten tasks, preserving normal motor cadence. Retain every outcome and paid hold.
A same-host original-only repeat is appropriate before claiming a quantitative
gain across the rebuilt host; it is a separate named repeat, not a replacement
for baseline003. Full direct control and multi-seed/generalization comparisons
remain incomplete. This trial does not complete the overall research phases.
