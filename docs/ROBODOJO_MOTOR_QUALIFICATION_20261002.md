# RoboDojo Motor-Only Qualification

Evidence reviewed 2026-10-02 for G0.5's seeded BF16/FLA/clip variant and exact
pi0.5 OpenPI/JAX. This is a software-contract qualification of the two specified
motor-only bindings, not proof of safe hardware operation, published-score
reproduction, GPT correction competence or a harness gain. Original native
results remain `native_unqualified` and development; they are not rewritten.

## Reviewed Checks

| Check | Evidence And Scope |
|---|---|
| Reset/render | Each policy completed the fixed five-case development screen with three real camera streams and robot measurements. Initial and decision-boundary sensor captures are retained in verified local backups. |
| Action convention | Both use native joint14: left six arm joints/opening, then right six/opening. `RoboDojoRPC.step` sends one joint action to source `chunk_step`, without EEF conversion. G0.5 explicitly clips its predicted grippers; pi0.5 retains the source continuous-opening clip. No binary-gripper substitution. |
| Completion | Native evaluator registration is nonvacuous and agrees with controller success/score/steps. Both successes and full-limit failures are retained. No scoring query selects control actions. |
| Legal inputs | `to_xpl` selects only three RGB cameras, robot joints/opening, robot-only EEF poses and instruction. Pi0.5's source client selects images/state/prompt only. Hidden object poses, task scores and other episodes are not policy arguments. There is no GPT actor in these bindings. |
| Actual ACKs | All 4,459 G0.5 and 4,292 pi0.5 control ACKs are contiguous and exactly once. G0.5 receives actual observations and rejects pending-step gaps. Its source history is assembled at prediction boundaries; receipt of every ACK is not a claim that every native frame enters that history. Pi0.5 is sensory-stateless; fresh source identity and inference indices verify seed provenance. |
| Native timing | Both execute actual actions at 25 Hz. G0.5's policy frequency remains explicitly 30; this labeled runtime variant is not silently retimed. Pi0.5 executes a 15-action prefix of H50 predictions. Wall time is not a real-time guarantee. |

Pinned GPT-as-Policy revision: `8f3d362b077d8efb77e2a7274d5b2c20e2243846`;
XPolicyLab revision: `408b99d959a7b2207f5f785528fefcc019d7b131`;
RoboDojo root revision: `ee67a1468510da7624a089164402359f2afc72c8`.
The first two consumed policy/server checkouts have no tracked modifications.
RoboDojo's XPolicyLab and cuRobo submodule pointers differ from its root pin;
this deployed runtime is not claimed to be a pristine recursive upstream tree.
The harness separately pins consumed XPolicyLab/GPT-as-Policy sources; the
qualified lane sends native joints, not a cuRobo-generated grasp/trajectory.
Dependency fingerprints are retained, not a universal binary/runtime lock.

## Exact Bindings

G0.5 binds `g05-fla-seed0-ancillary-bound-004`, including actual
`external/env_cfg/` alias-file hashes. Its resolved motor-only config digest is
`8435f0509f047bbf9794fc9c6f859fa3eb40bc75db8f30598d8a9e8afa3b0d05`.
The earlier screen configurations did not include the same ancillary hash
metadata. Source inspection previously established that their resolved robot
dimensions and single-observation inference configuration are unchanged; the
new checks bind those files without changing model inputs, weights or control.
This retrospective review does not assert historical config hashes were equal.

Pi0.5 binds `pi05-exact-bound-001`; its resolved motor-only config digest is
`af24908a77cde16230bd25e26e46ef37d17742ec53ff806a0b8cdfb0d7b112f8`.
The second worker differs in operational ports/recording paths; it does not
automatically inherit this exact configuration's qualification record.

Machine-readable records reside in `docs/evidence/robodojo-motor-qualification/`.
They reference hashed native results/audits and reviewed adapter source. Live
artifact rehashing is required when resolving/finally freezing the binding.

## Remaining Gate

Only motor-only is qualified here. Basic EEF translation/hold development
evidence does not qualify object contact, rotation, grasping, policy interruption
and resumption, or a complete supervised episode. Develop those paths through
the bounded matched pilot rather than more standalone microdiagnostics.

Freeze the reviewed motor-only configurations and the unchanged source before
opening untouched held-out cases. Freeze metadata alone does not qualify the
every-chunk/sparse or robot-policy-free configurations. Preserve the Flex-only
route, $85 ceiling and failed-request holds. Full Stage C/D comparisons remain
unfinished; neither qualification nor more component tests supplies that result.
