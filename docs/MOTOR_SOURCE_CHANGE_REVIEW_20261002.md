# Motor Qualification Source-Change Review

This is a source/evidence carry-forward review, not another native task run,
hardware safety certificate, supervision qualification or performance result.
Original development labels and older qualification/freeze files stay unchanged.

## G0.5 Wrapper Change

The earlier G0.5 motor qualification references `xpolicylab.py` hash
`f3076a9e2dbe08352791dea4236595670b7d53d083038e1e26f095fee0624acb`.
Commit `a3d4421` added opt-in two-GPU Intern placement, producing current hash
`5c052a5d0f0efefb45a548ccc65525eb631d0de5b98ba23bc10bbba8b74ad54c`.
The old record consequently cannot pass byte verification unchanged.

Reviewed diff: `git show a3d4421 -- k1lab/multibench/adapters/xpolicylab.py`.
For the exact G0.5 provider, `intern_component_placement` is absent:

- Construction still calls the original source `module.Model(cfg)`.
- Synchronization still calls the original default-device CUDA synchronize.
- Memory reporting still uses the original default-device counters.
- Observation packing, seeding, actions, clipping, ACKs, reset and invalidation
  are unchanged. No Intern loader hook executes on this branch.

The new record must verify the actual provider lacks that optional field,
rehash artifacts/ancillary configuration, and verify all unchanged native
evidence files before carrying forward checks. It replaces only the source
hash reference and adds this explicit review. It does not fabricate a fresh
G0.5 episode or re-score the five-case screen. Keep the old record historical.

## Other Changes And Lanes

The EEF quaternion-formatting fix affects model corrections, not motor-only
joint actions. It does not qualify corrections by inference. Reporting changes
only expose outcome status/reason counts; they do not alter control.

Pi0.5 and official XR1 qualifications must still pass their exact evidence and
resolved-config checks, rather than inherit G0.5's review. Intern uses its own
two-GPU motor-only qualification with actual native pilot evidence.

After these checks, generate fresh source/config/full-manifest freezes for
each exact motor binding. No held-out episode may be authorized merely by
this prose. A freeze is integrity/preregistration, not a competence result.
