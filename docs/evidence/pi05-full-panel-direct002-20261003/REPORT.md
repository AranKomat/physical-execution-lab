# Full-Panel Direct Continuation

## Scope

Run `pi05-full-panel-direct002` used all ten distinct fixed standard-layout
tasks concurrently, three native simulator groups, no motor policy, and
GPT-6.1 Sol medium. Flex was preferred, with owner-authorized same-model
standard processing after an explicit no-output Flex capacity rejection.
This is an adapted sparse-direct screen, not a faithful paper reproduction.

## Results

- Cohort wall time including startup: 1,647.29s (27.45 minutes).
- 468 executed native actions, 111 client HTTP attempts.
- 110 provider reservations: 108 settled, two unresolved holds.
- Settled cost: $1.38820125. Holds: Flex request `-1`, $0.042099;
  standard request `-109`, $0.132714. Total charged including holds: $1.56301425.
- The last raw relay summary precedes the failed final request and reports
  only109 attempts; the retained request directories and ledger establish110.
- Zero native terminal outcomes and no native scores. This is NOT0/10
  physical success rate and cannot support an approach ranking.

| Task | Actions | Outcome |
|---|---:|---|
| arrange_largest_number |0|Translation bound rejection|
| build_tower |161|Model stopped incomplete|
| classify_objects_by_language |0|Translation bound rejection|
| fold_clothes |0|Translation bound rejection|
| imitate_sorting_sequence |35|8-value action;16 required|
| make_kong |70|8-value actions;16 required|
| classify_objects |69|HTTP error after relay halted|
| organize_table |66|HTTP error after relay halted|
| pack_objects_into_box |0|Translation bound rejection|
| put_bottles_into_dustbin |67|HTTP error after relay halted|

The standard failure was an OpenRouter admission-control429: credit
availability could not be verified in time. It was not a Flex rejection or
evidence of robot-task failure. No automatic retry followed. Its full hold
remains unresolved. The original Flex-only `direct001` remains separately
retained, not overwritten or retroactively reclassified.

## Interface Diagnosis

Four initial requests violated the frozen0.05m Euclidean translation bound:
number arrangement about0.060m; language classification0.062/0.071m;
clothes folding included0.067,0.101 and0.134m waypoints; packing included0.10
and0.15m waypoints. All waypoints are validated against the observation's
current EEF, not merely against the preceding waypoint. Consequently a
sequence of individually small increments can still exceed the decision bound.
The two shape violations omitted one arm's required8-value segment.

Of107 returned correction decisions, requested tick counts were:
1:9,3:16,4:8,5:63,6:2,8:3,10:4,12:1,40:1.
At25Hz, five ticks represent0.2s simulated time. The actor WAS given
`control_hz=25`, both current EEF poses, the translation limit and action
convention. The problem is not missing frequency information. The contract
does not clearly spell out cumulative waypoint validation/held-target
semantics, and the tool schema does not constrain each action to16 values.
These are plausible generic interface confounds, not evidence that all
direct task reasoning or physical execution is fundamentally impossible.
No limits, prompts or schemas changed during the trial.

## Verification And Preservation

All ten live reset/FK admission gates passed. Control audit passed for every
journal and468 ACKs, including robot-only source DLS bounds and zero motor
policy calls. This is control-record integrity, not task success proof.
All1,066 files in the complete local run backup hash-match the remote tree;
aggregate SHA256 of the sorted relative-path/hash JSON:
`29e3b5a1d63a43879b3e49f0034e8612ccbf18d3905268662705055f4078fa60`.

Local raw backup: `runs/pi05-full-panel-direct002/`.
Local paid wire records: `runs/pi05-full-panel-direct002_api/`.
Public control audit: `control-audit.json` beside this report.
Remote unique records remain retained. No model weights were copied to Mac.
Owned simulator processes and relay/tunnel were cleaned up; both GPUs
reported0MiB afterward. Remote root disk had about3.0GiB free.

## Remaining Work

1. Keep original-only baseline003:3/10 native successes, mean score0.44,
   12.52minutes, zero paid calls. Do not import singleton development scores.
2. Run numeric hybrid across the whole ten-task panel, then semantic hybrid,
   one method at a time with shared fused pi0.5. Neither has full-panel results.
3. Before new paid requests, explicitly account for standard429 request
   `pi05-full-panel-direct002-109` and retain its hold. Flex authorization
   does not authorize retries of arbitrary HTTP failures.
4. Any post-trial source edits require a fresh source freeze. The relay
   metadata correction changes no control behavior or historical raw records.
5. If revisiting direct, use a separately named generic interface ablation:
   explicit16-value action schema and waypoint/lease semantics. Do not loosen
   limits midtrial, silently replace the failed condition, or add task recipes.
6. Report missing/censored slots honestly. Only after the first complete screen
   use preselected additional matched layouts for promising methods.
