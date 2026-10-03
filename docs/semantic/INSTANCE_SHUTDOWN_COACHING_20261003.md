# GPU Instance Shutdown: Completed Coaching Screen

## Shutdown Boundary

Prepared 2026-10-03 at the owner's request. Project evidence is secured locally
and both GPUs are idle. No new experiments or paid calls were made during
shutdown preparation. No instance stop, deletion, reboot, system-setting change
or operation on unrelated CPU workloads was performed.

Repository: https://github.com/AranKomat/physical-execution-lab
Local root: `/Users/macbookpro/Developer/random/gpu/physical-execution-lab`
Remote root: `/root/physical-execution-lab`
Current endpoint: `ssh -p 53786 root@92.180.27.84`

Final remote check at 2026-10-03 13:59 UTC: both RTX 4090 GPUs had 0 MiB used,
0% utilization, driver 580.178.04. No owned experiment processes or reverse
relay listener on port 19861 remained. This is project readiness, not a backup
or clearance statement for the owner's unrelated workloads.

## Verified Local Evidence

All 23,166 inventoried files (12,456,533,349 bytes) under remote `runs/` and
`configs/local/` match local SHA-256 hashes: zero missing, zero changed.
The inventory excludes duplicate archives, Python caches, credential files and
the shutdown snapshot itself. It is not a full disk image or physics checkpoint.

Snapshot: `runs/instance-shutdown-20261003-coaching/` under the local root.

- `inventory.json`: remote paths, sizes and hashes.
- `coverage.json`: each remote file's verified local location. Most are under
  the same `runs/` path; historical configs remain under
  `runs/instance-shutdown-20261003/configs-local/`; new remote-only metadata is
  under this snapshot's `remote-only/`. Use the mapping rather than guessing.
- `backup-verification.json`: complete independent local verification receipt.
- `environment.json`: native package versions and source revision/status records.
- `source-backup.json` and `native-source-config.tar.gz`: 3,204 frozen native
  source/config files, 51,884,751 bytes uncompressed; archive hash verified.
- `additional-metadata.tar.gz`: 17 otherwise remote-only config/log records.
- `final-idle.json`: final remote process/GPU/tunnel check.

Native source archive SHA-256:
`de1344618ed4debb089b7ad1308aa31dfe508709cef7f12e7ff0108b454d2384`
Executor freeze:
`6844994a96df5c7282c278c558351eda5626bd96ff855a4bec8f45bd5c336933`
Inventory SHA-256:
`19dce5ae96c8e1a1c7fd3f15be9ea53c934b7e1b15c49f4ca0d4931e3e0fc3ff`

Older pi0.5 baseline003 evidence was restored from its existing verified local
archive; its later integrity audit was copied separately. Raw records, API wires,
private configurations and archives stay git-ignored. Only sanitized receipts
and reports are published. Credentials and the authoritative ledger remain on
the Mac. No model weights were downloaded locally.

## Latest Completed Comparison

Ten distinct RoboDojo tasks together, one method per cohort, frozen G0.5 B10
BF16/FM with H32 prediction/H16 execution at 25 Hz:

| Condition | Native Successes | Mean Native Score |
|---|---:|---:|
| Original-only baseline002 | 5/10 | 0.620 |
| Subtask-only/recovery001 | 3/10 | 0.380 |
| Original plus mistake-only coaching006 | 5/10 | 0.605 |

Coaching006 completed 8,238 audited actions and 78 planner decisions. Three
corrections were accepted, none visibly completed, and no failed task was rescued.
All five baseline-successful tasks succeeded without corrections. Prompt/token,
source-prefix and actual-ACK checks passed; independent local audit matched.
Wall time was 1,423.38 seconds including startup. No coaching benefit is
demonstrated. This is an opened one-attempt-per-task screen, not official whole-
benchmark SR, replicated causal steering or untouched-task generalization.

GPT-6.1 Sol/medium served 61 successful Flex calls and 17 same-model Standard
calls after explicit no-output Flex capacity rejection. Settled cost was
$0.57825750, with the $0.0701385 capacity hold retained. Latest ledger receipt:
5,771 shared reservations, $88.789483994300 charged including holds, $6.210516005700
remaining under the $95 ceiling. Re-read the ledger before new paid work.

Coaching003 remains Mac-sleep/transport-censored; 005 remains account-credit-
censored. Their partial scores are not complete SR denominators. Preserve all
holds and failed/setup records; do not merge or replay them. Full result details:
[fresh-run report](G05_COACHING_FRESH_RUN_20261003.md).

Retrospective diagnoses had terminal outcomes, future frames, full histories and
other runs that the online planner did not have. They are hypotheses, not proof
that the same model could detect those mistakes online. A fair detection study
must blind reviewers to future frames and outcomes; it has not been run.

## Restart And Remaining Work

1. Obtain a confirmed GPU endpoint before starting work. Read current STATUS,
   experiment progress and this report, not the earlier port-53210 shutdown plan.
2. Restore reviewed source/configs using the freeze and coverage map. Reacquire
   weights and simulator assets on the GPU host only; they and installed
   environments were not copied to the Mac. Reinstallation can take time.
3. Check driver, disk, GPU/process ownership, policy identity and native contracts.
   Environment receipts support reconstruction but do not replace qualification.
4. Check the local reservation ledger, retaining every unresolved hold. Use
   GPT-6.1 Sol/medium/Flex preferred; Standard only under the authorized explicit
   capacity fallback. Preserve the $3 cohort/$95 shared limits.
5. Do not automatically rerun the completed opened-panel comparisons. Reliable
   language steering, blinded online error detection, layout replication,
   untouched-task generalization and asynchronous execution remain research
   questions. Choose a discriminating test before spending more GPU/API time.
6. Start fresh named episodes; saved RGB/proprio and journals are not resumable
   full physics states. Keep failures and censored runs distinct.

The owner can stop this instance for our project. Deleting it would also discard
the unbacked installed runtimes, reacquirable model/assets caches and any unrelated
workload data. Those are outside this backup guarantee. Public source/reports are
on GitHub; full private evidence currently has a verified local Mac copy, not an
additional off-site backup.
