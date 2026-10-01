# Pi0.5 Five-Case Development Screen

## Complete Physical Results

The roster is the same predefined five development cases used for G0.5:
sorting layouts 0/1/2 and tower layouts 0/1, all source seed 0. Sorting layout 0
is the previously completed pilot, not a repeated or replacement episode.

| Case | Success | Score | Actions / limit | Policy calls | Runner wall s |
|---|---|---|---|---|---|
| Sorting layout 0 | Yes | 1.0 | 994 / 1100 | 67 | 546.40 |
| Tower layout 0 | Yes | 1.0 | 714 / 1050 | 48 | 410.64 |
| Sorting layout 1 | Yes | 1.0 | 755 / 1100 | 51 | 419.40 |
| Tower layout 1 | Yes | 1.0 | 729 / 1050 | 49 | 412.50 |
| Sorting layout 2 | No | 0.0 | 1100 / 1100 | 74 | 599.14 |

**4/5 successes**, mean native score 0.8, task-weighted success 83.3%.
Totals: 4,292 actual actions, 289 policy calls, zero GPT/API calls and zero
corrections. Mean runner wall time: 477.61 s. Sorting layout 2 reached its
original full native limit; no retry, task-specific repair or replacement case.

G0.5 completed 3/5 with mean score 0.68. Pi0.5's additional success is sorting
layout 1 (G0.5 score 0.4, pi0.5 score 1.0). Both solve both tower layouts; both
fail sorting layout 2 with score 0.0. These are related development layouts,
not held-out generalization, published-score reproduction or a harness-only
ablation. Same case/seed does not imply byte-identical camera images across
resets. Keep both policies; do not expand this screen to seek a preferred winner.

## Runtime And Integrity

Exact publisher-verified checkpoint, pinned OpenPI/JAX runtime, native joint14
actions at 25 Hz, H50 predictions and a 15-action execution prefix. Original
continuous gripper clipping is retained. Source JAX RNG starts at seed 0 in
each fresh episode server and advances with inference; stateless sensory
context does not mean resetting the RNG before every proposal.

The four new episodes ran in two isolated workers, each colocating its own
policy and simulator on one GPU. Observed memory was about 15.2-15.5 GB per
device, not a continuous peak measurement. Concurrent wall times include
shared CPU/I/O activity and are not isolated model-latency measurements.

The two bound provider identities differ because ports/recording paths differ:
`78de83adc06eae60af453f72fd026f40de9c3eef3a214bf528770f51abd321c2`
and `60b502ee4857775e4fe84bc03301eab7d35204cd2e0a9d8ba87848349ec671e1`.
Weights, preprocessing and control settings are unchanged. Do not claim the
complete provider hashes are identical.

Offline audits verify hash-chained journals, exactly contiguous ACKs,
controller/evaluator agreement, nonvacuous completion, H50 proposal accounting
and contiguous source inference indices starting at zero. The generic audit
initially rejected pi0.5 because its seed is recorded in source-server metadata,
not in each proposal. The explicit pi0.5 audit path checks the fresh source
identity and bound checkpoint instead; historical journals were not rewritten.
Per-proposal clipping magnitudes are unavailable in its diagnostic metadata
and are reported as null, not zero. Raw predictions remain in source NPZs.
Suffix-discard/invalidation counters describe H50/15 prefix bookkeeping, not
GPT interventions or recurrent sensory-memory resets.

Small public evidence: [results and aggregates](evidence/pi05-development-screen/report/aggregates.json).
Sorting layout 0's result/audit remain under `evidence/pi05-native-pilot/`.
All four new episodes, both bound provider roots with raw proposal NPZs, and
the timing session/input are locally retained in three streamed archives under
`runs/native-evidence/`. All 8,170 file entries match terminal remote hashes,
with no missing files or mismatches; see
[backup verification](evidence/pi05-development-screen/backup-verification.json).
The original sorting-layout-0 pilot has its earlier separately verified backup.
These audits establish bookkeeping/provenance, not automatic physical safety
or independent visual scoring. All results remain development and retain their
original `native_unqualified` labels; formal qualification/freeze is separate.

## Matched Recorded-Input Timing

Same `capture-005/observation.wire.json` and observation-corpus hash as the
G0.5 test, three warmups and 30 measured proposals through the loopback bridge.
Both simulators were terminal; backup I/O overlapped both policies' recorded
timing sessions. Pi0.5 used a fresh seed-0 source server. Its RNG advances
between independent inputs, while its sensory context is stateless; no new
server is created per sample. This is not a steady-state physical rollout.

| Policy | p50 ms | p90 ms | p99 ms | Mean ms | Exposed actions |
|---|---|---|---|---|---|
| G0.5 | 800.99 | 841.25 | 888.68 | 803.90 | 16 |
| Pi0.5 | 453.92 | 488.25 | 523.19 | 454.00 | 15 |

Pi0.5's median proposal latency is about 43% lower on this input/hardware.
This does not establish the same gain in native episode speed or unseen-input
performance. The source generates H50 even though only 15 actions are exposed.
The timing JSON's `cold_load_seconds=0.2134` measures bridge construction after
the JAX source is already loaded, NOT complete model cold startup; do not
compare it to G0.5's model-load duration. JAX memory peaks are not collected by
the client. Source-launch commands/logs are retained in the local timing backup.
Reproduction command: `scripts/multibench/run_pi05_latency.py`, with the exact
bound provider and saved observation. No physics or paid API calls.

## Next Gate

The predefined quality screen, matched warm timing and local backups are
complete. Qualify and freeze retained policy bindings before
held-out comparisons. Stage C
still needs complete motor-only/every-chunk/sparse and robot-policy-free
dense/sparse comparisons. Stage D still needs matched XR1 supervision.
The shared paid ledger retains all unresolved Flex holds; no tier fallback,
automatic retry or paid call occurred during this screen.
