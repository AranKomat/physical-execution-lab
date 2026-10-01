# EEF Controller Development Check

This closes the basic translation/hold bring-up gate for the shared RoboDojo
correction path. It is not a completed Stage C comparison, task solution,
contact/grasp qualification, or real-robot safety certificate.

## Native Evidence

One fresh tower-layout-0 development episode used the pinned donor DLS and only
measured robot poses to choose targets. Both arms kept their measured orientation
and fully open gripper command. Targets: hold for 5 actions, raise the left link6
20 mm for 25 actions, raise the right link6 20 mm for 25 actions, then return both
to their initial measured poses for 25 actions. Total: **80 actual sequential
native ACKs**, **zero policy inference or paid requests**. All four endpoints
passed the existing 3 mm / 0.035 rad arrival check without changing its limits.

At five actions into each translation phase, the largest translation residual
was 0.1501 mm. Therefore this probe does not support increasing the existing
five-action correction horizon. Full-phase endpoint errors are idealized
simulator measurements, not estimates of physical robot accuracy.

No hidden object coordinates, scoring feedback, contact predictions, or task
recipe selected these targets. External clearance remained explicitly unknown;
this was simulator-only exploratory motion at the reset arm poses. Closure,
rotation changes, object contact, policy interruption/restart during a live
correction, and general reachable-workspace behavior are not demonstrated here.

Complete traces, native recordings and before/after RGB/proprio captures:
`runs/native-evidence/eef-controller-probe-002/`. Small public endpoint evidence:
`docs/evidence/eef-controller-probe/result.json`.

The first command failed before creating an episode because the donor path
resolved from the SSH working directory. Supplying its absolute path fixed
that configuration issue. The next launch (`eef-controller-probe-001`) stopped
before any action because the previously used Isaac EULA environment flag was
missing. The successful launch explicitly restored `OMNI_KIT_ACCEPT_EULA=YES`.
These startup failures are retained; neither is counted as a task/policy failure.

## Next Experiment

Proceed to a bounded G0.5 supervision development pilot, using the same seeded
FLA provider and sensors for motor-only/every-chunk/sparse conditions. Formal
held-out freezes and full qualification records remain pending. Do not add more
translation probes merely to accumulate passing component tests.

Provider preparation `ancillary-bound-004` guards the actual
`external/env_cfg/` aliases. Earlier `-002` and `-003` preparations are historical
copies with resolved-target paths and must not authorize formal comparisons.

The existing private shared ledger was inspected read-only: 4,532 reservations,
$75.750305744300 spent-plus-held, 151 unsettled reservations, and
$9.249694255700 remaining under the approved $85 ceiling. All holds remain intact.
The existing provider advertises `openai/gpt-6.1-sol` on `openai/flex`, including
tools and medium reasoning. No paid request was made. A local budget-enforced
Responses bridge still needs binding before paid supervision; neither provider
availability nor this controller probe completes that gate.
