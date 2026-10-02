# Pi0.5 Every-Chunk Review: Budget-Censored Result

## Result

Fresh development run `pi05-every-chunk-sol-flex-dev-002` stopped at its
predeclared 75-review limit, not at native task termination. It executed
658 actions with no API or contract error. Original result remains
`status=incomplete`, `termination=review_budget`, native score null.
This is not a full-horizon physical failure, success, or completed held-out
three-condition comparison. No automatic retry or tier fallback occurred.

| Condition, same nominal tower0 development case | Outcome | Actions | Policy calls | GPT calls | Wall s |
|---|---|---:|---:|---:|---:|
| Earlier motor-only pi0.5 | Native success, score 1.0 | 714 | 48 | 0 | 410.64 |
| Sparse Sol Flex 001 | Full-horizon failure, score 0.0 | 1050 | 93 | 27 | 807.82 |
| Every-chunk 001 | Quaternion contract error; native score null | 626 | 69 | 69 | 909.28 |
| Every-chunk 002 | Review-budget stop; native score null | 658 | 76 | 75 | 1191.61 |

These are nominal development comparisons, not exact physics replay or a
strong causal estimate. Initial observation fingerprints differ; Sol responses
are not assumed deterministic. The older attempt is retained unchanged, not
replaced by this run or pooled into a single result.

## Protocol And Audits

Executed code: `773b5d0`. Same released pi0.5, provider identity, sensor/control
conventions, tower0 source seed and original 1050-action horizon as the prior
every-chunk trial. New run retains 75 reviews, $3 local cap, 2400-second wall
limit, shared $85 ceiling, Sol 6.1 medium/Flex-only, and no retry/fallback.
The software change is bounded EEF quaternion representation normalization;
translation, rotation, takeover and strict Action gates remain unchanged.

All **75 API requests settled**, serving `openai/gpt-6.1-sol`/Flex, for
**$0.71236500**. Token totals: 499,526 input, 18,064 output, including 1,972
reasoning tokens; cached input zero. No new unsettled hold was introduced.

All 658 actions were motor actions, with zero corrections or monitor
interruptions. Review decisions: **three accept, 72 shorten**. The metric
`shortened_chunks=75` includes the normal H50-to-15 executable-prefix discard;
it is not 75 semantic shorten decisions.

The terminal audit verifies all 658 contiguous ACKs, source inference indices
0..75, and all 76 source NPZ action arrays matching the journal. Accounting:
3800 proposed = 658 executed + 3092 discarded + 50 unresolved.
The runner requested a final policy proposal before checking its review budget;
those 50 unresolved actions were not executed and are not relabeled discarded.
The audit is bookkeeping/provenance evidence, not native completion approval.

No correction was requested in this run. Therefore it **does not test live
quaternion normalization**, although the retained rejected response passes the
offline check documented in [the correction fix](CORRECTION_QUATERNION_FIX_20261002.md).
Absence of the old error here does not by itself prove that fix under execution.

## Time And Interpretation

| Runner component | Seconds |
|---|---:|
| GPT review waiting | 795.14 |
| Environment | 249.07 |
| ACK transport | 65.77 |
| Policy inference | 44.82 |
| Setup | 25.17 |
| Robot-only preview | 2.39 |

GPT waiting accounts for about 67% of runner wall time. Simulation advances
only during actual control, not model waiting. This is not real-time control.

Average executed prefix was about 8.77 actions across 75 reviewed segments,
below the 15-action executable maximum. The cap could theoretically permit
1125 actions, but actual shortening exhausted it at 658. This is a concrete
resource/behavior trade-off: the every-chunk condition did not establish useful
completion under its declared budget, despite more review cost/time than the
nominal successful motor-only baseline. Do not convert censorship into a
verified native failure or claim that all supervision is harmful.

Frequent shortening alters resampling times and RNG progression. That is a
plausible disruption mechanism, not a demonstrated cause of task behavior.
Do not tune a tower recipe, force accepts, silently extend the live budget,
or rerun until a favorable outcome appears.

## Evidence And Next Gate

Small public evidence: `docs/evidence/pi05-every-chunk-sol-flex-dev-002/`.
Full terminal backup: `runs/native-evidence/pi05-every-chunk-sol-flex-dev-002/`.
All 2,101 payloads match the terminal remote per-file checksums, with zero
missing/changed files. Source NPZ proposals and token-free bound configs are
included; raw API audits remain private on the Mac, not published to Git.
Shared ledger after settlement: 4708 reservations, $77.561067994300 spent plus
holds, $7.438932005700 remaining; 154 older unsettled reservations retained.
All owned model/simulator/relay/tunnel workers exited; both GPUs report zero
memory usage. The unrelated CPU workload was not restarted or changed.

Next: retain this censored outcome in the development comparison, refresh
current-source freezes, and move to the predefined remaining cases/direct
conditions rather than repeat tower0 until it wins. Intern's four remaining
fixed-roster cases are prepared and use zero paid calls, but need both GPUs.
Matched held-out supervision, robot-policy-free dense/sparse and XR1 matched
supervision remain unfinished. Direct dense's original 180-by-5 call budget
cannot reach the 1050/1100 horizons; explicitly distinguish a resource-limited
comparison from any separately authorized full-horizon profile.
