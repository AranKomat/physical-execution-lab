# Generic Correction Quaternion Formatting Fix

The prior every-chunk development trial stopped at native step 626 because
the model's right EEF quaternion norm was 1.013110, outside `Action`'s 1% unit
contract. Its left norm was 1.000056. The response, contract-error result and
full trace remain unchanged; the stopped episode was not retried.

The actor decoder now converts finite EEF quaternion vectors with at most 5%
norm error to unit length **before** constructing the strict `Action`. This
changes only representation scale, not the represented rotation. Zero vectors,
nonfinite/nonnumeric inputs and gross norm errors still fail. `Action` retains
its original unit guard; no gripper clipping or general target repair was added.

The 5 cm translation bound, 0.35 rad rotation bound, takeover evidence gate,
correction horizon and original prompts/schema remain unchanged. Original model
wire values remain archived and normalized actions are recorded by the existing
journal. This is a generic decoder version change, not a tower-specific policy
or an improvement to the motor model.

Offline decoding of the exact retained response at step 626 now passes all those
unchanged geometric bounds. No paid call, simulator reset, robot action or
rewritten result was involved. Evidence:
`docs/evidence/pi05-every-chunk-sol-flex-dev-001/quaternion-offline-check.json`.
CPU suite: 295 tests passed, including malformed quaternion rejection and
unchanged translation/rotation rejection after normalization. These checks
do not complete Stage C or prove recovery/task success.

Source changes invalidate previous code freezes. Generate and verify fresh
freezes before scored comparisons; retain historical freezes as historical
records. A new named development every-chunk trial can test the corrected
decoder later, with its new version and limits labeled, rather than resuming
or hiding the original contract-error episode.
