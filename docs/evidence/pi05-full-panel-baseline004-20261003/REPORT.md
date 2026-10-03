# Same-Host Full-Ten Original-Only Control

Completed 2026-10-03 on the rebuilt two-4090 host used for semantic001.
This is a separately named control, not a replacement for old-host baseline003.
It uses the same fixed ten-task standard-layout roster and screened fused-vmap
pi0.5 runtime, original instructions only, native H50 predictions and H15
execution prefixes. No GPT calls, prompt interventions or numeric corrections.
Single attempts are descriptive screens, not official per-task success rates.

## Results

| Task | Native Success | Score | Actions |
|---|---|---:|---:|
| arrange_largest_number | No | 0.15 | 1050 |
| build_tower | No | 0.30 | 1050 |
| classify_objects_by_language | No | 0 | 1100 |
| fold_clothes | Yes | 1 | 300 |
| imitate_sorting_sequence | No | 0 | 638 |
| make_kong | No | 0 | 600 |
| classify_objects | No | 0.40 | 1100 |
| organize_table | No | 0.50 | 1000 |
| pack_objects_into_box | No | 0.10 | 1300 |
| put_bottles_into_dustbin | Yes | 1 | 493 |

All ten reached native terminal outcomes without controller errors: **2/10
successes, mean native score 0.345**, 8,631 actions, 578 policy calls, 87 fused
batches and 204 group prediction requests. Wall time including startup was
757.9503 s (12.63 minutes); no paid calls. Score is partial task completion,
not probability of success. Native binary-only tasks remain binary.

Retained actor-input hashes, prediction/task indexing, source-prefix equality,
emitted actions and terminal ACKs passed the independent offline audit. This
audit establishes record integrity, not full benchmark/hardware qualification
or source-singleton bitwise equivalence. Its `native_admission_pending` field
describes the scope of that audit, not a fresh qualification decision.

## Preservation

Full raw archive:
`runs/pi05-full-panel-baseline004-evidence.tar.gz`.
Remote and downloaded local SHA-256 matched:
`0e4f866312e78bc910661ff06d8368631df0787cca25fe9d12d6433f83a5e7d4`.
Extracted local evidence is in `runs/pi05-full-panel-baseline004/` and passed
`scripts/semantic/audit_full_panel_baseline.py`; local receipt is
`runs/pi05-full-panel-baseline004-local-audit.json`. Public audit copies are
retained beside this report. No model weights were copied to the Mac.

## Interpretation

Semantic001 also has two successes, but classification replaces bottles:
classification score 0.4 to 1, packing 0.10 to 0.25, folding stays successful,
table stays 0.5, and bottles is censored by planner abstention. Three semantic
scores are unavailable, so a full-panel semantic mean cannot be compared as a
point estimate. Baseline003's 3/10 and 0.44 are old-host historical evidence.
Same-host matching removes one confound, not rollout stochasticity/numerical
variation or the need for additional preselected layouts. There is no proven
hierarchy benefit or reliable loss from this pair.

See the [all-ten visual review](../pi05-semantic-visual-audit001-20261003/REPORT.md)
for instruction-following evidence and remaining uncertainty.

## Retained Visual Contrast

All ten original-only contact sheets were subsequently rendered and inspected
for the instruction-following comparison. The head and both wrist pixels are
real retained actor inputs, sampled at native H15 motor boundaries; derived
MP4s are not continuous physics recordings. The epoch renderer already
published with the subtask-only report was reused without modifying control or
making paid calls. `visual-index.json` lists the actual source steps; MP4s stay
local in `runs/pi05-baseline004-visual-audit001/`.

| Task | Contact Sheet |
|---|---|
| Number arrangement | [View](arrange_largest_number.jpg) |
| Tower | [View](build_tower.jpg) |
| Language classification | [View](classify_objects_by_language.jpg) |
| Folding | [View](fold_clothes.jpg) |
| Imitation | [View](imitate_sorting_sequence.jpg) |
| Kong | [View](make_kong.jpg) |
| Classification | [View](classify_objects.jpg) |
| Table organization | [View](organize_table.jpg) |
| Packing | [View](pack_objects_into_box.jpg) |
| Bottles | [View](put_bottles_into_dustbin.jpg) |

Classification's retained end view has a doll in red and pens in blue, unlike
the correct category placement in both semantic formats. Baseline packing also
starts with the shoe; the subtask-only car-request/shoe-action mismatch is
consistent with an existing routine continuing despite the changed prompt.
These contrasts are descriptive, not identical-state causal experiments.
