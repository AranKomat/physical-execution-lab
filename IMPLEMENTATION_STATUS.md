# Implementation status — PDF-grounded revision 2

## Evidence boundary

The complete 37-page DynaHarness PDF was reviewed. All new code below is implemented and CPU-tested where noted. **Native LIBERO episodes: 0. Learned-policy inference: 0. Paid LLM requests: 0. Real-robot actions: 0.** A native result comparable to the paper has not been measured.

The source-audit findings and native requirements are not replaced by an “exact reproduction” badge. The current deliverable is a substantially closer mechanism/protocol reconstruction for the external GPU agent to qualify.

| Area | Implemented | Validation / remaining work |
|---|---|---|
| PDF protocol | Per-suite budgets, 20/2/50 Hz declarations, model family, temperature/token/timeout/validity settings, source result blocks | CPU assertions; exact original sampler/versions/prompt absent |
| Symbolic planning | Single-step/sequence output schemas; no numeric poses; one serialization repair; snapshot/epoch/age checks | CPU/mock transport tests; actual Qwen output not exercised |
| Privileged geometry | Direct MuJoCo object/region/articulation/contact extraction, with provenance | Math/mock seam tests; native asset/site/joint mappings unqualified |
| Analytic pick/place | Approach/descent/jaw/lift; actual-contact + object-motion verification; object-to-TCP transport; climb/corridor; slots; release/local check | Kinematic fixture only; native grasping/clearance/tolerances need testing |
| Articulated skills | Drawer slide, knob/handle rotation, door arc; explicit shift/ramp/reseat hook | CPU geometry tests; original full controllers and thresholds not supplied |
| Insertion | Staged cavity placement with height/slot validation | Not a qualified connector/contact-search controller |
| Executed controls | A2static fixed retries; A2seq frozen plan; A2ctrl refusal/substitution/replan/reseat | CPU decision/counter tests and trace audits; exact original scheduler remains partly reconstructed |
| Completion and budgets | Per-action native Boolean sampling; independent latch; leases; affordability; one total action budget | Synthetic pulse and interruption tests; native callback timing still to qualify |
| Native policy service | RPent ten-action chunk override; model byte-manifest and live attestation checks | Manifest tests; no GPU model load |
| Safety seam | 50 Hz physics-substep hook; measured qdot; partial-action uncertainty handling | Mock callback cadence; not native- or hardware-qualified |
| Evaluation | Paired manifests, full denominator, failure/missing rows, cell bootstrap, exact discordant test, protocol/source hashes | CPU regression and example pipeline; no source-paper benchmark result |
| Evolution | Cell-count Eq5 gate, targeted + broader admission, explicit reconstructed diagnostic labels | CPU gates; no autonomous skill-evolution campaign |
| K1 | Legacy selected geometry bridge remains | Deliberately not part of the privileged reproduction; full sensor replacement later |
| Failure replay | Physics-only archive with missing-state warning | Complete controller/RNG/governor resume not implemented |

## Tested during this build

See `validation.json` and `docs/CPU_TEST_OUTPUT.txt` for the final exact count. The suite contains the original 125 tests plus paper-protocol, analytic-geometry, executor, admission, native-math/mock and policy-manifest tests.

The packaged examples process four synthetic fixtures under five arms. They show accounting and execution differences; they are not a claimed robotics gain. A2static/A2ctrl can tie. This is intentional: no toy success margin was engineered to resemble the paper.

## Native-critical work remaining

1. Fetch/install the pinned ecosystem; verify checkpoint identity, normalization, ten-action chunks and Qwen serving.
2. Inspect current physical geometry, handle/site bindings, joint endpoints, camera conventions and OSC scaling. Validate the substep hook.
3. Make the first actual analytic grasp/lift/place complete; then qualify two-object slots, relational placement and articulated skills.
4. Freeze and run matched bare/nominal/dynamic conditions on balanced predeclared states. Do not substitute an API success message for native completion.
5. Extend the library from concrete failed states; obtain the authors' supplement or release where possible.
6. Only afterward add K1 sensor grounding, stronger planners, harder benchmarks and self-evolution.

No full upstream clone or model asset is included. The GitHub connector supplied selected source reads; direct network checkout/download was unavailable. The authoritative study source is the PDF included in `references/`.
