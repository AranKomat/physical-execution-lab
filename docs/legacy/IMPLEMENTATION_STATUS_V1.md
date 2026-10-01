# Implementation status — delivered October 1, 2026

## Evidence boundary

**Implemented and CPU-tested is not the same as natively qualified.** The build
host has Python 3.13.5, pytest, NumPy and Pillow, but no installed RPent/K1/MuJoCo,
no usable NVIDIA GPU, no model credentials, and no direct outbound DNS/download
path. GitHub source was read through the connector; repositories were not cloned.

## Local verification

**125 CPU tests passed** under Python 3.13.5. Three synthetic conditions each
completed four fixture cases (12 total). The included journals and reports are
under `examples/cpu_evidence/`. Native episodes: 0; live model calls: 0.
`validation.json` and `docs/CPU_TEST_OUTPUT.txt` record this scope. CI is configured
for additional Python versions but was not run on hosted GitHub Actions here.

## Component matrix

| Component | Delivery state | What remains |
|---|---|---|
| Typed proposals/targets/receipts | CPU tested | Tune validation only from real interface evidence |
| Per-step shared execution guards | CPU tested with deterministic fixtures | Qualify native step and termination semantics |
| Dynamic Cartesian stagnation | CPU tested | Native thresholds and useful object-relative metrics |
| Effect-preserving substitution | CPU tested | Broader capability-semantic equivalence needs design/testing |
| Analytic pick/place/push/pull/arc compositions | Executable in toy and source-bound native adapters | Real grasp, object effects, contact/obstacle envelopes NOT qualified |
| Frozen π0.5 dispatch | Mocked contract tested | Download exact checkpoint; actual inference and action layout |
| RPent reset/step/chunk bridge | Actual source interfaces inspected; mocked tests | Native dependencies, reset/render/action tests, no GPU run yet |
| Image/depth/calibration conversion | Numerical CPU tests | Actual cameras, wrist extrinsics and physical frame validation |
| Optional native MP4 recording | Implemented streaming path | GPU/FFmpeg recording not exercised |
| Built-in metric backprojection | Numerical CPU tests | Real/noisy depth generality not established |
| K1 geometry bridges | Exact interfaces inspected; import mocks tested | Pinned upstream imports and real geometry calls |
| Full K1 system | Not implemented | SAM3, tracker, grasp hypotheses, history, independent full baseline |
| API planner | Mocked HTTP/function-call tests | Actual provider/local Qwen server compatibility |
| External Codex file bridge | CPU-tested request/hash/response/timeout | Real external agent model and recorded configuration |
| Trusted command bridge | Real subprocess CPU tests | Not a sandbox; caller must trust executable |
| Durable API reservations | CPU tested | Provider dollar accounting, multi-worker allocation/reconciliation |
| State catalogs/manifests | Hash/schema/split tests; native catalog interface inspected | Installed asset catalog and exact paper state manifest |
| Evaluation and HTML reports | Full synthetic end-to-end tests | Real native measurements |
| Offline attribution/regression gate | CPU tested | Exact paper taxonomy, automated edit generator, broader regression |
| Bootstrap and installer | Dry plans tested; source pins inspected | Actual network clone, dependency solve, native import/run |
| DynaHarness exact reproduction | Not established | Full PDF protocol, exact skills/checkpoint/state access/budgets |
| BEHAVIOR, old GPU assembly project | Untouched | No work planned here |

## What the current experiments do not establish

- No claim of 17.5% → 75.2%, or 63.9% → 74.0%, has been reproduced here.
- No trained robot policy improved; no model training occurred.
- No industrial deployment, real-robot reliability, contact-force safety,
  collision-free motion or successful connector/GPU insertion is established.
- The fixture's mocked policy is deliberately a no-op. Comparing it with the
  scripted fixture planner is a software test, not a capability result.
- The deterministic governor currently has a usable metric for EEF target
  movement, not arbitrary task progress. Native VLA stages remain bounded
  without pretending their progress can be read from gripper width.
- The registry is independent basic engineering, not the evolved DynaHarness
  library whose ablation accounts for much of the paper's headline gain.

## Known native qualification risks

1. RPent uses private-but-inspected entry points. The source pin is checked to
   prevent silent API drift; a newer upstream may need a small reviewed adapter.
2. Native dependencies use several libraries/branches. Our explicit source
   installer reduces moving-reference risk but is not a proven solved environment.
3. E0/E1/E2 source access and reset/control semantics must be qualified together.
4. Initial-state hashes identify source states. Actual post-reset settling and
   policy randomness still need native inspection.
5. Upstream policy sampling is not seeded by this adapter. Repeat identifiers are
   not claims of paired common-random-number policy noise.
6. The geometry profile contains no whole-arm collision planner. Motion limits
   and EEF progress do not establish external clearance or force measurement.
7. Camera conversion follows the reviewed RPent source. A metric-depth stream
   with another encoding must receive a new explicit adapter, not bypass checks.
8. A real provider may require adjusted decoding options. Record changes and keep
   the same configuration in matched conditions.
9. Stepwise RPC and video encoding add wall-clock latency. Do not equate apparent
   playback speed with robot cycle time or LLM latency.
10. The file/command bridge is trusted research integration. It does not prevent
    an external process with local filesystem access from reading evaluator files.
    Scientific discipline and process isolation are still required.

## Continuation priority

Run CPU tests → obtain full paper/source details → qualify RPent native smoke →
qualify baseline policy and one useful analytic skill → freeze dev work → matched
native E0/E1/E2 pilot → selective K1/perception extension → broader tests.

The report can be useful even when there is no improvement. A real tie, regression
or capability bottleneck is better evidence than a fabricated gain.
