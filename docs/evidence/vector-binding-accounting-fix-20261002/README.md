# Response Binding And Error Accounting Revision

This is a new source version after the completed recovery condition; it does
not modify or rerun the retained trial. No native episode or paid API call was
made to produce this correction evidence.

`semantic_lab/planner.py` now constrains episode, observation step, observation
SHA and semantic epoch to their exact request values in the tool schema. SHA
length is additionally constrained to64. Existing response parsing/state
validation remains authoritative: an invalid response is rejected, never
silently repaired or retried. Schema constraints do not prove provider
compliance; tests deliberately return an invalid response despite the schema
and verify rejection without planner-history or state mutation.

`semantic_lab/report.py::summarize_wave_results` accounts for every resolved
row, including planner contract errors, and preserves paid-call counts. The
revised experimental native adapter uses it instead of asserting that every
row is free of contract errors. Incomplete waves retain the error result;
they do not become native terminal successes. The revised supervisor aggregates
wave call counts before validating wave status. These are `002` operators;
all `001` source copies and old evidence remain unchanged.

CPU verification:379 repository tests passed, including the77 semantic tests.
The three revised experimental operators compile. This is software verification,
not native language-following, recovery, or held-out qualification. Old frozen
source bindings must not be reused for these changes; bind a new condition
before execution. The broader ten-task/fifty-case reference roster still needs
source-faithful vector admission and missing matched motor baselines.

No model weights were downloaded locally. GPU host confirmed idle before work;
no unrelated workload was interrupted.
