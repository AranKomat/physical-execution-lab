# Instance Shutdown Handoff

## Current Boundary

Owner requested shutdown preparation on2026-10-03. No further GPU or paid
experiments should start under this request. The agent stopped only its own
numeric-panel parent and child processes, not the rental or unrelated workloads.
The owner may stop the rental after independent backup verification completes.
Stopping is not permission to destroy the volume. Historical raw runs not
listed below still depend on the retained instance disk.

Repository: https://github.com/AranKomat/physical-execution-lab
Local checkout: `/Users/macbookpro/Developer/random/gpu/physical-execution-lab`
Remote checkout: `/root/physical-execution-lab`
Current endpoint: `ssh -p53210 root@92.180.27.84`
No checkpoints were downloaded to Mac during this preparation.

## Latest Experiments

Original-only baseline003 is complete: ten concurrent distinct tasks,3/10
native successes, mean normalized score0.44,8,497 actions,12.52minutes,
zero paid calls. Local full backup archive remains
`runs/pi05-full-panel-baseline003-evidence.tar.gz` with SHA256
`aaf1d2d4a8821f9a6bbe90ebaf375b85d2db7b9a0b9eeffe4d58ea2782b448d2`.

Direct001 and002 are retained censored runs, not0/10 physical successes.
Direct002 performed468 actions and cost$1.38820125 settled, plus$0.174813
unresolved holds. Standard fallback worked. Contract violations and a separate
OpenRouter admission-control429 prevented valid full-panel scoring.
Its full1,066-file backup was verified before the numeric trial; public report:
`docs/evidence/pi05-full-panel-direct002-20261003/REPORT.md`.

Numeric001 stopped at the3GiB disk preflight, before API or simulator actions.
Old regenerable texture cache, not records/weights, was cleared. Numeric002
then ran the whole panel concurrently using one fused pi0.5 runtime and Sol6.1
medium, Flex preferred with authorized same-model standard fallback.
All ten reset/FK admission gates passed. The owner interrupted it after
3,986 recorded commands, at parent wall1,200.66seconds including shutdown
cleanup. Retain the raw parent `KeyboardInterrupt` report and separate
`operator-interruption.json`; do not infer completed outcomes from process exit.

| Task | Retained Outcome | Actions | Native Score |
|---|---|---:|---:|
| fold_clothes |Native success|297|1.0|
| make_kong |Native failure|600|0.0|
| imitate_sorting_sequence |Native failure|636|0.0|
| organize_table |Model stopped incomplete|158|Unavailable|
| Other six fixed tasks |Owner-interrupted|Partial|Unavailable|

No full-cohort SR or mean score is available. Do not extrapolate1/3 native
terminal successes to the panel: the completed subset is duration-selected.
Numeric002 reserved82 requests, settled81 for$1.478102, and retains the
Flex-capacity hold `pi05-full-panel-numeric002-0` at$0.053577. No shutdown-time
provider reservation remains unresolved besides that known hold.
Shared charged total including all historical holds: $82.102604244300 against
the$85 ceiling at final local ledger inspection. Re-read it before new work.

## Independent Local Backups

- `runs/pi05-full-panel-numeric002/`: complete stopped run, sensor inputs,
  action journals, worker records, operator interruption and native results.
- `runs/pi05-full-panel-numeric002_api/`: local provider wire records;
  launcher/relay logs remain locally. Tokens are removed.
- `runs/reference-pi05-2-005/`: retained indexed controller evidence.
- `runs/pi05-approach-standard-fallback-preparation001/`: unchanged four-method
  panel/configs and plan.
- `runs/instance-shutdown-20261003/configs-local/`: remote local configurations
  and bound qualification artifacts; keep private, not public source.
- `runs/instance-shutdown-20261003/`: current executor and native-reference
  freezes. The current screen freeze is
  `0835c4793176826acb286cea49bf7fc6b908becbe3f7967121ef3700b59da38c`.

Backup verification completed: all3,224 numeric-run files,87 controller files,
six preparation files,676 local-config/artifact files and1,066 direct-run files
match the remote copies. Both copied freeze files also match. The baseline
archive hash was rechecked against the previously verified value above.
Numeric journal audit passed for all ten rows and3,986 contiguous ACKs;
there are zero recorded commands without a matching ACK. No claim is made that
partial journals are a resumable full physics checkpoint.
Verification: `runs/instance-shutdown-20261003/backup-verification.json` and
`numeric-partial-control-audit.json`; sanitized copies are public in
`docs/evidence/pi05-full-panel-numeric002-20261003/`.
These raw backups are git-ignored; do not publish API wires or private local
configs. Public source, reports and checklist changes are committed/pushed.

## Restart Sequence

1. Confirm owner wants new GPU work and verify the instance endpoint.
2. Restore only needed source/config/evidence; obtain weights on the GPU host,
   never the Mac. Check disk, driver and idle GPUs without altering other work.
3. Check the shared ledger and keep every unresolved hold. Flex capacity may
   fall back to the same Sol6.1 model on standard; generic retries remain off.
4. Preserve numeric002 as owner-interrupted. A fresh full-ten numeric run needs
   a new name; do not pretend its six live physics states can be resumed from
   RGB/proprio alone. No lossless simulator checkpoint was made.
5. Run numeric to completion, then semantic task-plus-subtask on all ten tasks,
   one method at a time with shared batched inference. Semantic is still unrun.
6. Retain all outcomes and scores, then preselect additional matched layouts
   for promising methods. Do not treat this one-layout screen as whole RoboDojo.
7. Direct-interface changes, if tested, need separately named frozen generic
   ablations; never replace the retained failed direct conditions silently.

Broader V5 shadow/context-switch/recovery and held-out/backend requirements
remain in the original handoff. CPU tests and source hashes do not complete
those research phases.
