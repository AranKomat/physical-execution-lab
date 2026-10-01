# Pi0.5 Sparse Supervision Development Result

## Complete Native Outcome

One new trial on tower layout 0, the first lexically sorted case in the fixed
development roster. Exact pi0.5, original joint/camera conventions and native
1,050-action horizon; Sol 6.1 medium reasoning, Flex-only, at most 75 reviews,
$3 local cap under the $85 shared ceiling. No retry, fallback or model swap.

| Condition | Success | Score | Actions | Policy calls | GPT calls | Runner wall s |
|---|---|---|---|---|---|---|
| Earlier motor-only development case | Yes | 1.0 | 714 | 48 | 0 | 410.64 |
| New sparse supervision development case | No | 0.0 | 1050 | 93 | 27 | 807.82 |

The sparse episode reached the original native limit with **no infrastructure
or API error**. This is a full-horizon native failure, not a capacity/cost/call
budget stop. It is the project's first complete supervised physical episode,
but not a completed three-condition or held-out experiment.

All 27 requests settled, served `openai/gpt-6.1-sol`/`flex`, actual cost
**$0.25800075**. Reported tokens: 177,477 input, 7,401 output including 1,511
reasoning; zero cached input. Review blocking: 229.35 s, about 28.4% of runner
wall time. Native environment work: 384.52 s; observation ACK transport: 105.77 s;
policy blocking: 51.72 s; setup: 24.90 s. This is not an isolated API-latency test.

## What Happened

Sol made one accept decision, 21 shorten decisions and **five separate
one-action corrections**, at native steps 926/939/985/1004/1038. There were
1,045 motor actions and five corrected actions, 14 local monitor interruptions,
and zero unresolved policy actions. The 88 shortened-chunk metric also includes
normal H50/15 source-prefix discards; it is not 88 GPT interventions.

The supervision loop and correction routing actually executed, but the task
did not succeed. Do not label those corrections successful recovery or infer
that a completed software pathway establishes manipulation competence.

The same case, environment contract, policy identity and package fingerprints
match the earlier motor row. Initial robot-state arrays are identical. Initial
RGB is not byte-identical: per-camera mean absolute differences are
0.384/0.293/0.307 on a 0-255 scale. The earlier row ran alongside another worker;
the new row ran alone. Wall caps differ (3600 versus 2400 s), neither binding.
This is a nominally matched development comparison, not an exact physics replay
or a causal proof from one deterministic trajectory.

Frequent shortening changes policy resampling times and advances the JAX RNG
through more proposals. That is a plausible disruption mechanism, not an
established explanation. This result supplies evidence against assuming that
more semantic supervision necessarily helps an already capable motor policy.
Retain the failure; do not rewrite a tower-specific recipe or repeat until a win.

## Verification And Next Step

Offline audit verifies evaluator/controller agreement, nonvacuous completion,
all 1,050 contiguous ACKs, source indices 0..92 and proposal accounting:
4,650 proposed = 1,045 motor actions + 3,605 discarded. Every source NPZ action
array matches its journal proposal. Raw clipping magnitudes remain unreported
in client diagnostics, not assumed zero. Small records:
`docs/evidence/pi05-sparse-sol-flex-dev-001/`. Full API audits remain private.
The complete native episode, prepared configs and matching source NPZ session
are retained in `runs/native-evidence/pi05-sparse-sol-flex-dev-001-backup.tar.gz`.
All 2,812 file payloads match the remote hashes. Tar reported a directory-mtime
change while a derived initial-observation report was added; verification found
no missing or changed payload. The warning remains in the public backup record.

Stage A motor-only qualification/freezes and Stage B screens are complete for
active scope. Stage C now has a real negative sparse result, not just route
checks; every-chunk, matched held-out conditions and direct dense/sparse remain
unfinished. Next use the predefined conditions, not another baseline screen.
Budget snapshot: 4,564 reservations, $76.192461494300 spent plus holds,
$8.807538505700 remaining. The three earlier Sol holds remain charged;
this trial introduces no unresolved request. Model/simulator/relay/tunnel are
stopped. The unrelated host workload was not stopped or reconfigured.
